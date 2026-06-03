# Auto-MFA Project Log

Last updated: 2026-06-04

## Purpose

This repository contains a Colab-first notebook for automatic phonetic annotation. The notebook combines OpenAI Whisper for ASR-based sentence transcription with Montreal Forced Aligner (MFA) for forced alignment, with a focus on Japanese audio.

## Repository Snapshot

- `README.md`: one-line project description.
- `auto_mfa.ipynb`: main and currently only implementation artifact.

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
- A first local GUI implementation now lives in `auto_mfa_tool/`.
- The local tool uses Tkinter and can be launched with `python -m auto_mfa_tool`.
- The local tool assumes `whisper`, `ffmpeg`, and `mfa` are already installed and available on PATH.
- The conversion function reads Whisper JSON `segments` and creates one interval tier named `sentences`.
- The MFA command uses the `japanese_mfa` acoustic model and dictionary.
- Existing saved notebook outputs show a successful sample run with two recordings and MFA export completed.
- Some notebook comments and output text appear mojibake/encoding-corrupted in the local `.ipynb`; the functional code is still understandable.

## Handoff Notes

- Start by reading `auto_mfa.ipynb` cells 4, 9, 17, 21, 22, 26, and 27.
- For the local tool, start by reading `auto_mfa_tool/pipeline.py` and `auto_mfa_tool/gui.py`.
- The GUI creates `whisper-output/`, `mfa-input/`, and `mfa-output/` inside the selected output directory.
- The next likely improvement is packaging the GUI as a Windows executable after the Python version is validated on real audio.
- Keep generated audio data, Whisper outputs, and MFA outputs out of version control unless explicitly requested.
