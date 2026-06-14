# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
from pathlib import Path


PRIVATE_DATA_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".textgrid"}
GENERATED_DIR_NAMES = {"whisper-output", "mfa-input", "mfa-output"}
SENSITIVE_TEXT_PATTERNS = (
    "c:/users/",
    "c:\\users\\",
    "/users/",
    "access_token",
    "gh_token",
    "secret",
    "password",
)


def find_release_safety_issues(bundle_root: Path, manifest_path: Path) -> list[str]:
    issues: list[str] = []
    bundle_root = Path(bundle_root)
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        return [f"missing manifest: {manifest_path}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"manifest is not valid JSON: {exc}"]

    manifest_text = manifest_path.read_text(encoding="utf-8").lower()
    for pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern in manifest_text:
            issues.append(f"manifest contains sensitive pattern: {pattern}")

    files = manifest.get("files", [])
    if not isinstance(files, list):
        issues.append("manifest files field is not a list")
        return issues

    for item in files:
        if not isinstance(item, dict):
            issues.append("manifest contains a non-object file entry")
            continue
        relative_path = str(item.get("path", ""))
        relative_lower = relative_path.lower()
        path = Path(relative_path)
        if Path(relative_path).is_absolute() or ":" in relative_path:
            issues.append(f"manifest path is not relative: {relative_path}")
        if path.suffix.lower() in PRIVATE_DATA_SUFFIXES:
            issues.append(f"private/generated media file included: {relative_path}")
        parts = {part.lower() for part in Path(relative_lower).parts}
        if parts & GENERATED_DIR_NAMES:
            issues.append(f"generated Auto-MFA output directory included: {relative_path}")
        resolved = (bundle_root / relative_path).resolve()
        try:
            resolved.relative_to(bundle_root.resolve())
        except ValueError:
            issues.append(f"manifest path escapes bundle root: {relative_path}")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Auto-MFA offline release manifest for unsafe entries.")
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--manifest", default="offline_manifest.json", type=Path)
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = args.bundle_root / manifest_path

    issues = find_release_safety_issues(args.bundle_root, manifest_path)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1
    print("offline release safety check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
