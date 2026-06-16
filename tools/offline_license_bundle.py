# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Iterable


SUMMARY_FILENAME = "THIRD_PARTY_LICENSES.md"
MANIFEST_FILENAME = "third_party_licenses_manifest.json"
MAX_COPIED_FILE_BYTES = 5 * 1024 * 1024
LICENSE_NAME_PREFIXES = ("license", "copying", "notice", "copyright", "authors")


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
    return cleaned.strip("._-") or "unknown"


def ensure_child_path(root: Path, path: Path) -> None:
    root_resolved = root.resolve()
    path_resolved = path.resolve()
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes output root: {path}") from exc


def is_notice_like(path: Path) -> bool:
    name = path.name.lower()
    return any(name.startswith(prefix) for prefix in LICENSE_NAME_PREFIXES)


def copy_file(source: Path, destination: Path, root: Path) -> str | None:
    if not source.is_file():
        return None
    if source.stat().st_size > MAX_COPIED_FILE_BYTES:
        return None
    ensure_child_path(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination.relative_to(root).as_posix()


def strip_package_filename(filename: str) -> str:
    if filename.endswith(".tar.bz2"):
        return filename[:-8]
    if filename.endswith(".conda"):
        return filename[:-6]
    return Path(filename).stem


def conda_cache_dirs() -> list[Path]:
    candidates: list[Path] = []
    raw_env = os.environ.get("CONDA_PKGS_DIRS", "")
    for item in raw_env.split(os.pathsep):
        if item:
            candidates.append(Path(item))

    conda_exe = shutil.which("conda")
    if conda_exe:
        try:
            result = subprocess.run(
                [conda_exe, "info", "--json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                candidates.extend(Path(item) for item in data.get("pkgs_dirs", []) if item)
        except (OSError, json.JSONDecodeError):
            pass

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key not in seen:
            unique.append(candidate)
            seen.add(key)
    return unique


def read_conda_records(env_prefix: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    conda_meta = env_prefix / "conda-meta"
    if not conda_meta.exists():
        return records

    for path in sorted(conda_meta.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("name"):
            records.append(data)
    return records


def conda_package_dir_names(record: dict[str, object]) -> list[str]:
    names: list[str] = []
    for key in ("dist_name", "fn"):
        value = str(record.get(key, "") or "")
        if not value:
            continue
        names.append(strip_package_filename(value) if key == "fn" else value)

    name = str(record.get("name", "") or "")
    version = str(record.get("version", "") or "")
    build = str(record.get("build", "") or record.get("build_string", "") or "")
    if name and version and build:
        names.append(f"{name}-{version}-{build}")

    unique: list[str] = []
    for item in names:
        if item and item not in unique:
            unique.append(item)
    return unique


def find_conda_package_dir(record: dict[str, object], package_cache_dirs: Iterable[Path]) -> Path | None:
    for root in package_cache_dirs:
        for dirname in conda_package_dir_names(record):
            candidate = root / dirname
            if candidate.exists():
                return candidate
    return None


def copy_conda_license_files(
    record: dict[str, object],
    package_dir: Path | None,
    destination: Path,
    output_root: Path,
) -> list[str]:
    copied: list[str] = []
    destination.mkdir(parents=True, exist_ok=True)

    metadata = {
        "name": record.get("name", ""),
        "version": record.get("version", ""),
        "build": record.get("build", record.get("build_string", "")),
        "license": record.get("license", ""),
        "license_family": record.get("license_family", ""),
        "channel": record.get("channel", ""),
        "url": record.get("url", ""),
    }
    metadata_path = destination / "conda-package-record.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copied.append(metadata_path.relative_to(output_root).as_posix())

    if not package_dir:
        return copied

    info_dir = package_dir / "info"
    licenses_dir = info_dir / "licenses"
    if licenses_dir.exists():
        for source in sorted(path for path in licenses_dir.rglob("*") if path.is_file()):
            relative = source.relative_to(licenses_dir)
            copied_path = copy_file(source, destination / "licenses" / relative, output_root)
            if copied_path:
                copied.append(copied_path)

    for source in sorted(info_dir.glob("*")):
        if source.is_file() and (is_notice_like(source) or source.name in {"about.json", "index.json"}):
            copied_path = copy_file(source, destination / "info" / source.name, output_root)
            if copied_path:
                copied.append(copied_path)

    recipe_dir = info_dir / "recipe"
    if recipe_dir.exists():
        for source in sorted(path for path in recipe_dir.rglob("*") if path.is_file() and is_notice_like(path)):
            relative = source.relative_to(recipe_dir)
            copied_path = copy_file(source, destination / "recipe" / relative, output_root)
            if copied_path:
                copied.append(copied_path)

    return copied


def collect_conda_licenses(env_prefix: Path, output_root: Path, package_cache_dirs: Iterable[Path] | None = None) -> list[dict[str, object]]:
    records = read_conda_records(env_prefix)
    cache_dirs = list(package_cache_dirs) if package_cache_dirs is not None else conda_cache_dirs()
    output_dir = output_root / "conda"
    packages: list[dict[str, object]] = []

    for record in records:
        name = str(record.get("name", "") or "")
        version = str(record.get("version", "") or "")
        build = str(record.get("build", record.get("build_string", "")) or "")
        package_id = safe_name("-".join(item for item in (name, version, build) if item))
        package_dir = find_conda_package_dir(record, cache_dirs)
        copied = copy_conda_license_files(record, package_dir, output_dir / package_id, output_root)
        packages.append(
            {
                "manager": "conda",
                "name": name,
                "version": version,
                "build": build,
                "license": record.get("license", ""),
                "license_family": record.get("license_family", ""),
                "channel": record.get("channel", ""),
                "url": record.get("url", ""),
                "license_files": copied,
            }
        )

    return packages


def pip_license_files(dist: metadata.Distribution) -> list[Path]:
    files = dist.files or []
    selected: list[Path] = []
    for file in files:
        path = Path(str(file))
        parts = [part.lower() for part in path.parts]
        if is_notice_like(path) or "licenses" in parts:
            selected.append(file)
    return selected


def collect_pip_licenses(output_root: Path, distributions: Iterable[metadata.Distribution] | None = None) -> list[dict[str, object]]:
    packages: list[dict[str, object]] = []
    output_dir = output_root / "pip"
    dists = list(distributions) if distributions is not None else list(metadata.distributions())

    for dist in sorted(dists, key=lambda item: (item.metadata.get("Name", "") or "").lower()):
        name = dist.metadata.get("Name", "") or "unknown"
        version = dist.version or ""
        package_id = safe_name(f"{name}-{version}")
        destination = output_dir / package_id
        destination.mkdir(parents=True, exist_ok=True)

        copied: list[str] = []
        metadata_text = dist.read_text("METADATA")
        if metadata_text:
            metadata_path = destination / "METADATA"
            metadata_path.write_text(metadata_text, encoding="utf-8")
            copied.append(metadata_path.relative_to(output_root).as_posix())

        for file in pip_license_files(dist):
            source = Path(dist.locate_file(file))
            copied_path = copy_file(source, destination / "licenses" / Path(str(file)).name, output_root)
            if copied_path and copied_path not in copied:
                copied.append(copied_path)

        packages.append(
            {
                "manager": "pip",
                "name": name,
                "version": version,
                "license": dist.metadata.get("License", "") or "",
                "summary": dist.metadata.get("Summary", "") or "",
                "home_page": dist.metadata.get("Home-page", "") or dist.metadata.get("Project-URL", "") or "",
                "license_files": copied,
            }
        )

    return packages


def write_summary(packages: list[dict[str, object]], output_path: Path) -> None:
    conda_packages = [item for item in packages if item.get("manager") == "conda"]
    pip_packages = [item for item in packages if item.get("manager") == "pip"]

    lines = [
        "# Third-Party License Bundle",
        "",
        "This folder is generated during the Windows offline release build.",
        "It collects available license, notice, and package metadata files from the packed conda environment.",
        "Package records use relative paths so the bundle can be copied between machines without leaking local build paths.",
        "",
        "Model assets are summarized in `../OFFLINE_RELEASE_NOTICES.md`.",
        "",
        "## Conda Packages",
        "",
        "| Package | Version | Build | License | License files |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for item in conda_packages:
        lines.append(
            f"| {item.get('name', '')} | {item.get('version', '')} | {item.get('build', '')} | "
            f"{item.get('license', '') or item.get('license_family', '')} | {len(item.get('license_files', []))} |"
        )

    lines.extend(
        [
            "",
            "## Pip Package Metadata",
            "",
            "| Package | Version | License | Metadata/license files |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for item in pip_packages:
        lines.append(
            f"| {item.get('name', '')} | {item.get('version', '')} | {item.get('license', '')} | "
            f"{len(item.get('license_files', []))} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Preserve this directory when redistributing the offline bundle.",
            "- Review `third_party_licenses_manifest.json` before publishing a new release.",
            "- FFmpeg must remain an LGPL build; the release script rejects GPL-enabled FFmpeg builds.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def build_license_bundle(bundle_root: Path, env_prefix: Path, package_cache_dirs: Iterable[Path] | None = None) -> dict[str, object]:
    bundle_root = Path(bundle_root)
    env_prefix = Path(env_prefix)
    licenses_root = bundle_root / "licenses"
    ensure_child_path(bundle_root, licenses_root)
    if licenses_root.exists():
        shutil.rmtree(licenses_root)
    licenses_root.mkdir(parents=True, exist_ok=True)

    packages = []
    packages.extend(collect_conda_licenses(env_prefix, licenses_root, package_cache_dirs))
    packages.extend(collect_pip_licenses(licenses_root))

    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "package_count": len(packages),
        "packages": packages,
    }

    (licenses_root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_summary(packages, licenses_root / SUMMARY_FILENAME)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect third-party license files for the Auto-MFA offline bundle.")
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--env-prefix", type=Path, default=Path(sys.prefix))
    args = parser.parse_args(argv)

    manifest = build_license_bundle(args.bundle_root, args.env_prefix)
    print(f"third-party license bundle ready: {manifest['package_count']} package records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
