# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from auto_mfa_tool.environment import (
    CHINESE_TOKENIZER_CHECK_CODE,
    ENV_NAME,
    JAPANESE_TOKENIZER_CHECK_CODE,
    KOREAN_TOKENIZER_CHECK_CODE,
    PYTHON_RUNTIME_CHECK_CODE,
    build_create_env_command,
    build_launch_command,
    build_model_download_commands,
    check_environment,
    model_download_specs,
)


class EnvironmentCheckTest(unittest.TestCase):
    def test_mamba_missing_disables_create_and_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: None, run=fake_runner({}))

        self.assertFalse(status.mamba_path)
        self.assertFalse(status.can_create)
        self.assertFalse(status.ready)
        self.assertIn("mamba: not found", "\n".join(status.messages))

    def test_mamba_present_without_environment_allows_create(self):
        responses = {
            ("mamba", "env", "list", "--json"): completed({"envs": []}),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.mamba_path)
        self.assertFalse(status.env_exists)
        self.assertTrue(status.can_create)
        self.assertFalse(status.ready)

    def test_ready_when_environment_and_tools_exist(self):
        env_path = f"/example/envs/{ENV_NAME}"
        responses = {
            ("mamba", "env", "list", "--json"): completed({"envs": [env_path]}),
            ("mamba", "run", "-n", ENV_NAME, "whisper", "--help"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "ffmpeg", "-version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "mfa", "version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.0"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                "spacy/sudachipy/sudachidict-core available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", KOREAN_TOKENIZER_CHECK_CODE): completed(
                "python-mecab-ko/jamo available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                "spacy-pkuseg/dragonmapper/hanziconv available"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.env_exists)
        self.assertFalse(status.can_create)
        self.assertTrue(status.ready)

    def test_runtime_failure_blocks_ready_status(self):
        env_path = f"/example/envs/{ENV_NAME}"
        responses = {
            ("mamba", "env", "list", "--json"): completed({"envs": [env_path]}),
            ("mamba", "run", "-n", ENV_NAME, "whisper", "--help"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "ffmpeg", "-version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "mfa", "version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", PYTHON_RUNTIME_CHECK_CODE): failed("RuntimeError: Numpy is not available"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                "spacy/sudachipy/sudachidict-core available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", KOREAN_TOKENIZER_CHECK_CODE): completed(
                "python-mecab-ko/jamo available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                "spacy-pkuseg/dragonmapper/hanziconv available"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.env_exists)
        self.assertFalse(status.ready)
        self.assertIn("numpy/torch: missing", "\n".join(status.messages))

    def test_japanese_tokenizer_failure_blocks_ready_status(self):
        env_path = f"/example/envs/{ENV_NAME}"
        responses = {
            ("mamba", "env", "list", "--json"): completed({"envs": [env_path]}),
            ("mamba", "run", "-n", ENV_NAME, "whisper", "--help"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "ffmpeg", "-version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "mfa", "version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.0"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", JAPANESE_TOKENIZER_CHECK_CODE): failed(
                "ModuleNotFoundError: No module named 'sudachipy'"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", KOREAN_TOKENIZER_CHECK_CODE): completed(
                "python-mecab-ko/jamo available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                "spacy-pkuseg/dragonmapper/hanziconv available"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.env_exists)
        self.assertFalse(status.ready)
        self.assertIn("japanese-tokenizer: missing", "\n".join(status.messages))

    def test_korean_tokenizer_failure_blocks_ready_status(self):
        env_path = f"/example/envs/{ENV_NAME}"
        responses = {
            ("mamba", "env", "list", "--json"): completed({"envs": [env_path]}),
            ("mamba", "run", "-n", ENV_NAME, "whisper", "--help"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "ffmpeg", "-version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "mfa", "version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.0"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                "spacy/sudachipy/sudachidict-core available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", KOREAN_TOKENIZER_CHECK_CODE): failed(
                "ModuleNotFoundError: No module named 'mecab'"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                "spacy-pkuseg/dragonmapper/hanziconv available"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.env_exists)
        self.assertFalse(status.ready)
        self.assertIn("korean-tokenizer: missing", "\n".join(status.messages))

    def test_chinese_tokenizer_failure_blocks_ready_status(self):
        env_path = f"/example/envs/{ENV_NAME}"
        responses = {
            ("mamba", "env", "list", "--json"): completed({"envs": [env_path]}),
            ("mamba", "run", "-n", ENV_NAME, "whisper", "--help"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "ffmpeg", "-version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "mfa", "version"): completed("ok"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.0"),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                "spacy/sudachipy/sudachidict-core available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", KOREAN_TOKENIZER_CHECK_CODE): completed(
                "python-mecab-ko/jamo available"
            ),
            ("mamba", "run", "-n", ENV_NAME, "python", "-c", CHINESE_TOKENIZER_CHECK_CODE): failed(
                "ModuleNotFoundError: No module named 'spacy_pkuseg'"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.env_exists)
        self.assertFalse(status.ready)
        self.assertIn("chinese-tokenizer: missing", "\n".join(status.messages))

    def test_launch_command_uses_isolated_environment(self):
        self.assertEqual(
            build_launch_command(),
            ["mamba", "run", "-n", ENV_NAME, "python", "-m", "auto_mfa_tool", "--app"],
        )

    def test_create_command_uses_environment_file(self):
        root = Path("repo")
        self.assertEqual(build_create_env_command(root), ["mamba", "env", "create", "-f", str(root / "environment.yml")])

    def test_model_download_commands_include_official_presets(self):
        self.assertEqual(
            model_download_specs(),
            (
                ("acoustic", "japanese_mfa"),
                ("dictionary", "japanese_mfa"),
                ("acoustic", "korean_mfa"),
                ("dictionary", "korean_mfa"),
                ("acoustic", "english_mfa"),
                ("dictionary", "english_mfa"),
                ("acoustic", "mandarin_mfa"),
                ("dictionary", "mandarin_china_mfa"),
            ),
        )
        self.assertEqual(
            build_model_download_commands()[0],
            ["mamba", "run", "-n", ENV_NAME, "mfa", "model", "download", "acoustic", "japanese_mfa"],
        )


def fake_runner(responses):
    def run(command):
        return responses.get(tuple(command), subprocess.CompletedProcess(command, 1, stdout="missing"))

    return run


def completed(stdout):
    if isinstance(stdout, dict):
        stdout = json.dumps(stdout)
    return subprocess.CompletedProcess([sys.executable], 0, stdout=stdout)


def failed(stdout):
    return subprocess.CompletedProcess([sys.executable], 1, stdout=stdout)


if __name__ == "__main__":
    unittest.main()
