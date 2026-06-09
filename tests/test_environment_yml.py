# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class EnvironmentYmlTest(unittest.TestCase):
    def test_numpy_is_pinned_below_two_for_torch_compatibility(self):
        environment_yml = (ROOT / "environment.yml").read_text(encoding="utf-8")

        self.assertIn("python=3.11", environment_yml)
        self.assertIn("numpy<2", environment_yml)
        self.assertIn("openai-whisper", environment_yml)


if __name__ == "__main__":
    unittest.main()
