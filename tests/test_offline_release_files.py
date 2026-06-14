# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class OfflineReleaseFileTest(unittest.TestCase):
    def test_windows_offline_powershell_launcher_sets_offline_runtime(self):
        script = (ROOT / "run_auto_mfa_windows_offline.ps1").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: Apache-2.0", script)
        self.assertIn("AUTO_MFA_OFFLINE", script)
        self.assertIn("AUTO_MFA_WHISPER_MODEL_DIR", script)
        self.assertIn("AUTO_MFA_BUNDLED_WHISPER_MODELS", script)
        self.assertIn("MFA_ROOT_DIR", script)
        self.assertIn("Expand-Archive", script)
        self.assertIn("conda-unpack", script)
        self.assertIn("$SmokeTest", script)
        self.assertIn("python.exe", script)
        self.assertIn("-m\", \"auto_mfa_tool\", \"--app", script)

    def test_windows_offline_batch_wrapper_invokes_powershell_launcher(self):
        script = (ROOT / "run_auto_mfa_windows_offline.bat").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: Apache-2.0", script)
        self.assertIn("run_auto_mfa_windows_offline.ps1", script)
        self.assertIn("-ExecutionPolicy Bypass", script)
        self.assertIn("%*", script)

    def test_build_script_creates_expected_bundle_assets(self):
        script = (ROOT / "tools" / "build_windows_offline_release.ps1").read_text(encoding="utf-8")

        self.assertIn("conda-pack", script)
        self.assertIn("--ignore-missing-files", script)
        self.assertIn("Test-FFmpegRedistributionBuild", script)
        self.assertIn("Refusing to build an offline redistributable bundle with GPL-enabled FFmpeg", script)
        self.assertIn("whisper.load_model('small'", script)
        self.assertIn("MFA_ROOT_DIR", script)
        self.assertIn("offline_manifest.py", script)
        self.assertIn("offline_release_safety.py", script)
        self.assertIn("SHA256SUMS.txt", script)
        self.assertIn("auto-mfa-env-windows-x86_64.zip", script)
        self.assertIn("ReleaseAssetLimitBytes", script)

    def test_windows_offline_workflow_uses_windows_runner_and_smoke_test(self):
        workflow = (ROOT / ".github" / "workflows" / "windows-offline-release.yml").read_text(encoding="utf-8")

        self.assertIn("windows-2025", workflow)
        self.assertIn("build_windows_offline_release.ps1", workflow)
        self.assertIn("-SmokeTest", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("gh release create", workflow)
        self.assertIn("gh release upload", workflow)

    def test_gitignore_excludes_offline_build_outputs(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("/dist/", gitignore)
        self.assertIn("/runtime/", gitignore)
        self.assertIn("/payload/", gitignore)
        self.assertIn("/models/", gitignore)


if __name__ == "__main__":
    unittest.main()
