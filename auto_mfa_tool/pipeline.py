# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .offline import normalize_whisper_model, whisper_model_dir_args
from .runtime_checks import check_current_environment, environment_is_ready, format_environment_report


AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac"}
LogSink = Callable[[str], None]


class PipelineError(RuntimeError):
    """Raised when the Auto-MFA pipeline cannot continue."""


@dataclass(frozen=True)
class PipelineConfig:
    audio_dir: Path
    output_dir: Path
    language: str = "ja"
    whisper_model: str = "small"
    tier_name: str = "sentences"
    mfa_acoustic_model: str = "japanese_mfa"
    mfa_dictionary: str = "japanese_mfa"


@dataclass(frozen=True)
class PipelinePaths:
    whisper_output: Path
    mfa_input: Path
    mfa_output: Path


@dataclass(frozen=True)
class TextGridInterval:
    start: float
    end: float
    label: str


def default_log(message: str) -> None:
    print(message, flush=True)


def build_paths(output_dir: Path) -> PipelinePaths:
    return PipelinePaths(
        whisper_output=output_dir / "whisper-output",
        mfa_input=output_dir / "mfa-input",
        mfa_output=output_dir / "mfa-output",
    )


def check_environment() -> list[str]:
    return [name for name in ("whisper", "ffmpeg", "mfa") if shutil.which(name) is None]


def require_environment() -> None:
    checks = check_current_environment()
    if environment_is_ready(checks):
        return
    message = ["Environment check failed before running Whisper:", *format_environment_report(checks)]
    raise PipelineError("\n".join(message))


def discover_audio_files(audio_dir: Path) -> list[Path]:
    audio_dir = Path(audio_dir)
    if not audio_dir.exists():
        raise PipelineError(f"Audio directory does not exist: {audio_dir}")
    if not audio_dir.is_dir():
        raise PipelineError(f"Audio path is not a directory: {audio_dir}")

    audio_files = sorted(
        path for path in audio_dir.iterdir() if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    )
    if not audio_files:
        supported = ", ".join(sorted(AUDIO_SUFFIXES))
        raise PipelineError(f"No audio files found in {audio_dir}. Supported extensions: {supported}")

    stems: dict[str, Path] = {}
    for path in audio_files:
        if path.stem in stems:
            raise PipelineError(
                "Duplicate audio stem found: "
                f"{stems[path.stem].name} and {path.name}. Use unique base filenames."
            )
        stems[path.stem] = path

    return audio_files


def run_command(command: Sequence[str], log: LogSink = default_log) -> None:
    log("")
    log("$ " + " ".join(str(part) for part in command))
    process = subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert process.stdout is not None
    for line in process.stdout:
        log(line.rstrip())

    return_code = process.wait()
    if return_code != 0:
        raise PipelineError(f"Command failed with exit code {return_code}: {command[0]}")


def build_whisper_command(audio_files: Sequence[Path], output_dir: Path, config: PipelineConfig) -> list[str]:
    whisper_model = normalize_whisper_model(config.whisper_model)
    return [
        "whisper",
        *(str(path) for path in audio_files),
        "--model",
        whisper_model,
        *whisper_model_dir_args(),
        "--language",
        config.language,
        "--output_dir",
        str(output_dir),
        "--output_format",
        "all",
    ]


def run_whisper(audio_files: Sequence[Path], output_dir: Path, config: PipelineConfig, log: LogSink) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_command(build_whisper_command(audio_files, output_dir, config), log)


def parse_whisper_json(json_path: Path) -> list[TextGridInterval]:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Invalid Whisper JSON: {json_path}") from exc

    segments = data.get("segments")
    if not isinstance(segments, list):
        raise PipelineError(f"Whisper JSON has no segments list: {json_path}")

    intervals: list[TextGridInterval] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue
        label = str(segment.get("text", "")).strip()
        if end > start and label:
            intervals.append(TextGridInterval(start=start, end=end, label=label))

    if not intervals:
        raise PipelineError(f"No valid Whisper segments found in {json_path}")

    return intervals


