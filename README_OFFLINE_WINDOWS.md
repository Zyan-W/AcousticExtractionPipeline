# Auto-MFA Windows Offline Bundle

This folder is the Windows x86_64 offline distribution of Auto-MFA. It is meant
for machines that cannot download Python packages, Whisper model weights, or
MFA pretrained models during setup.

## Included

- Auto-MFA source code and Windows offline launchers.
- A packed Windows `auto-mfa` conda environment in `payload/`.
- Whisper `small` model weights in `models/whisper/`.
- Official MFA acoustic and dictionary presets used by the GUI in `models/mfa/`.
- `offline_manifest.json`, `SHA256SUMS.txt`, and release notices.
- `licenses/`, including copied package license files and a generated
  `third_party_licenses_manifest.json` for the bundled environment.

## First Run

1. Extract the offline bundle to a writable local folder.
2. Double-click `run_auto_mfa_windows_offline.bat`.
3. Wait while the bundled conda environment is unpacked on first launch.
4. Use the GUI normally after it opens.

The launcher does not require Miniforge, mamba, conda, or internet access on
the target machine. It sets:

- `AUTO_MFA_OFFLINE=1`
- `AUTO_MFA_WHISPER_MODEL_DIR=models\whisper`
- `AUTO_MFA_BUNDLED_WHISPER_MODELS=small`
- `MFA_ROOT_DIR=models\mfa`

Only Whisper `small` is bundled in this offline release.

## Smoke Test

From PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_auto_mfa_windows_offline.ps1 -SmokeTest
```

This unpacks the environment if needed and checks Python, Whisper, FFmpeg, MFA,
NumPy/PyTorch, Japanese/Korean/Chinese tokenizer support, the bundled Whisper
model, and the bundled MFA model directory.

## Verify Files

Use `SHA256SUMS.txt` to verify files inside the extracted folder. The release
zip also has a sibling `.sha256` file when built by the project release script.

## Notes

- Keep the extracted folder writable because MFA stores configuration, command
  history, temporary files, and saved model indexes under `MFA_ROOT_DIR`.
- Do not put private audio files or generated TextGrids inside this bundle
  before sharing it.
- See `OFFLINE_RELEASE_NOTICES.md` and `THIRD_PARTY_NOTICES.md` before
  redistributing the bundle.
- Preserve the `licenses/` folder when copying the bundle to USB or external
  drives; it contains the generated third-party license evidence for the
  bundled conda environment.
