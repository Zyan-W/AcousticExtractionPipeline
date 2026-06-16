# SPDX-License-Identifier: Apache-2.0

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvName = "auto-mfa"
$EnvFile = Join-Path $ProjectRoot "environment.yml"
$RuntimeCheckCode = "import numpy as np; import torch; torch.from_numpy(np.zeros(1, dtype=np.float32)); import montreal_forced_aligner; import spacy; import sudachipy; import sudachidict_core; import jamo; from mecab import MeCab; import spacy_pkuseg; import dragonmapper; import hanziconv; print('runtime ok')"
$ModelDownloads = @(
    @("acoustic", "japanese_mfa"),
    @("dictionary", "japanese_mfa"),
    @("acoustic", "korean_mfa"),
    @("dictionary", "korean_mfa"),
    @("acoustic", "english_mfa"),
    @("dictionary", "english_mfa"),
    @("acoustic", "mandarin_mfa"),
    @("dictionary", "mandarin_china_mfa")
)

function New-EnvTool {
    param(
        [string]$Command,
        [string]$Name
    )
    [PSCustomObject]@{
        Command = $Command
        Name = $Name
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Get-InstallRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    $baseRoots = @(
        $env:CONDA_PREFIX,
        $env:MAMBA_ROOT_PREFIX,
        (Join-Path $env:USERPROFILE "miniforge3"),
        (Join-Path $env:USERPROFILE "Miniforge3"),
        (Join-Path $env:USERPROFILE "miniconda3"),
        (Join-Path $env:USERPROFILE "Miniconda3"),
        (Join-Path $env:LOCALAPPDATA "miniforge3"),
        (Join-Path $env:LOCALAPPDATA "Miniforge3"),
        (Join-Path $env:LOCALAPPDATA "miniconda3"),
        (Join-Path $env:LOCALAPPDATA "Miniconda3"),
        (Join-Path $env:ProgramData "miniforge3"),
        (Join-Path $env:ProgramData "Miniforge3"),
        (Join-Path $env:ProgramData "miniconda3"),
        (Join-Path $env:ProgramData "Miniconda3")
    )

    foreach ($root in $baseRoots) {
        if ($root -and (Test-Path -LiteralPath $root) -and -not $roots.Contains($root)) {
            $roots.Add($root)
        }
    }

    $registryPaths = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    foreach ($registryPath in $registryPaths) {
        Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -match "Miniforge|Miniconda|Mambaforge" -and $_.InstallLocation } |
            ForEach-Object {
                if ((Test-Path -LiteralPath $_.InstallLocation) -and -not $roots.Contains($_.InstallLocation)) {
                    $roots.Add($_.InstallLocation)
                }
            }
    }

    $roots
}

function Find-EnvTool {
    foreach ($commandName in @("mamba", "mamba.bat")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($command) {
            return New-EnvTool -Command $command.Source -Name "mamba"
        }
    }

    $roots = Get-InstallRoots
    foreach ($root in $roots) {
        foreach ($relativePath in @("condabin\mamba.bat", "Scripts\mamba.exe", "Library\bin\mamba.exe")) {
            $candidate = Join-Path $root $relativePath
            if (Test-Path -LiteralPath $candidate) {
                return New-EnvTool -Command $candidate -Name "mamba"
            }
        }
    }

    foreach ($commandName in @("conda", "conda.bat")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($command) {
            return New-EnvTool -Command $command.Source -Name "conda"
        }
    }

    foreach ($root in $roots) {
        foreach ($relativePath in @("condabin\conda.bat", "Scripts\conda.exe")) {
            $candidate = Join-Path $root $relativePath
            if (Test-Path -LiteralPath $candidate) {
                return New-EnvTool -Command $candidate -Name "conda"
            }
        }
    }

    $null
}

function Test-Runtime {
    & $EnvTool.Command run -n $EnvName python -c $RuntimeCheckCode *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    & $EnvTool.Command run -n $EnvName mfa version *> $null
    return $LASTEXITCODE -eq 0
}

function Show-RuntimeCheckError {
    & $EnvTool.Command run -n $EnvName python -c $RuntimeCheckCode
    & $EnvTool.Command run -n $EnvName mfa version
}

Set-Location -LiteralPath $ProjectRoot

$EnvTool = Find-EnvTool
if (-not $EnvTool) {
    Write-Host "Miniforge/mamba/conda was not found."
    Write-Host "If Miniforge is installed in a custom folder, open Miniforge Prompt and run this script from there."
    Write-Host "Otherwise install Miniforge first, then run this script again:"
    Write-Host "https://github.com/conda-forge/miniforge"
    exit 1
}

Write-Step "Using $($EnvTool.Name): $($EnvTool.Command)"

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Write-Host "Missing environment file: $EnvFile"
    exit 1
}

Write-Step "Checking for $EnvName environment"
$envJson = & $EnvTool.Command env list --json
$envData = $envJson | ConvertFrom-Json
$envExists = $false
foreach ($envPath in $envData.envs) {
    if ((Split-Path -Leaf $envPath) -eq $EnvName) {
        $envExists = $true
        break
    }
}

if (-not $envExists) {
    Write-Step "Creating $EnvName environment"
    & $EnvTool.Command env create -f $EnvFile
}
else {
    Write-Step "$EnvName environment already exists"
}

Write-Step "Checking runtime dependencies"
if (-not (Test-Runtime)) {
    Write-Host "The existing $EnvName environment needs to be updated."
    Write-Host "Updating from environment.yml before launching Auto-MFA..."
    & $EnvTool.Command env update -n $EnvName -f $EnvFile --prune
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Step "Rechecking runtime dependencies"
    if (-not (Test-Runtime)) {
        Write-Host "Runtime check still failed after updating the environment."
        Write-Host "Try recreating the environment manually:"
        Write-Host "$($EnvTool.Command) env remove -n $EnvName"
        Write-Host "$($EnvTool.Command) env create -f $EnvFile"
        Show-RuntimeCheckError
        exit 1
    }
}

Write-Step "Ensuring official MFA models"
foreach ($model in $ModelDownloads) {
    & $EnvTool.Command run -n $EnvName mfa model download $model[0] $model[1]
}

Write-Step "Launching Auto-MFA"
& $EnvTool.Command run -n $EnvName python -m auto_mfa_tool --app
