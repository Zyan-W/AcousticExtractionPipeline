# SPDX-License-Identifier: Apache-2.0

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auto_mfa_tool.offline import (
    BUNDLED_WHISPER_MODELS_ENV_VAR,
    OFFLINE_ENV_VAR,
    WHISPER_MODEL_DIR_ENV_VAR,
    bundled_whisper_models,
    normalize_whisper_model,
    offline_mode_enabled,
    whisper_model_choices,
    whisper_model_dir_args,
)
from auto_mfa_tool.pipeline import PipelineConfig, build_whisper_command
from tools.offline_manifest import build_manifest, write_checksums, write_manifest
from tools.offline_release_safety import find_release_safety_issues


class OfflineRuntimeTest(unittest.TestCase):
    def test_offline_mode_flag_accepts_common_true_values(self):
        self.assertTrue(offline_mode_enabled({OFFLINE_ENV_VAR: "1"}))
        self.assertTrue(offline_mode_enabled({OFFLINE_ENV_VAR: "true"}))
        self.assertFalse(offline_mode_enabled({OFFLINE_ENV_VAR: "0"}))
        self.assertFalse(offline_mode_enabled({}))

    def test_offline_model_choices_default_to_small(self):
        env = {OFFLINE_ENV_VAR: "1"}

        self.assertEqual(bundled_whisper_models(env), ("small",))
        self.assertEqual(whisper_model_choices(env), ("small",))
        self.assertEqual(normalize_whisper_model("large", env), "small")

    def test_custom_bundled_model_list_is_supported(self):
        env = {
            OFFLINE_ENV_VAR: "1",
            BUNDLED_WHISPER_MODELS_ENV_VAR: "small,medium",
        }

        self.assertEqual(whisper_model_choices(env), ("small", "medium"))
        self.assertEqual(normalize_whisper_model("medium", env), "medium")

    def test_whisper_model_dir_args_follow_environment(self):
        env = {WHISPER_MODEL_DIR_ENV_VAR: r"C:\Auto-MFA\models\whisper"}

        self.assertEqual(whisper_model_dir_args(env), ["--model_dir", r"C:\Auto-MFA\models\whisper"])

    def test_pipeline_adds_offline_model_dir_and_restricts_model(self):
        env = {
            OFFLINE_ENV_VAR: "1",
            WHISPER_MODEL_DIR_ENV_VAR: r"C:\Auto-MFA\models\whisper",
        }
        config = PipelineConfig(audio_dir=Path("audio"), output_dir=Path("out"), whisper_model="large")

        with patch.dict(os.environ, env, clear=True):
            command = build_whisper_command([Path("sample.wav")], Path("out"), config)

        self.assertIn("--model_dir", command)
        self.assertIn(r"C:\Auto-MFA\models\whisper", command)
        self.assertEqual(command[command.index("--model") + 1], "small")


class OfflineManifestTest(unittest.TestCase):
    def test_manifest_uses_relative_paths_and_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README_OFFLINE_WINDOWS.md").write_text("hello\n", encoding="utf-8")
            (root / "offline_manifest.json").write_text("old\n", encoding="utf-8")
            (root / "SHA256SUMS.txt").write_text("old\n", encoding="utf-8")

            manifest = build_manifest(
                bundle_root=root,
                platform="windows-x86_64",
                bundle_name="Auto-MFA-windows-x86_64-offline",
                whisper_models=("small",),
                mfa_models=("acoustic:japanese_mfa",),
            )
            write_manifest(manifest, root / "offline_manifest.json")
            write_checksums(manifest["files"], root / "SHA256SUMS.txt")

            paths = [item["path"] for item in manifest["files"]]
            self.assertEqual(paths, ["README_OFFLINE_WINDOWS.md"])
            self.assertNotIn(str(root), (root / "offline_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("README_OFFLINE_WINDOWS.md", (root / "SHA256SUMS.txt").read_text(encoding="utf-8"))

    def test_release_safety_check_rejects_private_generated_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "offline_manifest.json"
            manifest_path.write_text(
                '{"files": [{"path": "mfa-output/private.TextGrid"}, {"path": "audio.wav"}]}',
                encoding="utf-8",
            )

            issues = find_release_safety_issues(root, manifest_path)

            self.assertTrue(any("generated Auto-MFA output directory" in issue for issue in issues))
            self.assertTrue(any("private/generated media file" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
