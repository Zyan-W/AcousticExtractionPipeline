# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import queue
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

from .environment import (
    build_create_env_command,
    build_launch_command,
    check_environment,
    project_root,
)


class EnvironmentGuideApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Auto-MFA Environment Guide")
        self.geometry("820x520")
        self.minsize(720, 460)

        self._queue: queue.Queue[str] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._launch_enabled = False
        self._create_enabled = False

        self._build_ui()
        self.after(100, self._drain_queue)
        self.after(200, self.check_environment)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.output = tk.Text(frame, wrap="word", height=18)
        self.output.grid(row=0, column=0, columnspan=3, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, command=self.output.yview)
        scrollbar.grid(row=0, column=3, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)

        self.check_button = ttk.Button(frame, text="Check Environment", command=self.check_environment)
        self.check_button.grid(row=1, column=0, sticky="ew", pady=(12, 0), padx=(0, 6))

        self.create_button = ttk.Button(frame, text="Create Environment", command=self.create_environment)
        self.create_button.grid(row=1, column=1, sticky="ew", pady=(12, 0), padx=6)

        self.launch_button = ttk.Button(frame, text="Launch Tool", command=self.launch_tool)
        self.launch_button.grid(row=1, column=2, sticky="ew", pady=(12, 0), padx=(6, 0))

        self._set_buttons(create=False, launch=False)

    def check_environment(self) -> None:
        if self._is_busy():
            return
        self.output.delete("1.0", "end")
        self._log("Checking Auto-MFA environment...\n")
        status = check_environment()
        for message in status.messages:
            self._log(message)
        self._log("")
        if status.ready:
            self._log("Ready. You can launch the Auto-MFA tool.")
        elif status.can_create:
            self._log("Environment can be created now.")
        elif status.env_exists:
            self._log("Environment exists, but one or more required commands are missing.")
        else:
            self._log("Install Miniforge/mamba or restore environment.yml, then check again.")
        self._set_buttons(create=status.can_create, launch=status.ready)

    def create_environment(self) -> None:
        if self._is_busy() or not self._create_enabled:
            return
        command = build_create_env_command()
        self._set_buttons(create=False, launch=False)
        self._log("")
        self._log("$ " + " ".join(command))
        self._worker = threading.Thread(target=self._run_streaming_command, args=(command, True), daemon=True)
        self._worker.start()

    def launch_tool(self) -> None:
        if self._is_busy() or not self._launch_enabled:
            return
        command = build_launch_command()
        self._log("")
        self._log("$ " + " ".join(command))
        try:
            subprocess.Popen(command, cwd=project_root())
        except OSError as exc:
            self._log(f"Could not launch Auto-MFA: {exc}")
        else:
            self._log("Auto-MFA launched in the auto-mfa environment.")

    def _run_streaming_command(self, command: list[str], recheck_after: bool) -> None:
        try:
            process = subprocess.Popen(
                command,
                cwd=project_root(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            self._queue.put(f"Could not start command: {exc}")
            self._queue.put("__DONE__")
            return

        assert process.stdout is not None
        for line in process.stdout:
            self._queue.put(line.rstrip())
        code = process.wait()
        self._queue.put(f"Command finished with exit code {code}.")
        if recheck_after:
            self._queue.put("__RECHECK__")
        self._queue.put("__DONE__")

    def _drain_queue(self) -> None:
        try:
            while True:
                message = self._queue.get_nowait()
                if message == "__RECHECK__":
                    self.after(50, self.check_environment)
                elif message == "__DONE__":
                    self._worker = None
                    self._set_buttons(create=self._create_enabled, launch=self._launch_enabled)
                else:
                    self._log(message)
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    def _is_busy(self) -> bool:
        return bool(self._worker and self._worker.is_alive())

    def _log(self, message: str) -> None:
        self.output.insert("end", message + "\n")
        self.output.see("end")

    def _set_buttons(self, create: bool, launch: bool) -> None:
        self._create_enabled = create
        self._launch_enabled = launch
        self.check_button.configure(state="normal")
        self.create_button.configure(state="normal" if create else "disabled")
        self.launch_button.configure(state="normal" if launch else "disabled")


def main() -> None:
    app = EnvironmentGuideApp()
    app.mainloop()
