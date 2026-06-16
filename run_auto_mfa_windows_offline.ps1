# SPDX-License-Identifier: Apache-2.0

param(
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"

$BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvArchive = Join-Path $BundleRoot "payload\auto-mfa-env-windows-x86_64.zip"
$RuntimeRoot = Join-Path $BundleRoot "runtime"
$RuntimeEnv = Join-Path $RuntimeRoot "auto-mfa"
$PythonExe = Join-Path $RuntimeEnv "python.exe"
$CondaUnpackMarker = Join-Path $RuntimeEnv ".conda-unpack-complete"
$WhisperModelDir = Join-Path $BundleRoot "models\whisper"
$MfaRootDir = Join-Path $BundleRoot "models\mfa"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments = @()
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Expand-OfflineEnvironment {
    if (Test-Path -LiteralPath $PythonExe) {
        return
    }

    if ((Test-Path -LiteralPath $RuntimeEnv) -and -not (Test-Path -LiteralPath $PythonExe)) {
        throw "Runtime folder exists but python.exe is missing: $RuntimeEnv. Move or delete this folder, then rerun the offline launcher."
    }

    if (-not (Test-Path -LiteralPath $EnvArchive)) {
        throw "Missing packed environment: $EnvArchive. Download or copy the complete Windows offline bundle."
    }

    Write-Step "Extracting bundled Auto-MFA environment"
    New-Item -ItemType Directory -Force -Path $RuntimeEnv | Out-Null
    Expand-Archive -LiteralPath $EnvArchive -DestinationPath $RuntimeEnv -Force

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw "The packed environment did not contain python.exe at the expected path: $PythonExe"
    }
}

function Invoke-CondaUnpack {
    if (Test-Path -LiteralPath $CondaUnpackMarker) {
        return
    }

    $condaUnpackExe = Join-Path $RuntimeEnv "Scripts\conda-unpack.exe"
    $condaUnpackScript = Join-Path $RuntimeEnv "Scripts\conda-unpack-script.py"

    Write-Step "Finalizing relocated environment"
    if (Test-Path -LiteralPath $condaUnpackExe) {
        Invoke-Native -FilePath $condaUnpackExe
    }
    elseif (Test-Path -LiteralPath $condaUnpackScript) {
        Invoke-Native -FilePath $PythonExe -Arguments @($condaUnpackScript)
    }
    else {
        Write-Host "conda-unpack was not found; continuing because this environment may already be relocatable."
    }

    New-Item -ItemType File -Force -Path $CondaUnpackMarker | Out-Null
}

function Set-OfflineEnvironment {
    $env:PYTHONNOUSERSITE = "1"
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    $env:AUTO_MFA_OFFLINE = "1"
    $env:AUTO_MFA_WHISPER_MODEL_DIR = $WhisperModelDir
    $env:AUTO_MFA_BUNDLED_WHISPER_MODELS = "small"
    $env:MFA_ROOT_DIR = $MfaRootDir
    $env:PATH = "$RuntimeEnv;$RuntimeEnv\Scripts;$RuntimeEnv\Library\bin;$env:PATH"
    $script:OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
}

function Test-OfflineRuntime {
    Write-Step "Checking bundled offline runtime"

    $smallModel = Join-Path $WhisperModelDir "small.pt"
    if (-not (Test-Path -LiteralPath $smallModel)) {
        throw "Missing bundled Whisper small model: $smallModel"
    }

    $runtimeCheck = "import numpy as np; import torch; torch.from_numpy(np.zeros(1, dtype=np.float32)); import montreal_forced_aligner; import spacy; import sudachipy; import sudachidict_core; import jamo; from mecab import MeCab; import spacy_pkuseg; import dragonmapper; import hanziconv; print('runtime ok')"
    Invoke-Native -FilePath $PythonExe -Arguments @("-c", $runtimeCheck)

    $offlineCheck = "from auto_mfa_tool.offline import offline_mode_enabled, whisper_model_dir; import pathlib; assert offline_mode_enabled(); assert pathlib.Path(whisper_model_dir()).joinpath('small.pt').exists(); print('offline config ok')"
    Invoke-Native -FilePath $PythonExe -Arguments @("-c", $offlineCheck)

    $whisperLoadCheck = "import os, whisper; whisper.load_model('small', download_root=os.environ['AUTO_MFA_WHISPER_MODEL_DIR']); print('whisper small load ok')"
    Invoke-Native -FilePath $PythonExe -Arguments @("-c", $whisperLoadCheck)

    Invoke-Native -FilePath "whisper" -Arguments @("--help")
    Invoke-Native -FilePath "mfa" -Arguments @("model", "list", "acoustic")
    Invoke-Native -FilePath "mfa" -Arguments @("model", "list", "dictionary")
}

Set-Location -LiteralPath $BundleRoot
Expand-OfflineEnvironment
Invoke-CondaUnpack
Set-OfflineEnvironment

if ($SmokeTest) {
    Test-OfflineRuntime
    Write-Step "Offline smoke test passed"
    exit 0
}

Write-Step "Launching Auto-MFA offline"
Invoke-Native -FilePath $PythonExe -Arguments @("-m", "auto_mfa_tool", "--app")
