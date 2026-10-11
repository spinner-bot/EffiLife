[CmdletBinding()]
param(
    [ValidateSet('check', 'build')]
    [string]$Action = 'check',
    [ValidateSet('nsis', 'msi')]
    [string]$Bundle = 'nsis'
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'This helper is only available on Windows.'
}

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$desk = Join-Path $root 'time-helper\desk'
$vswhereCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'),
    (Join-Path $env:ProgramFiles 'Microsoft Visual Studio\Installer\vswhere.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

if (-not $vswhereCandidates) {
    throw 'Visual Studio Installer vswhere.exe was not found. Install the MSVC C++ build tools or run from a Developer PowerShell.'
}

$vswhere = @($vswhereCandidates)[0]
$installationPath = (& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1).Trim()
if (-not $installationPath) {
    throw 'No Visual Studio installation with the x86/x64 MSVC toolset was found.'
}

$vcvars = Join-Path $installationPath 'VC\Auxiliary\Build\vcvars64.bat'
if (-not (Test-Path -LiteralPath $vcvars)) {
    throw "MSVC environment script was not found: $vcvars"
}

# Import the complete MSVC environment into this PowerShell child process.
$environmentLines = & cmd.exe /d /s /c "call `"$vcvars`" -arch=x64 >nul && set"
foreach ($line in $environmentLines) {
    $separator = $line.IndexOf('=')
    if ($separator -le 0) { continue }
    $name = $line.Substring(0, $separator)
    $value = $line.Substring($separator + 1)
    Set-Item -Path "Env:$name" -Value $value
}

$rustBin = if ($env:EFFILIFE_RUST_TOOLCHAIN_DIR) {
    $env:EFFILIFE_RUST_TOOLCHAIN_DIR
} else {
    'F:\dev-tools\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin'
}
$nodeBin = if ($env:EFFILIFE_NODE_DIR) { $env:EFFILIFE_NODE_DIR } else { 'F:\dev-tools\node' }
$env:Path = "$rustBin;$nodeBin;$env:Path"

if ($Action -eq 'check') {
    & (Join-Path $rustBin 'cargo.exe') check --manifest-path (Join-Path $desk 'src-tauri\Cargo.toml') --target x86_64-pc-windows-msvc
} else {
    Push-Location $desk
    try {
        & (Join-Path $nodeBin 'npm.cmd') run tauri build -- --bundles $Bundle
    } finally {
        Pop-Location
    }
}

exit $LASTEXITCODE
