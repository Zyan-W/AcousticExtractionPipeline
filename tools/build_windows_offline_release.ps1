# SPDX-License-Identifier: Apache-2.0

param(
    [string]$OutputRoot = "dist\offline",
    [string]$BundleName = "Auto-MFA-windows-x86_64-offline",
    [string]$EnvName = "auto-mfa",
    [switch]$SkipEnvironmentUpdate
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([System.IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRootPath = $OutputRoot
}
else {
    $OutputRootPath = Join-Path $ProjectRoot $OutputRoot
}

$BundleRoot = Join-Path $OutputRootPath $BundleName
$PayloadDir = Join-Path $BundleRoot "payload"
$ModelsDir = Join-Path $BundleRoot "models"
$WhisperModelDir = Join-Path $ModelsDir "whisper"
$MfaRootDir = Join-Path $ModelsDir "mfa"
$LicenseSummary = Join-Path $BundleRoot "licenses\THIRD_PARTY_LICENSES.md"
$LicenseManifest = Join-Path $BundleRoot "licenses\third_party_licenses_manifest.json"
$EnvArchive = Join-Path $PayloadDir "auto-mfa-env-windows-x86_64.zip"
$BundleZip = Join-Path $OutputRootPath "$BundleName.zip"
$ReleaseAssetLimitBytes = [int64]2 * 1024 * 1024 * 1024
$RuntimeCheckCode = "import numpy as np; import torch; torch.from_numpy(np.zeros(1, dtype=np.float32)); import montreal_forced_aligner; import spacy; import sudachipy; import sudachidict_core; import jamo; from mecab import MeCab; import spacy_pkuseg; import dragonmapper; import hanziconv; print('runtime ok')"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Find-EnvTool {
    foreach ($name in @("mamba", "mamba.bat", "conda", "conda.bat")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }
    throw "Could not find mamba or conda on PATH. Install Miniforge or run this script from a Miniforge Prompt."
}

$EnvTool = Find-EnvTool

function Invoke-EnvTool {
    param([string[]]$Arguments)
    & $EnvTool @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $EnvTool $($Arguments -join ' ')"
    }
}

function Test-EnvExists {
    $envJson = & $EnvTool env list --json
    if ($LASTEXITCODE -ne 0) {
        throw "Could not list conda environments."
    }
    $envData = $envJson | ConvertFrom-Json
    foreach ($envPath in $envData.envs) {
        if ((Split-Path -Leaf $envPath) -eq $EnvName) {
            return $true
        }
    }
    return $false
}

function Copy-BundleSourceFiles {
    $items = @(
        "auto_mfa_tool",
        "environment.yml",
        "LICENSE",
        "NOTICE",
        "README.md",
        "README_OFFLINE_WINDOWS.md",
        "THIRD_PARTY_NOTICES.md",
        "OFFLINE_RELEASE_NOTICES.md",
        "AI_USAGE.md",
        "run_auto_mfa_windows_offline.ps1",
        "run_auto_mfa_windows_offline.bat"
    )

    foreach ($item in $items) {
        $source = Join-Path $ProjectRoot $item
        $destination = Join-Path $BundleRoot $item
        if (-not (Test-Path -LiteralPath $source)) {
            throw "Missing bundle source file: $source"
        }
        Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
    }
}

function Get-MfaModelSpecs {
    Push-Location $ProjectRoot
    try {
        $json = & $EnvTool run -n $EnvName python -c "import json; from auto_mfa_tool.environment import model_download_specs; print(json.dumps(model_download_specs()))"
        if ($LASTEXITCODE -ne 0) {
            throw "Could not read MFA model specs from auto_mfa_tool.environment."
        }
        return $json | ConvertFrom-Json
    }
    finally {
        Pop-Location
    }
}

function Set-TemporaryEnvVar {
    param(
        [string]$Name,
        [string]$Value,
        [scriptblock]$Body
    )
    $oldValue = [Environment]::GetEnvironmentVariable($Name, "Process")
    [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    try {
        & $Body
    }
    finally {
        [Environment]::SetEnvironmentVariable($Name, $oldValue, "Process")
    }
}

function Get-EnvPackageRecords {
    param([string]$PackageName)
    $json = & $EnvTool list -n $EnvName $PackageName --json
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect package in ${EnvName}: $PackageName"
    }
    return $json | ConvertFrom-Json
}

function Test-FFmpegRedistributionBuild {
    $records = @(Get-EnvPackageRecords -PackageName "ffmpeg")
    $ffmpeg = $records | Where-Object { $_.name -eq "ffmpeg" } | Select-Object -First 1
    if (-not $ffmpeg) {
        throw "ffmpeg is missing from the ${EnvName} environment."
    }

    $buildString = [string]$ffmpeg.build_string
    if (-not $buildString) {
        $buildString = [string]$ffmpeg.build
    }
    $buildLower = $buildString.ToLowerInvariant()

    if ($buildLower -match "(^|[_-])gpl([_-]|$)") {
        throw "Refusing to build an offline redistributable bundle with GPL-enabled FFmpeg build: $($ffmpeg.version) $buildString"
    }
    if ($buildLower -notmatch "lgpl") {
        throw "FFmpeg build string does not clearly identify an LGPL build: $($ffmpeg.version) $buildString"
    }

    Write-Host "FFmpeg redistribution check passed: $($ffmpeg.version) $buildString"
}

Write-Step "Preparing output folders"
New-Item -ItemType Directory -Force -Path $OutputRootPath | Out-Null
if (Test-Path -LiteralPath $BundleRoot) {
    Remove-Item -LiteralPath $BundleRoot -Recurse -Force
}
if (Test-Path -LiteralPath $BundleZip) {
    Remove-Item -LiteralPath $BundleZip -Force
}
if (Test-Path -LiteralPath "$BundleZip.sha256") {
    Remove-Item -LiteralPath "$BundleZip.sha256" -Force
}
New-Item -ItemType Directory -Force -Path $PayloadDir, $WhisperModelDir, $MfaRootDir | Out-Null

Write-Step "Using environment tool: $EnvTool"
if (-not $SkipEnvironmentUpdate) {
    if (Test-EnvExists) {
        Write-Step "Updating $EnvName environment"
        Invoke-EnvTool -Arguments @("env", "update", "-n", $EnvName, "-f", (Join-Path $ProjectRoot "environment.yml"), "--prune")
    }
    else {
        Write-Step "Creating $EnvName environment"
        Invoke-EnvTool -Arguments @("env", "create", "-f", (Join-Path $ProjectRoot "environment.yml"))
    }
}

Write-Step "Verifying runtime dependencies"
Invoke-EnvTool -Arguments @("run", "-n", $EnvName, "python", "-c", $RuntimeCheckCode)
Invoke-EnvTool -Arguments @("run", "-n", $EnvName, "mfa", "version")
Test-FFmpegRedistributionBuild

Write-Step "Downloading bundled Whisper small model"
Set-TemporaryEnvVar -Name "AUTO_MFA_WHISPER_MODEL_DIR" -Value $WhisperModelDir -Body {
    Invoke-EnvTool -Arguments @(
        "run", "-n", $EnvName, "python", "-c",
        "import os, whisper; whisper.load_model('small', download_root=os.environ['AUTO_MFA_WHISPER_MODEL_DIR']); print('whisper small ready')"
    )
}

Write-Step "Downloading bundled MFA preset models"
$modelSpecs = Get-MfaModelSpecs
$mfaModelLabels = New-Object System.Collections.Generic.List[string]
Set-TemporaryEnvVar -Name "MFA_ROOT_DIR" -Value $MfaRootDir -Body {
    foreach ($model in $modelSpecs) {
        $modelType = [string]$model[0]
        $modelName = [string]$model[1]
        $mfaModelLabels.Add("${modelType}:${modelName}")
        Invoke-EnvTool -Arguments @("run", "-n", $EnvName, "mfa", "model", "download", $modelType, $modelName)
    }
}

Write-Step "Installing conda-pack into base environment"
Invoke-EnvTool -Arguments @("install", "-n", "base", "-c", "conda-forge", "conda-pack", "-y")

Write-Step "Packing Windows environment"
Invoke-EnvTool -Arguments @("run", "-n", "base", "conda-pack", "-n", $EnvName, "--format", "zip", "--force", "--ignore-missing-files", "-o", $EnvArchive)

Write-Step "Copying Auto-MFA source and offline docs"
Copy-BundleSourceFiles

Write-Step "Collecting third-party license files"
Invoke-EnvTool -Arguments @(
    "run", "-n", $EnvName, "python", (Join-Path $ProjectRoot "tools\offline_license_bundle.py"),
    "--bundle-root", $BundleRoot
)
if (-not (Test-Path -LiteralPath $LicenseSummary)) {
    throw "Missing generated third-party license summary: $LicenseSummary"
}
if (-not (Test-Path -LiteralPath $LicenseManifest)) {
    throw "Missing generated third-party license manifest: $LicenseManifest"
}

Write-Step "Writing offline manifest and checksums"
Invoke-EnvTool -Arguments @(
    "run", "-n", $EnvName, "python", (Join-Path $ProjectRoot "tools\offline_manifest.py"),
    "--bundle-root", $BundleRoot,
    "--platform", "windows-x86_64",
    "--bundle-name", $BundleName,
    "--whisper-models", "small",
    "--mfa-models", ($mfaModelLabels -join ","),
    "--manifest", "offline_manifest.json",
    "--checksums", "SHA256SUMS.txt"
)

Write-Step "Checking offline release safety"
Invoke-EnvTool -Arguments @(
    "run", "-n", $EnvName, "python", (Join-Path $ProjectRoot "tools\offline_release_safety.py"),
    "--bundle-root", $BundleRoot,
    "--manifest", "offline_manifest.json"
)

Write-Step "Creating release zip"
Compress-Archive -Path (Join-Path $BundleRoot "*") -DestinationPath $BundleZip -Force
$zipInfo = Get-Item -LiteralPath $BundleZip
if ($zipInfo.Length -ge $ReleaseAssetLimitBytes) {
    throw "Release asset is $($zipInfo.Length) bytes, which is at or above GitHub's 2 GiB per-file limit."
}
$zipHash = Get-FileHash -Algorithm SHA256 -LiteralPath $BundleZip
"$($zipHash.Hash.ToLowerInvariant())  $(Split-Path -Leaf $BundleZip)" | Set-Content -LiteralPath "$BundleZip.sha256" -Encoding UTF8

Write-Step "Windows offline bundle ready"
Write-Host "Folder: $BundleRoot"
Write-Host "Release asset: $BundleZip"
Write-Host "Release asset checksum: $BundleZip.sha256"
