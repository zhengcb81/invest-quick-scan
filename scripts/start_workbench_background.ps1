[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Python,
    [Parameter(Mandatory)][string]$UiRoot,
    [Parameter(Mandatory)][string]$DashboardConfig,
    [Parameter(Mandatory)][string]$LogDirectory,
    [ValidateRange(0, 65535)][int]$Port = 0,
    [string]$DataRoot
)

$ErrorActionPreference = 'Stop'
$command = Get-Item -LiteralPath $Python
$windowless = if ($command.Name -ieq 'pythonw.exe') {
    $command.FullName
} else {
    Join-Path $command.DirectoryName 'pythonw.exe'
}
if (-not (Test-Path -LiteralPath $windowless -PathType Leaf)) {
    throw "Use an installed Windows Python with a sibling pythonw.exe: $Python"
}

$entry = (Get-Item -LiteralPath (Join-Path $PSScriptRoot 'open_dashboard.py')).FullName
$ui = (Resolve-Path -LiteralPath $UiRoot).Path
$config = (Resolve-Path -LiteralPath $DashboardConfig).Path
$arguments = @('-B', '-X', 'utf8', ('"' + $entry + '"'), '--ui-root', ('"' + $ui + '"'),
    '--dashboard-config', ('"' + $config + '"'), '--port', $Port.ToString(), '--no-refresh')
if ($DataRoot) {
    $resolvedData = (Resolve-Path -LiteralPath $DataRoot).Path
    $arguments += @('--data-root', ('"' + $resolvedData + '"'))
}

$logs = [IO.Directory]::CreateDirectory([IO.Path]::GetFullPath($LogDirectory)).FullName
$prefix = Join-Path $logs ('workbench-' + [guid]::NewGuid().ToString('N'))
$inputPath = $prefix + '.stdin'
$outputPath = $prefix + '.stdout'
$errorPath = $prefix + '.stderr'
[IO.File]::WriteAllBytes($inputPath, [byte[]]@())
$process = Start-Process -FilePath $windowless -ArgumentList $arguments `
    -WorkingDirectory (Split-Path -Parent $PSScriptRoot) -WindowStyle Hidden -PassThru `
    -RedirectStandardInput $inputPath -RedirectStandardOutput $outputPath -RedirectStandardError $errorPath
[pscustomobject]@{
    process_id = $process.Id
    executable = $windowless
    requested_port = $Port
    stdout = $outputPath
    stderr = $errorPath
}
