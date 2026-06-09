# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class StartupScriptTest(unittest.TestCase):
    def test_windows_double_click_wrapper_invokes_powershell_script(self):
        script = (ROOT / "run_auto_mfa_windows.bat").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: Apache-2.0", script)
        self.assertIn("run_auto_mfa_windows.ps1", script)
        self.assertIn("-ExecutionPolicy Bypass", script)
        self.assertIn("pause >nul", script)

    def test_windows_script_creates_environment_and_launches_app(self):
        script = (ROOT / "run_auto_mfa_windows.ps1").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: Apache-2.0", script)
        self.assertIn("Find-EnvTool", script)
        self.assertIn("miniforge3", script)
        self.assertIn("conda", script)
        self.assertIn("& $EnvTool.Command env create -f $EnvFile", script)
        self.assertIn("Ensuring official MFA models", script)
        self.assertIn("& $EnvTool.Command run -n $EnvName mfa model download $model[0] $model[1]", script)
        self.assertIn("& $EnvTool.Command run -n $EnvName python -m auto_mfa_tool --app", script)
        self.assertIn("Set-Location -LiteralPath $ProjectRoot", script)

    def test_macos_script_creates_environment_and_launches_app(self):
        script = (ROOT / "run_auto_mfa_macos.sh").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: Apache-2.0", script)
        self.assertIn("find_env_tool", script)
        self.assertIn("miniforge3", script)
        self.assertIn("conda", script)
        self.assertIn('"$ENV_TOOL" env create -f "$ENV_FILE"', script)
        self.assertIn("Ensuring official MFA models", script)
        self.assertIn('"$ENV_TOOL" run -n "$ENV_NAME" mfa model download $model', script)
        self.assertIn('"$ENV_TOOL" run -n "$ENV_NAME" python -m auto_mfa_tool --app', script)
        self.assertIn('cd "$PROJECT_ROOT"', script)

    def test_macos_double_click_wrapper_invokes_shell_script(self):
        script = (ROOT / "run_auto_mfa_macos.command").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: Apache-2.0", script)
        self.assertIn("run_auto_mfa_macos.sh", script)
        self.assertIn("Press Return to close this window", script)


if __name__ == "__main__":
    unittest.main()
