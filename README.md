# Auto-MFA

An automatic audio annotation tool using Whisper ASR and Montreal Forced Aligner.

This project is released under the Apache License 2.0. See `LICENSE`,
`NOTICE`, `THIRD_PARTY_NOTICES.md`, and `AI_USAGE.md`.

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

For Apache-2.0 release compatibility, this repository does not bundle FFmpeg.
If you redistribute binaries with this project, use an FFmpeg build that fits
your redistribution policy; do not bundle a GPL-enabled FFmpeg build without
explicit approval.

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

## Code Origin And Licenses

The project source code is licensed under Apache-2.0. The local GUI and
pipeline code in `auto_mfa_tool/` are project code written for this repository.
They do not copy source from Whisper, MFA, FFmpeg, PraatIO, blogs, Stack
Overflow answers, papers, or another open-source project. The TextGrid writer
uses the public [Praat TextGrid file-format description](https://praat.org/manual/TextGrid_file_formats.html)
and implements the simple interval-tier text format directly.

Direct local GUI imports are Python standard-library modules only:

- Python standard library, including `tkinter`: [PSF License Agreement](https://docs.python.org/3/license.html).

External command-line tools used at runtime are not bundled or copied into this
repository:

| Name | Purpose | Version | License |
| --- | --- | --- | --- |
| Python standard library, including `tkinter` | Runtime and GUI | Python 3.10+ expected; user-installed | [PSF License Agreement](https://docs.python.org/3/license.html) |
| OpenAI Whisper / `openai-whisper` | ASR transcription CLI | User-installed; not pinned or bundled | [MIT License](https://github.com/openai/whisper/blob/main/LICENSE) |
| FFmpeg | Audio decoding support used by Whisper | User-installed; not pinned or bundled | [LGPL v2.1+ by default](https://www.ffmpeg.org/legal.html); GPL v2+ if built with GPL components |
| Montreal Forced Aligner | Forced alignment CLI | User-installed; not pinned or bundled | [MIT License](https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner) |
| MFA pretrained models, including `japanese_mfa` defaults | Acoustic/dictionary models | User-downloaded; not bundled | [CC BY 4.0](https://github.com/MontrealCorpusTools/mfa-models) |

Notebook-only dependencies used by `auto_mfa.ipynb`:

| Name | Purpose | Version | License |
| --- | --- | --- | --- |
| PraatIO / `praatio` | TextGrid writing in the original notebook workflow | Notebook installs user-selected/current package version | [MIT License](https://github.com/timmahrt/praatIO) |
| `condacolab` | Conda setup inside Google Colab | Notebook installs user-selected/current package version | [MIT License](https://github.com/conda-incubator/condacolab) |
| Google Colab APIs | File upload and Drive mounting in Colab | Provided by Colab runtime | Service/API terms; not bundled project code |

The project invokes third-party tools through their public command-line
interfaces and follows the public Praat TextGrid file-format documentation. It
does not vendor third-party source code. Transitive dependencies installed by
Whisper, MFA, PraatIO, conda, or Colab remain governed by their own licenses.
See `THIRD_PARTY_NOTICES.md` for the release notice table.

## Test

```powershell
python -m unittest discover -s tests -v
```
