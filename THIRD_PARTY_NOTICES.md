# Third-Party Notices

Auto-MFA source code is released under the Apache License 2.0. This repository
does not vendor or copy third-party source code.

## Direct Local Tool Imports

| Name | Purpose | Version | License | Use |
| --- | --- | --- | --- | --- |
| Python standard library, including `tkinter` | Runtime, GUI, filesystem, subprocess, JSON, tests | Python 3.10+ expected; user-installed | PSF License Agreement | Imported directly by `auto_mfa_tool/` and tests |
| Miniforge / mamba / conda | Isolated environment creation and dependency management | User-installed; not pinned or bundled | BSD-3-Clause | Checked and invoked by the environment guide or startup scripts; not bundled |
| pip | Installs `openai-whisper` inside the isolated environment | Installed by `environment.yml`; package version resolved by conda-forge | MIT License | Invoked by mamba during environment creation; not bundled |
| NumPy | Whisper/PyTorch runtime compatibility check | `numpy<2` from `environment.yml`; not bundled | BSD-3-Clause | Imported by a runtime check command to catch incompatible environments before transcription |
| PyTorch | Whisper runtime backend compatibility check | Installed as an `openai-whisper` dependency; not bundled | BSD-style | Imported by a runtime check command to verify the NumPy bridge used by Whisper |

## External Runtime Tools

These tools are invoked by command name and are not bundled with this
repository.

| Name | Purpose | Version | License | Use |
| --- | --- | --- | --- | --- |
| OpenAI Whisper / `openai-whisper` | Speech recognition and timestamped JSON generation | Installed into `auto-mfa` by `environment.yml`; not bundled | MIT License | Called via `whisper` CLI |
| FFmpeg | Audio decoding support used by Whisper | Installed into `auto-mfa` by `environment.yml`; not bundled | LGPL v2.1 or later by default; GPL v2 or later if built with GPL components | Called as external executable; do not redistribute a GPL-enabled build with this Apache-2.0 project without explicit approval |
| Montreal Forced Aligner | Forced alignment | Installed into `auto-mfa` by `environment.yml`; not bundled | MIT License | Called via `mfa` CLI |
| MFA pretrained models, including `japanese_mfa`, `korean_mfa`, `english_mfa`, `mandarin_mfa`, and `mandarin_china_mfa` | Official acoustic and dictionary presets for alignment | Downloaded by the setup flow through the MFA CLI; not bundled | CC BY 4.0 | Referenced by model name and downloaded through public MFA commands |

## Notebook-Only Dependencies

These appear in `auto_mfa.ipynb` as a Colab-oriented historical workflow and
are not imported by the local desktop GUI.

| Name | Purpose | Version | License | Use |
| --- | --- | --- | --- | --- |
| PraatIO / `praatio` | TextGrid writing in the original notebook workflow | Notebook installs user-selected/current package version | MIT License | Notebook-only historical workflow |
| `condacolab` | Conda setup inside Google Colab | Notebook installs user-selected/current package version | MIT License | Notebook-only historical workflow |
| Google Colab APIs | File upload and Drive mounting in Colab | Provided by Google Colab runtime | Service/API terms, not bundled project code | Notebook-only runtime APIs |

## Format And API References

- Praat TextGrid format: public file-format documentation used to implement a
  simple interval-tier writer. No Praat source code is copied.
- Whisper, FFmpeg, and MFA are used through public command-line interfaces.
- No code has been copied from specific open-source repositories, blogs,
  Stack Overflow answers, or papers.