def write_textgrid(intervals: Sequence[TextGridInterval], output_path: Path, tier_name: str = "sentences") -> Path:
    if output_path.suffix != ".TextGrid":
        output_path = output_path.with_suffix(".TextGrid")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    xmax = max(interval.end for interval in intervals)
    intervals_with_blanks = list(_include_blank_intervals(intervals, xmax))

    lines = [
        'File type = "ooTextFile"',
        'Object class = "TextGrid"',
        "",
        "xmin = 0",
        f"xmax = {_format_time(xmax)}",
        "tiers? <exists>",
        "size = 1",
        "item []:",
        "    item [1]:",
        '        class = "IntervalTier"',
        f'        name = "{_escape_textgrid_text(tier_name)}"',
        "        xmin = 0",
        f"        xmax = {_format_time(xmax)}",
        f"        intervals: size = {len(intervals_with_blanks)}",
    ]

    for index, interval in enumerate(intervals_with_blanks, start=1):
        lines.extend(
            [
                f"        intervals [{index}]:",
                f"            xmin = {_format_time(interval.start)}",
                f"            xmax = {_format_time(interval.end)}",
                f'            text = "{_escape_textgrid_text(interval.label)}"',
            ]
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def whisper_json_to_textgrid(json_path: Path, output_path: Path, tier_name: str = "sentences") -> Path:
    return write_textgrid(parse_whisper_json(json_path), output_path, tier_name=tier_name)


def batch_convert_whisper_jsons(
    audio_files: Sequence[Path],
    whisper_output_dir: Path,
    mfa_input_dir: Path,
    tier_name: str,
    log: LogSink = default_log,
) -> list[Path]:
    mfa_input_dir.mkdir(parents=True, exist_ok=True)
    textgrids: list[Path] = []

    for audio_path in audio_files:
        json_path = whisper_output_dir / f"{audio_path.stem}.json"
        if not json_path.exists():
            raise PipelineError(f"Expected Whisper JSON was not found: {json_path}")
        textgrid_path = whisper_json_to_textgrid(json_path, mfa_input_dir / audio_path.stem, tier_name=tier_name)
        log(f"TextGrid saved: {textgrid_path}")
        textgrids.append(textgrid_path)

    return textgrids


def prepare_mfa_input(audio_files: Sequence[Path], textgrids: Sequence[Path], mfa_input_dir: Path, log: LogSink) -> None:
    expected_textgrids = {path.stem for path in textgrids}
    for audio_path in audio_files:
        if audio_path.stem not in expected_textgrids:
            raise PipelineError(f"Missing TextGrid for audio file: {audio_path.name}")
        destination = mfa_input_dir / audio_path.name
        shutil.copy2(audio_path, destination)
        log(f"Audio copied: {destination}")


def run_mfa(paths: PipelinePaths, config: PipelineConfig, log: LogSink) -> None:
    paths.mfa_output.mkdir(parents=True, exist_ok=True)
    command = [
        "mfa",
        "align",
        str(paths.mfa_input),
        config.mfa_dictionary,
        config.mfa_acoustic_model,
        str(paths.mfa_output),
        "--clean",
    ]
    try:
        run_command(command, log)
    except PipelineError as exc:
        log("")
        log("If MFA reports missing Japanese tokenizer support, update the environment first:")
        log("mamba env update -n auto-mfa -f environment.yml --prune")
        log("")
        log("If MFA cannot find a model, install it first, for example:")
        log(f"mfa model download acoustic {config.mfa_acoustic_model}")
        log(f"mfa model download dictionary {config.mfa_dictionary}")
        raise exc


def run_pipeline(config: PipelineConfig, log: LogSink = default_log) -> PipelinePaths:
    config = PipelineConfig(
        audio_dir=Path(config.audio_dir),
        output_dir=Path(config.output_dir),
        language=config.language.strip() or "ja",
        whisper_model=normalize_whisper_model(config.whisper_model.strip() or "small"),
        tier_name=config.tier_name.strip() or "sentences",
        mfa_acoustic_model=config.mfa_acoustic_model.strip() or "japanese_mfa",
        mfa_dictionary=config.mfa_dictionary.strip() or "japanese_mfa",
    )

    log("Checking external tools...")
    require_environment()

    paths = build_paths(config.output_dir)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    paths.whisper_output.mkdir(parents=True, exist_ok=True)
    paths.mfa_input.mkdir(parents=True, exist_ok=True)
    paths.mfa_output.mkdir(parents=True, exist_ok=True)

    audio_files = discover_audio_files(config.audio_dir)
    log(f"Found {len(audio_files)} audio file(s).")

    log("Running Whisper transcription...")
    run_whisper(audio_files, paths.whisper_output, config, log)

    log("Converting Whisper JSON to TextGrid...")
    textgrids = batch_convert_whisper_jsons(audio_files, paths.whisper_output, paths.mfa_input, config.tier_name, log)

    log("Preparing MFA input...")
    prepare_mfa_input(audio_files, textgrids, paths.mfa_input, log)

    log("Running MFA alignment...")
    run_mfa(paths, config, log)

    log("")
    log(f"Done. MFA output: {paths.mfa_output}")
    return paths


def _include_blank_intervals(
    intervals: Sequence[TextGridInterval],
    xmax: float,
) -> Iterable[TextGridInterval]:
    current = 0.0
    for interval in sorted(intervals, key=lambda item: (item.start, item.end)):
        start = max(interval.start, current)
        if start > current:
            yield TextGridInterval(current, start, "")
        end = max(interval.end, start)
        yield TextGridInterval(start, end, interval.label)
        current = end
    if xmax > current:
        yield TextGridInterval(current, xmax, "")


def _format_time(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def _escape_textgrid_text(value: str) -> str:
    return value.replace('"', '""')
