<#
.SYNOPSIS
    Opens an interactive Claude Code session for this repository with its
    vendored Planning With Files plugin.

.DESCRIPTION
    This launcher never installs or updates a Claude plugin.  It pins the
    session to the repository copy and scopes PLAN_ID, PWF_PLAN_ROOT and the
    Git Bash search path to the Claude child process only.  CLAUDE_PLUGIN_ROOT
    also makes an already-installed standalone PWF skill take its upstream
    no-op branch, so its activation-scoped hooks cannot duplicate this
    plugin's lifecycle hooks.

    Pass any Claude Code arguments after the script name, for example:
      .\tools\claude-pwf.ps1 --debug-file .\pwf-plugin-debug.log
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClaudeArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$pluginDirectory = Join-Path $PSScriptRoot 'planning-with-files'
$claudeExecutable = 'C:\Users\schne\.local\bin\claude.exe'
$gitBashExecutable = 'C:\Program Files\Git\bin\bash.exe'
$gitBashDirectory = Split-Path -Parent $gitBashExecutable
$planId = '2026-09-18-dialogforge-v2'

foreach ($requiredPath in @($repositoryRoot, $pluginDirectory, $claudeExecutable, $gitBashExecutable)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required PWF launcher path is unavailable: $requiredPath"
    }
}

$savedPath = $env:PATH
$savedPlanId = $env:PLAN_ID
$savedPlanRoot = $env:PWF_PLAN_ROOT
$savedTrustedPython = $env:PWF_TRUSTED_PYTHON
$savedClaudePluginRoot = $env:CLAUDE_PLUGIN_ROOT

try {
    # Claude Code resolves `sh` for the upstream lifecycle hooks from this
    # child environment.  No machine-level PATH or Claude configuration changes.
    $env:PATH = "$gitBashDirectory;$savedPath"
    $env:PLAN_ID = $planId
    $env:PWF_PLAN_ROOT = $repositoryRoot
    $env:CLAUDE_PLUGIN_ROOT = $pluginDirectory

    $projectPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $projectPython) {
        $env:PWF_TRUSTED_PYTHON = $projectPython
    }

    Push-Location -LiteralPath $repositoryRoot
    try {
        & $claudeExecutable --plugin-dir $pluginDirectory @ClaudeArgs
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:PATH = $savedPath
    $env:PLAN_ID = $savedPlanId
    $env:PWF_PLAN_ROOT = $savedPlanRoot
    $env:PWF_TRUSTED_PYTHON = $savedTrustedPython
    $env:CLAUDE_PLUGIN_ROOT = $savedClaudePluginRoot
}
