<#
.SYNOPSIS
    Mammoth CLI installer for Windows (PowerShell 5.1+ or PowerShell 7).

.DESCRIPTION
    Installs the `mammoth` CLI with uv (pinned) and, by default, the bundled
    agent skill for Codex, Claude Code, and Cursor at user scope. It never
    requires administrator privileges, never disables TLS verification, and
    never modifies a certificate store. It honors standard HTTP proxy settings.

.PARAMETER Version
    Exact CLI version to install (X.Y.Z). The versioned release embeds a
    default; omit to install the latest published release.

.PARAMETER CliOnly
    Install only the CLI. Mutually exclusive with -SkillsOnly.

.PARAMETER SkillsOnly
    Install only the agent skill. Mutually exclusive with -CliOnly.

.PARAMETER NoModifyPath
    Do not modify the user PATH; print the manual instruction instead.

.PARAMETER NonInteractive
    Never prompt.

.PARAMETER BootstrapUvOnly
    Ensure the pinned uv executable is available, then exit. Intended for
    installation diagnostics and clean-machine verification.

.PARAMETER Local
    Build the mammoth-io SDK (repo root) and mammoth-cli wheels from this source
    checkout and install them, resolving every other runtime dependency from
    PyPI. Mirrors the POSIX installer's --local. Use bare (-Local) to build from
    the repo containing this installer's parent directory, or supply a path
    (-Local <repo>) to build from an explicit CLI project directory.

.PARAMETER LocalDir
    Explicit CLI project directory for -Local. Positional, so `-Local <repo>`
    binds here; defaults to the mammoth-cli directory containing this installer.
#>
[CmdletBinding()]
param(
    [string]$Version = "__CLI_VERSION__",
    [switch]$CliOnly,
    [switch]$SkillsOnly,
    [switch]$NoModifyPath,
    [switch]$NonInteractive,
    [switch]$BootstrapUvOnly,
    [switch]$Local,
    [Parameter(Position = 0)]
    [string]$LocalDir
)

$ErrorActionPreference = "Stop"
$UvPinnedVersion = "0.11.30"
$CliPackage = "mammoth-cli"

function Write-Log($msg) { Write-Host "mammoth-install: $msg" }
function Die($msg) { Write-Error "mammoth-install: error: $msg"; exit 1 }

if ($CliOnly -and $SkillsOnly) { Die "-CliOnly and -SkillsOnly are mutually exclusive" }
if ($BootstrapUvOnly -and ($CliOnly -or $SkillsOnly -or $Local)) {
    Die "-BootstrapUvOnly cannot be combined with -CliOnly, -SkillsOnly, or -Local"
}
$installCli = -not $SkillsOnly
$installSkills = -not $CliOnly

function Test-Platform {
    $arch = $env:PROCESSOR_ARCHITECTURE
    switch -Wildcard ($arch) {
        "AMD64" { return "x86_64" }
        "ARM64" { return "aarch64" }
        default { Die "unsupported architecture '$arch'. Install manually: uv tool install $CliPackage" }
    }
}

# Is dotted version $version >= the pinned version? Field-by-field integer
# comparison, missing fields counting as 0.
#
# POLICY: a $version that is NOT purely dotted digits — i.e. it carries any
# prerelease or build suffix such as "0.11.30rc1", "0.11.30-alpha", or
# "0.11.30+build" — does NOT satisfy the pin, even when its numeric fields would
# otherwise compare >=. A prerelease/suffixed build is not the pinned final
# release and may behave differently, so the caller bootstraps the pinned uv
# instead of trusting it. (Mirrors uv_version_ge in mammoth-install.sh.)
function Test-UvVersionAtLeastPinned([string]$version) {
    if ($version -notmatch '^[0-9]+(\.[0-9]+)*$') { return $false }
    $have = $version.Split('.')
    $want = $UvPinnedVersion.Split('.')
    $count = [Math]::Max($have.Count, $want.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $h = if ($i -lt $have.Count) { [int]$have[$i] } else { 0 }
        $w = if ($i -lt $want.Count) { [int]$want[$i] } else { 0 }
        if ($h -gt $w) { return $true }
        if ($h -lt $w) { return $false }
    }
    return $true
}

