# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from auto_mfa_tool.environment import (
    ENV_NAME,
    build_create_env_command,
    build_launch_command,
    check_environment,
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
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "environment.yml").write_text("name: auto-mfa\n", encoding="utf-8")

            status = check_environment(root=root, which=lambda _: "mamba", run=fake_runner(responses))

        self.assertTrue(status.env_exists)
        self.assertFalse(status.can_create)
        self.assertTrue(status.ready)

    def test_launch_command_uses_isolated_environment(self):
        self.assertEqual(
            build_launch_command(),
            ["mamba", "run", "-n", ENV_NAME, "python", "-m", "auto_mfa_tool", "--app"],
        )

    def test_create_command_uses_environment_file(self):
        root = Path("repo")
        self.assertEqual(build_create_env_command(root), ["mamba", "env", "create", "-f", str(root / "environment.yml")])


def fake_runner(responses):
    def run(command):
        return responses.get(tuple(command), subprocess.CompletedProcess(command, 1, stdout="missing"))

    return run


def completed(stdout):
    if isinstance(stdout, dict):
        stdout = json.dumps(stdout)
    return subprocess.CompletedProcess([sys.executable], 0, stdout=stdout)


if __name__ == "__main__":
    unittest.main()
