# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Sequence


PYTHON_RUNTIME_CHECK_CODE = (
    "import numpy as np; "
    "import torch; "
    "torch.from_numpy(np.zeros(1, dtype=np.float32)); "
    "print(f'numpy={np.__version__}; torch={torch.__version__}')"
)

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class RuntimeCheck:
    name: str
    ok: bool
    detail: str
    fix_hint: str = ""


def check_current_environment(
    which: Callable[[str], str | None] = shutil.which,
    run: CommandRunner | None = None,
    python_executable: str | None = None,
) -> tuple[RuntimeCheck, ...]:
    run = run or _run_capture
    python_executable = python_executable or sys.executable
    return (
        RuntimeCheck("python", True, f"{sys.version.split()[0]} at {python_executable}"),
        _check_command("whisper", which),
        _check_command("ffmpeg", which),
        _check_command("mfa", which),
        _check_numpy_torch(run, python_executable),
    )


def environment_is_ready(checks: Sequence[RuntimeCheck]) -> bool:
    return all(check.ok for check in checks)


def format_environment_report(checks: Sequence[RuntimeCheck]) -> list[str]:
    lines: list[str] = []
    for check in checks:
        status = "OK" if check.ok else "ERROR"
        lines.append(f"[{status}] {check.name}: {check.detail}")
        if check.fix_hint and not check.ok:
            lines.append(f"       Fix: {check.fix_hint}")
    return lines


def _check_command(name: str, which: Callable[[str], str | None]) -> RuntimeCheck:
    path = which(name)
    if path:
        return RuntimeCheck(name, True, path)
    return RuntimeCheck(
        name,
        False,
        "not found on PATH",
        "Launch from the auto-mfa conda environment or recreate it from environment.yml.",
    )


def _check_numpy_torch(run: CommandRunner, python_executable: str) -> RuntimeCheck:
    result = run([python_executable, "-c", PYTHON_RUNTIME_CHECK_CODE])
    output = " ".join(result.stdout.split())[:240]
    if result.returncode == 0:
        return RuntimeCheck("numpy/torch", True, output or "available")
    return RuntimeCheck(
        "numpy/torch",
        False,
        output or "runtime check failed",
        "Run `mamba env update -n auto-mfa -f environment.yml` or recreate the auto-mfa environment.",
    )


def _run_capture(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