function Get-Uv {
    $existing = Get-Command uv -ErrorAction SilentlyContinue
    if ($existing) {
        # The installer promises a pinned uv ($UvPinnedVersion). Only trust an
        # already-present uv when it is at least that version AND is a clean
        # final release; an older or prerelease uv may not behave as the pin
        # expects. When it is not trusted, leave the user's uv untouched and
        # bootstrap the pinned binary into an installer-owned dir instead.
        $existingVersion = $null
        try {
            $out = (& $existing.Source --version 2>$null | Select-Object -First 1)
            $parts = ($out -split '\s+') | Where-Object { $_ -ne "" }
            if ($parts.Count -ge 2) { $existingVersion = $parts[1] }
        } catch { $existingVersion = $null }
        if ($existingVersion -and (Test-UvVersionAtLeastPinned $existingVersion)) {
            Write-Log "using existing uv $existingVersion at $($existing.Source) (>= pinned $UvPinnedVersion)"
            return $existing.Source
        }
        if (-not $existingVersion) {
            Write-Log "existing uv at $($existing.Source) reports no usable version; installing pinned uv $UvPinnedVersion instead"
        } else {
            Write-Log "existing uv $existingVersion at $($existing.Source) does not satisfy the pinned $UvPinnedVersion; installing pinned uv instead"
        }
        return Install-PinnedUv
    }
    Write-Log "uv not found; installing pinned uv $UvPinnedVersion (installer-owned, PATH untouched)"
    return Install-PinnedUv
}

