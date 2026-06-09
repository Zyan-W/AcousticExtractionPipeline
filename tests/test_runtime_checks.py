# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import unittest

from auto_mfa_tool.runtime_checks import (
    PYTHON_RUNTIME_CHECK_CODE,
    check_current_environment,
    environment_is_ready,
    format_environment_report,
)


class RuntimeChecksTest(unittest.TestCase):
    def test_ready_when_commands_and_numpy_torch_work(self):
        checks = check_current_environment(
            which=lambda name: f"/env/bin/{name}",
            run=fake_runner({(sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2")}),
        )

        self.assertTrue(environment_is_ready(checks))
        self.assertIn("[OK] numpy/torch", "\n".join(format_environment_report(checks)))

    def test_missing_command_is_reported_with_fix_hint(self):
        checks = check_current_environment(
            which=lambda name: None if name == "whisper" else f"/env/bin/{name}",
            run=fake_runner({(sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2")}),
        )
        report = "\n".join(format_environment_report(checks))

        self.assertFalse(environment_is_ready(checks))
        self.assertIn("[ERROR] whisper: not found on PATH", report)
        self.assertIn("environment.yml", report)

    def test_numpy_torch_failure_is_reported(self):
        checks = check_current_environment(
            which=lambda name: f"/env/bin/{name}",
            run=fake_runner(
                {
                    (sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): subprocess.CompletedProcess(
                        [sys.executable], 1, stdout="RuntimeError: Numpy is not available"
                    )
                }
            ),
        )
        report = "\n".join(format_environment_report(checks))

        self.assertFalse(environment_is_ready(checks))
        self.assertIn("[ERROR] numpy/torch: RuntimeError: Numpy is not available", report)
        self.assertIn("mamba env update", report)


def fake_runner(responses):
    def run(command):
        return responses.get(tuple(command), subprocess.CompletedProcess(command, 1, stdout="missing"))

    return run


def completed(stdout):
    return subprocess.CompletedProcess([sys.executable], 0, stdout=stdout)


if __name__ == "__main__":
    unittest.main()
