param(
    [ValidateSet('check', 'build')]
    [string]$Action = 'build',
    [string]$AndroidSdk = $(if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { 'F:\dev-tools\android-sdk' }),
    [string]$NdkVersion = '25.2.9519653',
    [string]$NodeDir = $(if ($env:EFFILIFE_NODE_DIR) { $env:EFFILIFE_NODE_DIR } else { 'F:\dev-tools\node' }),
    [string]$RustToolchainDir = $(if ($env:EFFILIFE_RUST_TOOLCHAIN_DIR) { $env:EFFILIFE_RUST_TOOLCHAIN_DIR } else { 'F:\dev-tools\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin' }),
    [string]$GradleHome = $(if ($env:GRADLE_USER_HOME) { $env:GRADLE_USER_HOME } else { 'F:\dev-tools\gradle-home' }),
    [string]$CargoTargetDir = $(if ($env:CARGO_TARGET_DIR) { $env:CARGO_TARGET_DIR } else { 'F:\android-target\EffiLife' })
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$deskRoot = Join-Path $repoRoot 'time-helper\desk'
$tauriRoot = Join-Path $deskRoot 'src-tauri'
$androidRoot = Join-Path $tauriRoot 'gen\android'
$ndkRoot = Join-Path $AndroidSdk "ndk\$NdkVersion"
$cargo = Join-Path $RustToolchainDir 'cargo.exe'
$rustc = Join-Path $RustToolchainDir 'rustc.exe'
$npm = Join-Path $NodeDir 'npm.cmd'

function Assert-Path([string]$path, [string]$label) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "$label not found: $path"
    }
}

Assert-Path $AndroidSdk 'Android SDK'
Assert-Path $ndkRoot 'Android NDK'
Assert-Path $cargo 'Cargo'
Assert-Path $rustc 'Rustc'
Assert-Path $npm 'npm'
Assert-Path (Join-Path $androidRoot 'gradlew.bat') 'Generated Android Gradle wrapper'

$env:ANDROID_HOME = $AndroidSdk
$env:ANDROID_SDK_ROOT = $AndroidSdk
$env:NDK_HOME = $ndkRoot
$env:GRADLE_USER_HOME = $GradleHome
$env:CARGO_TARGET_DIR = $CargoTargetDir
$env:PATH = "$NodeDir;$RustToolchainDir;$(Join-Path $AndroidSdk 'platform-tools');$env:PATH"

if ($Action -eq 'check') {
    Write-Output "Android SDK: $AndroidSdk"
    Write-Output "Android NDK: $ndkRoot"
    Write-Output "Cargo: $cargo"
    Write-Output "Gradle home: $GradleHome"
    Write-Output 'Managed Android build environment: ready'
    exit 0
}

$library = Join-Path $CargoTargetDir 'aarch64-linux-android\release\libefflife_desk_lib.so'
$buildStart = Get-Date
Push-Location $deskRoot
try {
    & $npm run mobile:android:build
    $tauriExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
if ($tauriExitCode -ne 0) {
    if (-not (Test-Path -LiteralPath $library) -or (Get-Item -LiteralPath $library).LastWriteTime -lt $buildStart) {
        throw "Tauri Android build failed before producing a fresh Rust library (exit code $tauriExitCode)"
    }
    Write-Warning "Tauri Android build stopped at the Windows symlink step; continuing with the fresh Rust library and managed Gradle build."
}

$jniLibrary = Join-Path $androidRoot 'app\src\main\jniLibs\arm64-v8a\libefflife_desk_lib.so'
Assert-Path $library 'Android Rust library'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $jniLibrary) | Out-Null
Copy-Item -LiteralPath $library -Destination $jniLibrary -Force

$assets = Join-Path $androidRoot 'app\src\main\assets'
New-Item -ItemType Directory -Force -Path $assets | Out-Null
Get-ChildItem -LiteralPath $assets -Force | Remove-Item -Recurse -Force
$frontendDist = Join-Path $deskRoot 'dist'
Assert-Path $frontendDist 'Unified frontend dist'
Get-ChildItem -LiteralPath $frontendDist -Force | Copy-Item -Destination $assets -Recurse -Force

$gradleProperties = Join-Path $androidRoot 'gradle.properties'
if (-not (Test-Path -LiteralPath $gradleProperties)) {
    Set-Content -LiteralPath $gradleProperties -Value 'android.overridePathCheck=true' -Encoding ASCII
} elseif (-not (Select-String -LiteralPath $gradleProperties -Pattern '^android\.overridePathCheck\s*=\s*true\s*$' -Quiet)) {
    Add-Content -LiteralPath $gradleProperties -Value 'android.overridePathCheck=true'
}

Push-Location $androidRoot
try {
    & (Join-Path $androidRoot 'gradlew.bat') app:assembleArm64Release -x rustBuildArm64Release
    if ($LASTEXITCODE -ne 0) { throw "Android APK build failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

$apkPath = Join-Path $androidRoot 'app\build\outputs\apk\arm64\release\app-arm64-release-unsigned.apk'
Assert-Path $apkPath 'Android ARM64 unsigned APK'
$apk = Get-Item -LiteralPath $apkPath
if ($apk.Length -le 0) { throw "Android APK artifact is empty: $apkPath" }
$apkHash = (Get-FileHash -LiteralPath $apk.FullName -Algorithm SHA256).Hash
Write-Output "Android APK: $($apk.FullName)"
Write-Output "Size: $($apk.Length) bytes"
Write-Output "SHA256: $apkHash"