# Download and install the pinned uv into a versioned, Mammoth-owned directory;
# never replace or overwrite a user's own uv. Astral's official installer
# verifies its own download. Returns the path to the installed uv.exe.
function Install-PinnedUv {
    Write-Log "installing pinned uv $UvPinnedVersion into an installer-owned dir"
    $installDir = Join-Path $env:LOCALAPPDATA "mammoth-cli\uv-$UvPinnedVersion"
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    $script = $null
    try { $script = Invoke-RestMethod "https://astral.sh/uv/$UvPinnedVersion/install.ps1" }
    catch { Die "could not download uv (offline or proxy failure). Install uv manually, then re-run." }
    # Confine the install to the Mammoth-owned dir and leave PATH untouched.
    $env:UV_UNMANAGED_INSTALL = $installDir
    $env:UV_NO_MODIFY_PATH = "1"
    & ([scriptblock]::Create($script))
    $candidates = @(
        (Join-Path $installDir "uv.exe"),
        (Join-Path $installDir "bin\uv.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    Die "uv was installed but its executable could not be located under $installDir"
}

function Install-Cli($uvBin) {
    if ($Version -and $Version -ne "__CLI_VERSION__") { $spec = "$CliPackage==$Version" } else { $spec = $CliPackage }
    Write-Log "installing $spec with uv"
    & $uvBin tool install --force $spec
    if ($LASTEXITCODE -ne 0) { Die "uv tool install failed for $spec" }
    $binDir = (& $uvBin tool dir --bin) 2>$null
    if (-not $binDir) { $binDir = Join-Path $env:USERPROFILE ".local\bin" }
    return $binDir.Trim()
}

# Build the CLI and its mammoth-io SDK dependency from this source checkout,
# then install ONLINE: the two just-built wheels are passed to uv explicitly so
# mammoth-io and mammoth-cli resolve to them, while every OTHER runtime
# dependency (typer, rich, platformdirs, ...) still resolves from PyPI. Mirrors
# install_cli_local in mammoth-install.sh. There is no offline mode here.
function Install-CliLocal($uvBin) {
    $cliDir = if ($LocalDir) {
        (Resolve-Path -LiteralPath $LocalDir).Path
    } else {
        (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
    }
    if (-not (Test-Path -LiteralPath (Join-Path $cliDir "pyproject.toml"))) {
        Die "no CLI project at '$cliDir' (pass -Local <repo>)"
    }
    # The mammoth-io SDK is the repository root that contains the CLI directory.
    $sdkDir = (Resolve-Path -LiteralPath (Join-Path $cliDir "..")).Path
    if (-not (Test-Path -LiteralPath (Join-Path $sdkDir "pyproject.toml"))) {
        Die "no mammoth-io SDK project at '$sdkDir'"
    }
    $wheelhouse = Join-Path ([System.IO.Path]::GetTempPath()) ("mammoth-wheelhouse-" + [System.Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $wheelhouse | Out-Null
    try {
        Write-Log "building mammoth-io and $CliPackage wheels from $sdkDir"
        & $uvBin build --wheel --out-dir $wheelhouse $sdkDir
        if ($LASTEXITCODE -ne 0) { Die "failed to build the mammoth-io SDK wheel" }
        & $uvBin build --wheel --out-dir $wheelhouse $cliDir
        if ($LASTEXITCODE -ne 0) { Die "failed to build the $CliPackage wheel" }
        $cliWheel = Get-ChildItem -LiteralPath $wheelhouse -Filter "mammoth_cli-*.whl" | Select-Object -First 1
        $sdkWheel = Get-ChildItem -LiteralPath $wheelhouse -Filter "mammoth_io-*.whl" | Select-Object -First 1
        if (-not $cliWheel -or -not $sdkWheel) { Die "built wheel artifacts were not found" }
        Write-Log "installing $CliPackage online (mammoth-io/$CliPackage from the local wheelhouse, other deps from PyPI)"
        # Install the exact CLI artifact and explicitly inject the exact SDK
        # artifact. PyPI stays enabled only for their third-party dependencies;
        # it cannot substitute either monorepo distribution.
        & $uvBin tool install --force $cliWheel.FullName --with $sdkWheel.FullName
        if ($LASTEXITCODE -ne 0) { Die "uv tool install failed from the local wheelhouse" }
    } finally {
        Remove-Item -LiteralPath $wheelhouse -Recurse -Force -ErrorAction SilentlyContinue
    }
    $binDir = (& $uvBin tool dir --bin) 2>$null
    if (-not $binDir) { $binDir = Join-Path $env:USERPROFILE ".local\bin" }
    return $binDir.Trim()
}

function Set-UserPath($binDir) {
    if ($NoModifyPath) { Write-Log "PATH unchanged (-NoModifyPath). Add $binDir to PATH."; return }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -and ($userPath.Split(';') -contains $binDir)) { Write-Log "PATH already contains $binDir"; return }
    $newPath = if ($userPath) { "$binDir;$userPath" } else { $binDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Log "added $binDir to the user PATH (open a new shell to pick it up)"
}

function Install-Skills($binDir) {
    $exe = Join-Path $binDir "mammoth.exe"
    if (-not (Test-Path $exe)) { $exe = "mammoth" }
    # A native exe's nonzero exit is NOT a terminating error, so the catch alone
    # never fires for a failed skill install. Inspect $LASTEXITCODE explicitly,
    # mirroring Install-Cli, so a failed skill install fails the installer. The
    # catch is retained for true terminating errors (e.g. exe not found).
    try { & $exe skill install --output json --no-input | Out-Null }
    catch { Die "skill install did not complete; run 'mammoth skill install' manually" }
    if ($LASTEXITCODE -ne 0) { Die "skill install did not complete; run 'mammoth skill install' manually" }
    Write-Log "installed the agent skill (user scope)"
}

if ($BootstrapUvOnly) {
    Test-Platform | Out-Null
    $uvBin = Get-Uv
    Write-Log "uv is available at $uvBin"
    exit 0
}

$binDir = $null
if ($installCli) {
    Test-Platform | Out-Null
    $uvBin = Get-Uv
    if ($Local) {
        $binDir = Install-CliLocal $uvBin
    } else {
        $binDir = Install-Cli $uvBin
    }
    Set-UserPath $binDir
} else {
    try { $binDir = (& uv tool dir --bin) 2>$null } catch { $binDir = Join-Path $env:USERPROFILE ".local\bin" }
}
if ($installSkills) { Install-Skills $binDir }
Write-Log "done"
