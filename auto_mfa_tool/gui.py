# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .pipeline import PipelineConfig, PipelineError, run_pipeline
from .presets import (
    DEFAULT_LANGUAGE_PRESET,
    acoustic_model_choices,
    dictionary_choices,
    find_preset,
    preset_labels,
)
from .runtime_checks import check_current_environment, environment_is_ready, format_environment_report
from .window_icon import apply_waveform_icon


class AutoMfaApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Auto-MFA")
        apply_waveform_icon(self)
        self.geometry("860x620")
        self.minsize(760, 520)

        self._log_queue: queue.Queue[str] = queue.Queue()
        self._worker: threading.Thread | None = None

        self.audio_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.language_preset = tk.StringVar(value=DEFAULT_LANGUAGE_PRESET.label)
        self.language = tk.StringVar(value=DEFAULT_LANGUAGE_PRESET.whisper_language)
        self.whisper_model = tk.StringVar(value="small")
        self.mfa_acoustic_model = tk.StringVar(value=DEFAULT_LANGUAGE_PRESET.mfa_acoustic_model)
        self.mfa_dictionary = tk.StringVar(value=DEFAULT_LANGUAGE_PRESET.mfa_dictionary)
        self.status_text = tk.StringVar(value="Ready")

        self._build_ui()
        self.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        form = ttk.Frame(self, padding=12)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self._add_path_row(form, 0, "Audio folder", self.audio_dir, self._choose_audio_dir)
        self._add_path_row(form, 1, "Output folder", self.output_dir, self._choose_output_dir)

        ttk.Label(form, text="Language preset").grid(row=2, column=0, sticky="w", pady=(8, 0))
        preset_box = ttk.Combobox(
            form,
            textvariable=self.language_preset,
            values=preset_labels(),
            state="readonly",
            width=22,
        )
        preset_box.grid(row=2, column=1, sticky="w", pady=(8, 0))
        preset_box.bind("<<ComboboxSelected>>", self._apply_language_preset)

        ttk.Label(form, text="Whisper model").grid(row=2, column=2, sticky="w", padx=(12, 4), pady=(8, 0))
        model_box = ttk.Combobox(
            form,
            textvariable=self.whisper_model,
            values=("tiny", "base", "small", "medium", "large"),
            state="readonly",
            width=14,
        )
        model_box.grid(row=2, column=3, sticky="w", pady=(8, 0))

        ttk.Label(form, text="Whisper language").grid(row=3, column=0, sticky="w", pady=(8, 0))
        language_box = ttk.Combobox(
            form,
            textvariable=self.language,
            values=("ja", "ko", "en", "zh"),
            state="readonly",
            width=10,
        )
        language_box.grid(row=3, column=1, sticky="w", pady=(8, 0))

        ttk.Label(form, text="MFA acoustic").grid(row=4, column=0, sticky="w", pady=(8, 0))
        acoustic_box = ttk.Combobox(
            form,
            textvariable=self.mfa_acoustic_model,
            values=acoustic_model_choices(),
            state="readonly",
        )
        acoustic_box.grid(row=4, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(form, text="MFA dictionary").grid(row=4, column=2, sticky="w", padx=(12, 4), pady=(8, 0))
        dictionary_box = ttk.Combobox(
            form,
            textvariable=self.mfa_dictionary,
            values=dictionary_choices(),
            state="readonly",
        )
        dictionary_box.grid(row=4, column=3, sticky="ew", pady=(8, 0))

        self.check_button = ttk.Button(form, text="Check Environment", command=self._start_environment_check)
        self.check_button.grid(row=5, column=0, sticky="ew", pady=(12, 0))

        self.run_button = ttk.Button(form, text="Run", command=self._start_pipeline)
        self.run_button.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(12, 0))

        ttk.Label(form, textvariable=self.status_text).grid(row=5, column=2, columnspan=2, sticky="w", pady=(12, 0))

        log_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", height=20)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _add_path_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: callable,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, columnspan=3, sticky="ew", pady=(0, 8))
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=4, padx=(8, 0), pady=(0, 8))

    def _choose_audio_dir(self) -> None:
        directory = filedialog.askdirectory(title="Select audio folder")
        if directory:
            self.audio_dir.set(directory)

    def _choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_dir.set(directory)

    def _apply_language_preset(self, _event: tk.Event | None = None) -> None:
        preset = find_preset(self.language_preset.get())
        if not preset:
            return
        self.language.set(preset.whisper_language)
        self.mfa_acoustic_model.set(preset.mfa_acoustic_model)
        self.mfa_dictionary.set(preset.mfa_dictionary)
        self.status_text.set(f"Preset: {preset.label}")

    def _start_environment_check(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        self.log_text.delete("1.0", "end")
        self.status_text.set("Checking environment...")
        self.run_button.configure(state="disabled")
        self.check_button.configure(state="disabled")

        self._worker = threading.Thread(target=self._check_environment_worker, daemon=True)
        self._worker.start()

    def _start_pipeline(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        if not self.audio_dir.get().strip() or not self.output_dir.get().strip():
            messagebox.showerror("Auto-MFA", "Choose both an audio folder and an output folder.")
            return

        config = PipelineConfig(
            audio_dir=Path(self.audio_dir.get().strip()),
            output_dir=Path(self.output_dir.get().strip()),
            language=self.language.get().strip() or "ja",
            whisper_model=self.whisper_model.get().strip() or "small",
            mfa_acoustic_model=self.mfa_acoustic_model.get().strip() or "japanese_mfa",
            mfa_dictionary=self.mfa_dictionary.get().strip() or "japanese_mfa",
        )

        self.log_text.delete("1.0", "end")
        self.status_text.set("Running...")
        self.run_button.configure(state="disabled")
        self.check_button.configure(state="disabled")

        self._worker = threading.Thread(target=self._run_pipeline_worker, args=(config,), daemon=True)
        self._worker.start()

    def _check_environment_worker(self) -> None:
        checks = check_current_environment()
        self._queue_log("Environment check:")
        for line in format_environment_report(checks):
            self._queue_log(line)
        if environment_is_ready(checks):
            self._log_queue.put("__STATUS_CHECK_OK__")
        else:
            self._queue_log("")
            self._queue_log("Update or recreate the auto-mfa conda environment, then check again.")
            self._log_queue.put("__STATUS_CHECK_ERROR__")

    def _run_pipeline_worker(self, config: PipelineConfig) -> None:
        try:
            run_pipeline(config, log=self._queue_log)
        except PipelineError as exc:
            self._queue_log("")
            self._queue_log(f"ERROR: {exc}")
            self._log_queue.put("__STATUS_ERROR__")
        except Exception as exc:  # GUI boundary: keep unexpected failures visible.
            self._queue_log("")
            self._queue_log(f"UNEXPECTED ERROR: {exc}")
            self._log_queue.put("__STATUS_ERROR__")
        else:
            self._log_queue.put("__STATUS_DONE__")

    def _queue_log(self, message: str) -> None:
        self._log_queue.put(message)

    def _drain_log_queue(self) -> None:
        try:
            while True:
                message = self._log_queue.get_nowait()
                if message == "__STATUS_DONE__":
                    self.status_text.set("Done")
                    self.run_button.configure(state="normal")
                    self.check_button.configure(state="normal")
                elif message == "__STATUS_ERROR__":
                    self.status_text.set("Error")
                    self.run_button.configure(state="normal")
                    self.check_button.configure(state="normal")
                elif message == "__STATUS_CHECK_OK__":
                    self.status_text.set("Environment OK")
                    self.run_button.configure(state="normal")
                    self.check_button.configure(state="normal")
                elif message == "__STATUS_CHECK_ERROR__":
                    self.status_text.set("Environment needs attention")
                    self.run_button.configure(state="disabled")
                    self.check_button.configure(state="normal")
                else:
                    self.log_text.insert("end", message + "\n")
                    self.log_text.see("end")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)


def main() -> None:
    app = AutoMfaApp()
    app.mainloop()
