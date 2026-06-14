# Offline Release Notices

Auto-MFA source code is released under Apache-2.0. The Windows offline release
also redistributes third-party binaries, Python packages, model weights, and
model data so that the tool can run without internet access on the target
machine.

Before publishing an offline bundle, review the generated environment contents,
the conda package metadata, and the bundled model files. Do not publish a bundle
that includes GPL, AGPL, SSPL, BUSL, unclear-license, private, or device-local
material unless that redistribution has been explicitly approved.

## Bundled Runtime Components

| Component | Purpose | Expected license family |
| --- | --- | --- |
| Python and Python standard library | Runs Auto-MFA and Tkinter GUI | PSF License Agreement |
| conda-pack relocation files | Unpacks the bundled conda environment | BSD-3-Clause |
| pip | Package/runtime support inside the environment | MIT |
| NumPy | Whisper/PyTorch runtime bridge | BSD-3-Clause |
| PyTorch | Whisper backend | BSD-style |
| spaCy | Japanese tokenizer support used by MFA | MIT |
| SudachiPy | Japanese morphological analyzer | Apache-2.0 |
| SudachiDict Core | Japanese dictionary data | Apache-2.0 |
| OpenAI Whisper / `openai-whisper` | ASR transcription CLI | MIT |
| FFmpeg | Audio decoding for Whisper | LGPL v2.1+ by default; GPL v2+ if built with GPL components |
| Montreal Forced Aligner | Forced alignment CLI | MIT |

## Bundled Model Assets

| Asset | Purpose | Expected license |
| --- | --- | --- |
| Whisper `small` | Default offline ASR model | MIT project code; model redistribution should be reviewed before release |
| MFA `japanese_mfa`, `korean_mfa`, `english_mfa`, `mandarin_mfa` acoustic models | GUI preset acoustic models | CC BY 4.0 |
| MFA `japanese_mfa`, `korean_mfa`, `english_mfa`, `mandarin_china_mfa` dictionaries | GUI preset pronunciation dictionaries | CC BY 4.0 |

## Release Hygiene

The generated bundle must not include private audio recordings, generated
TextGrids, Whisper output, local user paths, access tokens, local shell history,
or machine-specific secrets. Check `offline_manifest.json`, `SHA256SUMS.txt`,
and the staged Git diff before uploading the first offline release.
