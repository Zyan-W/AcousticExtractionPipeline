# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence


ENV_NAME = "auto-mfa"
CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ToolCheck:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class EnvironmentStatus:
    python_executable: str
    python_version: str
    project_root: Path
    environment_file: Path
    environment_file_exists: bool
    mamba_path: str | None
    env_exists: bool
    tools: tuple[ToolCheck, ...] = field(default_factory=tuple)
    messages: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ready(self) -> bool:
        return bool(self.mamba_path and self.env_exists and self.tools and all(tool.ok for tool in self.tools))

    @property
    def can_create(self) -> bool:
        return bool(self.mamba_path and self.environment_file_exists and not self.env_exists)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def environment_file(root: Path | None = None) -> Path:
    return (root or project_root()) / "environment.yml"


def build_create_env_command(root: Path | None = None) -> list[str]:
    return ["mamba", "env", "create", "-f", str(environment_file(root))]


def build_launch_command() -> list[str]:
    return ["mamba", "run", "-n", ENV_NAME, "python", "-m", "auto_mfa_tool", "--app"]


def check_environment(
    root: Path | None = None,
    which: Callable[[str], str | None] = shutil.which,
    run: CommandRunner | None = None,
) -> EnvironmentStatus:
    root = root or project_root()
    env_file = environment_file(root)
    mamba_path = which("mamba")
    messages = [
        f"Python: {sys.version.split()[0]}",
        f"Python executable: {sys.executable}",
    ]

    if not env_file.exists():
        messages.append(f"Missing environment file: {env_file}")

    if not mamba_path:
        messages.append("mamba: not found. Install Miniforge first, then run this guide again.")
        return EnvironmentStatus(
            python_executable=sys.executable,
            python_version=sys.version,
            project_root=root,
            environment_file=env_file,
            environment_file_exists=env_file.exists(),
            mamba_path=None,
            env_exists=False,
            messages=tuple(messages),
        )

    messages.append(f"mamba: {mamba_path}")
    run = run or _run_capture
    env_exists, env_message = _mamba_env_exists(run)
    messages.append(env_message)

    tools: list[ToolCheck] = []
    if env_exists:
        tools = [
            _check_tool(run, "whisper", ["--help"]),
            _check_tool(run, "ffmpeg", ["-version"]),
            _check_tool(run, "mfa", ["version"]),
        ]
        for tool in tools:
            messages.append(f"{tool.name}: {'ok' if tool.ok else 'missing'} - {tool.detail}")
    else:
        messages.append(f"Create the isolated environment with: {' '.join(build_create_env_command(root))}")

    return EnvironmentStatus(
        python_executable=sys.executable,
        python_version=sys.version,
        project_root=root,
        environment_file=env_file,
        environment_file_exists=env_file.exists(),
        mamba_path=mamba_path,
        env_exists=env_exists,
        tools=tuple(tools),
        messages=tuple(messages),
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


def _mamba_env_exists(run: CommandRunner) -> tuple[bool, str]:
    result = run(["mamba", "env", "list", "--json"])
    if result.returncode != 0:
        return False, "Could not list mamba environments."
    try:
        envs = json.loads(result.stdout).get("envs", [])
    except json.JSONDecodeError:
        return False, "Could not parse mamba environment list."

    env_exists = any(Path(env).name == ENV_NAME or str(env).endswith(f"/{ENV_NAME}") for env in envs)
    if not env_exists:
        env_exists = any(str(env).endswith(f"\\{ENV_NAME}") for env in envs)
    return env_exists, f"{ENV_NAME} environment: {'found' if env_exists else 'not found'}"


def _check_tool(run: CommandRunner, tool: str, args: Sequence[str]) -> ToolCheck:
    result = run(["mamba", "run", "-n", ENV_NAME, tool, *args])
    if result.returncode == 0:
        return ToolCheck(tool, True, "available in isolated environment")
    output = " ".join(result.stdout.split())[:180]
    return ToolCheck(tool, False, output or "command failed")
