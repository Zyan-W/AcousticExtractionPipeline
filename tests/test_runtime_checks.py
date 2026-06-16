# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import unittest

from auto_mfa_tool.runtime_checks import (
    CHINESE_TOKENIZER_CHECK_CODE,
    JAPANESE_TOKENIZER_CHECK_CODE,
    KOREAN_TOKENIZER_CHECK_CODE,
    PYTHON_RUNTIME_CHECK_CODE,
    check_current_environment,
    environment_is_ready,
    format_environment_report,
)


class RuntimeChecksTest(unittest.TestCase):
    def test_ready_when_commands_and_numpy_torch_work(self):
        checks = check_current_environment(
            which=lambda name: f"/env/bin/{name}",
            run=fake_runner(
                {
                    (sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2"),
                    (sys.executable, "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy/sudachipy/sudachidict-core available"
                    ),
                    (sys.executable, "-c", KOREAN_TOKENIZER_CHECK_CODE): completed("python-mecab-ko/jamo available"),
                    (sys.executable, "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy-pkuseg/dragonmapper/hanziconv available"
                    ),
                }
            ),
        )

        self.assertTrue(environment_is_ready(checks))
        self.assertIn("[OK] numpy/torch", "\n".join(format_environment_report(checks)))
        self.assertIn("[OK] japanese-tokenizer", "\n".join(format_environment_report(checks)))
        self.assertIn("[OK] korean-tokenizer", "\n".join(format_environment_report(checks)))
        self.assertIn("[OK] chinese-tokenizer", "\n".join(format_environment_report(checks)))

    def test_missing_command_is_reported_with_fix_hint(self):
        checks = check_current_environment(
            which=lambda name: None if name == "whisper" else f"/env/bin/{name}",
            run=fake_runner(
                {
                    (sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2"),
                    (sys.executable, "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy/sudachipy/sudachidict-core available"
                    ),
                    (sys.executable, "-c", KOREAN_TOKENIZER_CHECK_CODE): completed("python-mecab-ko/jamo available"),
                    (sys.executable, "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy-pkuseg/dragonmapper/hanziconv available"
                    ),
                }
            ),
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
                    ),
                    (sys.executable, "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy/sudachipy/sudachidict-core available"
                    ),
                    (sys.executable, "-c", KOREAN_TOKENIZER_CHECK_CODE): completed("python-mecab-ko/jamo available"),
                    (sys.executable, "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy-pkuseg/dragonmapper/hanziconv available"
                    ),
                }
            ),
        )
        report = "\n".join(format_environment_report(checks))

        self.assertFalse(environment_is_ready(checks))
        self.assertIn("[ERROR] numpy/torch: RuntimeError: Numpy is not available", report)
        self.assertIn("mamba env update", report)

    def test_japanese_tokenizer_failure_is_reported(self):
        checks = check_current_environment(
            which=lambda name: f"/env/bin/{name}",
            run=fake_runner(
                {
                    (sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2"),
                    (sys.executable, "-c", JAPANESE_TOKENIZER_CHECK_CODE): subprocess.CompletedProcess(
                        [sys.executable], 1, stdout="ModuleNotFoundError: No module named 'sudachipy'"
                    ),
                    (sys.executable, "-c", KOREAN_TOKENIZER_CHECK_CODE): completed("python-mecab-ko/jamo available"),
                    (sys.executable, "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy-pkuseg/dragonmapper/hanziconv available"
                    ),
                }
            ),
        )
        report = "\n".join(format_environment_report(checks))

        self.assertFalse(environment_is_ready(checks))
        self.assertIn("[ERROR] japanese-tokenizer: ModuleNotFoundError", report)
        self.assertIn("spacy sudachipy sudachidict-core", report)

    def test_korean_tokenizer_failure_is_reported(self):
        checks = check_current_environment(
            which=lambda name: f"/env/bin/{name}",
            run=fake_runner(
                {
                    (sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2"),
                    (sys.executable, "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy/sudachipy/sudachidict-core available"
                    ),
                    (sys.executable, "-c", KOREAN_TOKENIZER_CHECK_CODE): subprocess.CompletedProcess(
                        [sys.executable], 1, stdout="ModuleNotFoundError: No module named 'mecab'"
                    ),
                    (sys.executable, "-c", CHINESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy-pkuseg/dragonmapper/hanziconv available"
                    ),
                }
            ),
        )
        report = "\n".join(format_environment_report(checks))

        self.assertFalse(environment_is_ready(checks))
        self.assertIn("[ERROR] korean-tokenizer: ModuleNotFoundError", report)
        self.assertIn("python-mecab-ko jamo", report)

    def test_chinese_tokenizer_failure_is_reported(self):
        checks = check_current_environment(
            which=lambda name: f"/env/bin/{name}",
            run=fake_runner(
                {
                    (sys.executable, "-c", PYTHON_RUNTIME_CHECK_CODE): completed("numpy=1.26; torch=2.2"),
                    (sys.executable, "-c", JAPANESE_TOKENIZER_CHECK_CODE): completed(
                        "spacy/sudachipy/sudachidict-core available"
                    ),
                    (sys.executable, "-c", KOREAN_TOKENIZER_CHECK_CODE): completed("python-mecab-ko/jamo available"),
                    (sys.executable, "-c", CHINESE_TOKENIZER_CHECK_CODE): subprocess.CompletedProcess(
                        [sys.executable], 1, stdout="ModuleNotFoundError: No module named 'spacy_pkuseg'"
                    ),
                }
            ),
        )
        report = "\n".join(format_environment_report(checks))

        self.assertFalse(environment_is_ready(checks))
        self.assertIn("[ERROR] chinese-tokenizer: ModuleNotFoundError", report)
        self.assertIn("spacy-pkuseg dragonmapper hanziconv", report)


def fake_runner(responses):
    def run(command):
        return responses.get(tuple(command), subprocess.CompletedProcess(command, 1, stdout="missing"))

    return run


def completed(stdout):
    return subprocess.CompletedProcess([sys.executable], 0, stdout=stdout)


if __name__ == "__main__":
    unittest.main()
