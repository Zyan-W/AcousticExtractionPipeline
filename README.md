# Auto-MFA

An automatic audio annotation tool using Whisper ASR and Montreal Forced Aligner.

The original workflow lives in `auto_mfa.ipynb`. The local tool version adds a
simple Tkinter desktop GUI that runs the same first-pass pipeline:

1. transcribe audio with Whisper,
2. convert Whisper JSON segments into sentence-level Praat TextGrids,
3. prepare the MFA input folder,
4. run MFA alignment,
5. write aligned TextGrids to the output folder.

## Requirements

Install these command-line tools before running the GUI, and make sure they are
available on `PATH`:

- Python 3.10+
- `whisper`
- `ffmpeg`
- `mfa`

The first version does not install dependencies automatically. If MFA reports a
missing model, install the Japanese defaults with:

```powershell
mfa model download acoustic japanese_mfa
mfa model download dictionary japanese_mfa
```

## Run The GUI

From the repository root:

```powershell
python -m auto_mfa_tool
```

On macOS, the command is usually:

```bash
python3 -m auto_mfa_tool
```

Choose an audio folder and an output folder, then click `Run`.

Supported audio extensions are `.wav`, `.mp3`, `.m4a`, and `.flac`.

The output folder will contain:

- `whisper-output/`
- `mfa-input/`
- `mfa-output/`

## macOS Notes

The tool is not Windows-only. It uses Python standard-library GUI code
(`tkinter`) and cross-platform path handling. On macOS, make sure the active
Python installation includes Tk support and that `whisper`, `ffmpeg`, and `mfa`
are available in the same terminal environment used to start the GUI.

## Test

```powershell
python -m unittest discover -s tests -v
```
