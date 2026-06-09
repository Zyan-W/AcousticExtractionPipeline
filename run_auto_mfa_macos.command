#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

bash "$SCRIPT_DIR/run_auto_mfa_macos.sh"
AUTO_MFA_EXIT=$?

echo
if [ "$AUTO_MFA_EXIT" -ne 0 ]; then
  echo "Auto-MFA exited with code $AUTO_MFA_EXIT."
fi
read -r -p "Press Return to close this window." _
exit "$AUTO_MFA_EXIT"
