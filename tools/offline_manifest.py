# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


DEFAULT_EXCLUDED_FILES = frozenset({"offline_manifest.json", "SHA256SUMS.txt"})


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_bundle_files(bundle_root: Path, excluded_files: Iterable[str] = DEFAULT_EXCLUDED_FILES) -> list[dict[str, object]]:
    bundle_root = Path(bundle_root)
    excluded = set(excluded_files)
    files: list[dict[str, object]] = []
    for path in sorted(bundle_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(bundle_root).as_posix()
        if relative_path in excluded or path.name in excluded:
            continue
        files.append(
            {
                "path": relative_path,
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return files


def build_manifest(
    bundle_root: Path,
    platform: str,
    bundle_name: str,
    whisper_models: Iterable[str],
    mfa_models: Iterable[str],
) -> dict[str, object]:
    files = iter_bundle_files(bundle_root)
    return {
        "schema_version": 1,
        "bundle_name": bundle_name,
        "platform": platform,
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "contents": {
            "whisper_models": sorted(set(whisper_models)),
            "mfa_models": sorted(set(mfa_models)),
            "packed_environment": "payload/auto-mfa-env-windows-x86_64.zip",
        },
        "files": files,
    }


def write_manifest(manifest: dict[str, object], output_path: Path) -> None:
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(files: Iterable[dict[str, object]], output_path: Path) -> None:
    lines = [f"{item['sha256']}  {item['path']}" for item in files]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write Auto-MFA offline release manifest and checksums.")
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--bundle-name", required=True)
    parser.add_argument("--whisper-models", default="small")
    parser.add_argument("--mfa-models", default="")
    parser.add_argument("--manifest", default="offline_manifest.json")
    parser.add_argument("--checksums", default="SHA256SUMS.txt")
    args = parser.parse_args(argv)

    manifest = build_manifest(
        bundle_root=args.bundle_root,
        platform=args.platform,
        bundle_name=args.bundle_name,
        whisper_models=parse_csv(args.whisper_models),
        mfa_models=parse_csv(args.mfa_models),
    )
    write_manifest(manifest, args.bundle_root / args.manifest)
    write_checksums(manifest["files"], args.bundle_root / args.checksums)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
