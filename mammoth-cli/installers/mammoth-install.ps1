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
#>
[CmdletBinding()]
param(
    [string]$Version = "__CLI_VERSION__",
    [switch]$CliOnly,
    [switch]$SkillsOnly,
    [switch]$NoModifyPath,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$UvPinnedVersion = "0.11.30"
$CliPackage = "mammoth-cli"

function Write-Log($msg) { Write-Host "mammoth-install: $msg" }
function Die($msg) { Write-Error "mammoth-install: error: $msg"; exit 1 }

if ($CliOnly -and $SkillsOnly) { Die "-CliOnly and -SkillsOnly are mutually exclusive" }
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

function Get-Uv {
    $existing = Get-Command uv -ErrorAction SilentlyContinue
    if ($existing) { Write-Log "using existing uv at $($existing.Source)"; return $existing.Source }
    Write-Log "uv not found; installing pinned uv $UvPinnedVersion (installer-owned, PATH untouched)"
    $script = $null
    try { $script = Invoke-RestMethod "https://astral.sh/uv/$UvPinnedVersion/install.ps1" }
    catch { Die "could not download uv (offline or proxy failure). Install uv manually, then re-run." }
    $env:UV_NO_MODIFY_PATH = "1"
    & ([scriptblock]::Create($script))
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) { Die "uv was not installed where expected" }
    return $uv.Source
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

$binDir = $null
if ($installCli) {
    Test-Platform | Out-Null
    $uvBin = Get-Uv
    $binDir = Install-Cli $uvBin
    Set-UserPath $binDir
} else {
    try { $binDir = (& uv tool dir --bin) 2>$null } catch { $binDir = Join-Path $env:USERPROFILE ".local\bin" }
}
if ($installSkills) { Install-Skills $binDir }
Write-Log "done"
