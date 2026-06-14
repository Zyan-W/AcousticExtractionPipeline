# Auto-MFA Project Log

Last updated: 2026-06-15

## Purpose

This repository contains a Colab-first notebook for automatic phonetic annotation. The notebook combines OpenAI Whisper for ASR-based sentence transcription with Montreal Forced Aligner (MFA) for forced alignment, with a focus on Japanese audio.

## Repository Snapshot

- `README.md`: local setup, GUI usage, language preset, and license notes.
- `auto_mfa.ipynb`: original notebook workflow retained as historical reference.
- `auto_mfa_tool/`: local Python/Tkinter desktop tool.

## Notebook Workflow

1. Run in Google Colab, preferably with a T4 GPU.
2. Install Whisper and FFmpeg.
3. Load audio either by direct Colab upload or from Google Drive.
4. Run Whisper with `--model small --language ja --output_format all`.
5. Convert Whisper `.json` segment output into sentence-tier Praat TextGrid files using `praatio`.
6. Copy raw `.wav` audio and generated `.TextGrid` files into an MFA input folder.
7. Install MFA through `condacolab` and `mamba`.
8. Download MFA Japanese acoustic and dictionary models, then run `mfa align`.
9. Export aligned TextGrid files to the MFA output folder.

## Key Paths Used In The Notebook

- Google Drive project folder: `/content/drive/MyDrive/auto-mfa`
- Raw audio: `/content/drive/MyDrive/auto-mfa/raw_audio`
- Whisper output: `/content/drive/MyDrive/auto-mfa/output`
- MFA input: `/content/drive/MyDrive/auto-mfa/mfa-input`
- MFA output: `/content/drive/MyDrive/auto-mfa/mfa-output`

## Current Implementation Notes

- The notebook is designed as an interactive Colab recipe and is retained as historical reference.
- The notebook outputs have been cleared before Apache-2.0 release preparation to avoid publishing Colab-generated frontend snippets, install logs, or transient runtime output.
- A first local GUI implementation now lives in `auto_mfa_tool/`.
- The default `python -m auto_mfa_tool` entrypoint now opens a Tkinter environment guide.
- The main annotation GUI can be launched directly with `python -m auto_mfa_tool --app`.
- Double-click startup wrappers now exist for Windows (`run_auto_mfa_windows.bat`) and macOS (`run_auto_mfa_macos.command`).
- Command-line startup scripts also exist for Windows (`run_auto_mfa_windows.ps1`) and macOS (`run_auto_mfa_macos.sh`); they check/create the `auto-mfa` environment and launch the main GUI.
- The macOS `.command` and `.sh` startup scripts must be tracked with executable file mode so zsh/Finder can run them directly after clone.
- Startup scripts run a quiet NumPy/PyTorch/MFA/tokenizer runtime check before downloading MFA models; if an existing environment is stale or missing MFA Japanese tokenizer dependencies (`spacy`, `sudachipy`, `sudachidict-core`), they run `env update -n auto-mfa -f environment.yml --prune` before launching.
- Startup scripts search common Miniforge/Miniconda locations and can fall back from `mamba` to `conda`, so users do not need to add Miniforge to the global PATH.
- Startup scripts and the environment guide download the official MFA presets used by the GUI after creating the isolated environment.
- `environment.yml` defines an isolated `auto-mfa` mamba environment for `python=3.11`, `numpy<2`, `ffmpeg`, `montreal-forced-aligner`, `spacy`, `sudachipy`, `sudachidict-core`, and `openai-whisper`.
- The main tool assumes `whisper`, `ffmpeg`, and `mfa` are available in the active environment or through `mamba run -n auto-mfa`.
- The main GUI includes a `Check Environment` button that verifies the active Python, `whisper`, `ffmpeg`, `mfa`, the NumPy/PyTorch bridge, and Japanese tokenizer support before a long Whisper/MFA run.
- The pipeline runs the same NumPy/PyTorch preflight before invoking Whisper, so stale macOS environments fail early with a clear environment report instead of a Whisper stack trace such as `RuntimeError: Numpy is not available`.
- `.gitignore` excludes Python caches, local virtual environments, OS metadata, local audio files, generated TextGrids, and Auto-MFA output directories so GitHub Desktop does not offer them for commit after local runs.
- Release documentation now includes `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, and `AI_USAGE.md`.
- The first offline release target is Windows x86_64 only. It should provide a copyable offline folder and GitHub Release asset while keeping generated environment/model bundles out of Git.
- Windows offline runtime should set `AUTO_MFA_OFFLINE=1`, point Whisper at a bundled `small` model cache, point MFA at bundled pretrained models via `MFA_ROOT_DIR`, and restrict the GUI to the bundled Whisper model.
- Offline release build tooling should create/update the `auto-mfa` environment, download the GUI's official MFA presets, download Whisper `small`, pack the Windows environment with `conda-pack`, and emit a manifest plus SHA-256 checksums.
- Before the first offline release push/upload, inspect staged files and generated manifests for local paths, audio files, TextGrid outputs, tokens, usernames, and device-specific data.
- The conversion function reads Whisper JSON `segments` and creates one interval tier named `sentences`.
- The main GUI language preset dropdown includes only MFA official acoustic/dictionary pairs that were confirmed in MFA model documentation: Japanese (`japanese_mfa`/`japanese_mfa`), Korean (`korean_mfa`/`korean_mfa`), English (`english_mfa`/`english_mfa`), and Mandarin Chinese (`mandarin_mfa`/`mandarin_china_mfa`).
- Minnan/Hokkien is intentionally not listed because the official MFA acoustic and dictionary indexes did not show a confirmed paired preset.
- The environment guide and main GUI use a small waveform window icon generated by `auto_mfa_tool/window_icon.py`; no external image asset is copied into the repository.
- Existing saved notebook outputs show a successful sample run with two recordings and MFA export completed.
- Some notebook comments and output text appear mojibake/encoding-corrupted in the local `.ipynb`; the functional code is still understandable.

## Handoff Notes

- Start by reading `auto_mfa.ipynb` cells 4, 9, 17, 21, 22, 26, and 27.
- For the local tool, start by reading `auto_mfa_tool/pipeline.py` and `auto_mfa_tool/gui.py`.
- Language presets live in `auto_mfa_tool/presets.py`; keep GUI dropdowns, setup downloads, tests, and README aligned with that file.
- Window icon drawing lives in `auto_mfa_tool/window_icon.py`.
- The GUI creates `whisper-output/`, `mfa-input/`, and `mfa-output/` inside the selected output directory.
- The next likely improvement is packaging the GUI as a Windows executable after the Python version is validated on real audio.
- Keep generated audio data, Whisper outputs, and MFA outputs out of version control unless explicitly requested.
