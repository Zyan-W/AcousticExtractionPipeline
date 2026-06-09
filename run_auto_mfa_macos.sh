#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="auto-mfa"
ENV_FILE="$PROJECT_ROOT/environment.yml"
ENV_TOOL=""
MODEL_DOWNLOADS=(
  "acoustic japanese_mfa"
  "dictionary japanese_mfa"
  "acoustic korean_mfa"
  "dictionary korean_mfa"
  "acoustic english_mfa"
  "dictionary english_mfa"
  "acoustic mandarin_mfa"
  "dictionary mandarin_china_mfa"
)
RUNTIME_CHECK_CODE="import numpy as np; import torch; torch.from_numpy(np.zeros(1, dtype=np.float32)); import montreal_forced_aligner; print('runtime ok')"

step() {
  printf "\n==> %s\n" "$1"
}

find_env_tool() {
  for name in mamba conda; do
    if command -v "$name" >/dev/null 2>&1; then
      command -v "$name"
      return 0
    fi
  done

  for candidate in \
    "$HOME/miniforge3/bin/mamba" \
    "$HOME/miniforge3/condabin/mamba" \
    "$HOME/Miniforge3/bin/mamba" \
    "$HOME/Miniforge3/condabin/mamba" \
    "$HOME/miniconda3/bin/conda" \
    "$HOME/miniconda3/condabin/conda" \
    "$HOME/Miniconda3/bin/conda" \
    "$HOME/Miniconda3/condabin/conda" \
    "/opt/miniforge3/bin/mamba" \
    "/opt/miniforge3/condabin/mamba" \
    "/opt/miniconda3/bin/conda" \
    "/opt/miniconda3/condabin/conda" \
    "/usr/local/miniforge3/bin/mamba" \
    "/usr/local/miniforge3/condabin/mamba"; do
    if [ -x "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done

  return 1
}

runtime_check_quiet() {
  "$ENV_TOOL" run -n "$ENV_NAME" python -c "$RUNTIME_CHECK_CODE" >/dev/null 2>&1 &&
    "$ENV_TOOL" run -n "$ENV_NAME" mfa version >/dev/null 2>&1
}

show_runtime_check_error() {
  "$ENV_TOOL" run -n "$ENV_NAME" python -c "$RUNTIME_CHECK_CODE"
  "$ENV_TOOL" run -n "$ENV_NAME" mfa version
}

cd "$PROJECT_ROOT"

if ! ENV_TOOL="$(find_env_tool)"; then
  echo "Miniforge/mamba/conda was not found."
  echo "If Miniforge is installed in a custom folder, open a Miniforge terminal and run this script from there."
  echo "Otherwise install Miniforge first, then run this script again:"
  echo "https://github.com/conda-forge/miniforge"
  exit 1
fi

step "Using environment tool: $ENV_TOOL"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing environment file: $ENV_FILE"
  exit 1
fi

step "Checking for $ENV_NAME environment"
if ! "$ENV_TOOL" env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  step "Creating $ENV_NAME environment"
  "$ENV_TOOL" env create -f "$ENV_FILE"
else
  step "$ENV_NAME environment already exists"
fi

step "Checking runtime dependencies"
if ! runtime_check_quiet; then
  echo "The existing $ENV_NAME environment needs to be updated."
  echo "Updating from environment.yml before launching Auto-MFA..."
  "$ENV_TOOL" env update -n "$ENV_NAME" -f "$ENV_FILE" --prune

  step "Rechecking runtime dependencies"
  if ! runtime_check_quiet; then
    echo "Runtime check still failed after updating the environment."
    echo "Try recreating the environment manually:"
    echo "$ENV_TOOL env remove -n $ENV_NAME"
    echo "$ENV_TOOL env create -f $ENV_FILE"
    show_runtime_check_error
    exit 1
  fi
fi

step "Ensuring official MFA models"
for model in "${MODEL_DOWNLOADS[@]}"; do
  # shellcheck disable=SC2086
  "$ENV_TOOL" run -n "$ENV_NAME" mfa model download $model
done

step "Launching Auto-MFA"
"$ENV_TOOL" run -n "$ENV_NAME" python -m auto_mfa_tool --app
