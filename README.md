# Auto-MFA

An automatic audio annotation tool using Whisper ASR and Montreal Forced Aligner.

This project is released under the Apache License 2.0. See `LICENSE`,
`NOTICE`, `THIRD_PARTY_NOTICES.md`, and `AI_USAGE.md`.

The original workflow lives in `auto_mfa.ipynb`. The local tool version adds a
Tkinter environment guide and a desktop GUI that runs the same first-pass
pipeline:

1. transcribe audio with Whisper,
2. convert Whisper JSON segments into sentence-level Praat TextGrids,
3. prepare the MFA input folder,
4. run MFA alignment,
5. write aligned TextGrids to the output folder.

## Requirements

Install Python and Miniforge before first use:

- Python 3.10+ with `tkinter`
- Miniforge with `mamba`

For Apache-2.0 release compatibility, this repository does not bundle FFmpeg.
If you redistribute binaries with this project, use an FFmpeg build that fits
your redistribution policy; do not bundle a GPL-enabled FFmpeg build without
explicit approval.

The environment guide creates an isolated `auto-mfa` conda environment from
`environment.yml`. It does not install Miniforge itself and does not install
packages into the global Python environment.

## First Run

The easiest path is to use the double-click startup script for your operating
system.

Windows:

Double-click `run_auto_mfa_windows.bat`.

macOS:

Double-click `run_auto_mfa_macos.command`.

If macOS says the command file is not executable, run this once in Terminal:

```bash
chmod +x run_auto_mfa_macos.command run_auto_mfa_macos.sh
```

You can also run the scripts from a terminal.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_auto_mfa_windows.ps1
```

macOS:

```bash
bash ./run_auto_mfa_macos.sh
```

The scripts switch to the project directory, create the `auto-mfa` environment
from `environment.yml` if it is missing, download the official MFA model
presets used by the GUI, and launch the annotation GUI.
They first try to use `mamba`; if Miniforge is installed but `mamba` is not on
PATH, they search common Miniforge/Miniconda locations and can fall back to
`conda`.

You can also open the environment guide manually from the repository root:

```powershell
python -m auto_mfa_tool
```

On macOS, use `python3` if `python` does not point to Python 3:

```bash
python3 -m auto_mfa_tool
```

The environment guide opens first:

1. Click `Check Environment`.
2. If Miniforge/mamba is found and `auto-mfa` does not exist, click `Create Environment`.
3. After the isolated environment is ready, click `Launch Tool`.

`Launch Tool` starts the main app with:

```bash
mamba run -n auto-mfa python -m auto_mfa_tool --app
```

This keeps `python`, `whisper`, `ffmpeg`, and `mfa` inside the same isolated
environment.

## Command-Line Alternative

You can also create and use the environment manually:

```bash
mamba env create -f environment.yml
mamba activate auto-mfa
python -m auto_mfa_tool --app
```

The startup scripts and environment guide download the GUI's official MFA
presets automatically. If you set up the environment manually, install the same
models inside the `auto-mfa` environment:

```bash
mfa model download acoustic japanese_mfa
mfa model download dictionary japanese_mfa
mfa model download acoustic korean_mfa
mfa model download dictionary korean_mfa
mfa model download acoustic english_mfa
mfa model download dictionary english_mfa
mfa model download acoustic mandarin_mfa
mfa model download dictionary mandarin_china_mfa
```

## Run The Annotation GUI Directly

After the environment is active, open the main tool directly with:

```bash
python -m auto_mfa_tool --app
```

Choose an audio folder and an output folder, then click `Run`.

Supported audio extensions are `.wav`, `.mp3`, `.m4a`, and `.flac`.

The language preset dropdown contains only MFA official acoustic/dictionary
pairs confirmed in the MFA model documentation:

| GUI preset | Whisper language | MFA acoustic model | MFA dictionary |
| --- | --- | --- | --- |
| Japanese | `ja` | `japanese_mfa` | `japanese_mfa` |
| Korean | `ko` | `korean_mfa` | `korean_mfa` |
| English | `en` | `english_mfa` | `english_mfa` |
| Mandarin Chinese | `zh` | `mandarin_mfa` | `mandarin_china_mfa` |

Minnan/Hokkien is not listed because the current official MFA acoustic and
dictionary indexes do not provide a confirmed paired preset for it. Add it only
after an official MFA model and dictionary are available.

The output folder will contain:

- `whisper-output/`
- `mfa-input/`
- `mfa-output/`

## macOS Notes

The tool is not Windows-only. It uses Python standard-library GUI code
(`tkinter`) and cross-platform path handling. On macOS, make sure the Python
used to open the environment guide includes Tk support. The guide can confirm
that the isolated `auto-mfa` environment contains `whisper`, `ffmpeg`, and
`mfa`, but it cannot start on a machine with no Python installed.

## Code Origin And Licenses

The project source code is licensed under Apache-2.0. The local GUI and
pipeline code in `auto_mfa_tool/` are project code written for this repository.
They do not copy source from Whisper, MFA, FFmpeg, PraatIO, blogs, Stack
Overflow answers, papers, or another open-source project. The TextGrid writer
uses the public [Praat TextGrid file-format description](https://praat.org/manual/TextGrid_file_formats.html)
and implements the simple interval-tier text format directly. The window
waveform icon is generated by project code and does not use an external image
asset.

Direct local GUI imports are Python standard-library modules only:

- Python standard library, including `tkinter`: [PSF License Agreement](https://docs.python.org/3/license.html).

External command-line tools used at runtime are not bundled or copied into this
repository:

| Name | Purpose | Version | License |
| --- | --- | --- | --- |
| Python standard library, including `tkinter` | Runtime and GUI | Python 3.10+ expected; user-installed | [PSF License Agreement](https://docs.python.org/3/license.html) |
| Miniforge / mamba / conda | Environment management and isolated dependency creation | User-installed; not pinned or bundled | [BSD-3-Clause](https://github.com/conda-forge/miniforge/blob/main/README.md) / [BSD-3-Clause](https://github.com/mamba-org/mamba) / [BSD-3-Clause](https://docs.conda.io/en/latest/license.html) |
| pip | Installs `openai-whisper` inside the isolated environment | Installed by `environment.yml`; package version resolved by conda-forge | [MIT License](https://github.com/pypa/pip) |
| OpenAI Whisper / `openai-whisper` | ASR transcription CLI | Installed by `environment.yml`; not pinned or bundled | [MIT License](https://github.com/openai/whisper/blob/main/LICENSE) |
| FFmpeg | Audio decoding support used by Whisper | Installed by `environment.yml`; not pinned or bundled | [LGPL v2.1+ by default](https://www.ffmpeg.org/legal.html); GPL v2+ if built with GPL components |
| Montreal Forced Aligner | Forced alignment CLI | Installed by `environment.yml`; not pinned or bundled | [MIT License](https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner) |
| MFA pretrained models, including `japanese_mfa`, `korean_mfa`, `english_mfa`, `mandarin_mfa`, and `mandarin_china_mfa` | Acoustic/dictionary models | Downloaded by the setup flow through the MFA CLI; not bundled | [CC BY 4.0](https://github.com/MontrealCorpusTools/mfa-models) |

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
