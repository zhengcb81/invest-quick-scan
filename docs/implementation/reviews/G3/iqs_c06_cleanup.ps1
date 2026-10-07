param([Parameter(Mandatory=$true)][string]$ManifestPath, [switch]$Apply)
$ErrorActionPreference = 'Stop'
$iqsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$intakeRoot = Join-Path $iqsRoot 'docs/implementation/intake/G3/2026-10-07-iqs-producer'
$manifestAbsolute = [IO.Path]::GetFullPath($ManifestPath)
if ($manifestAbsolute -ne (Join-Path $intakeRoot 'owned-file-manifest.json')) { throw 'Unexpected manifest path' }
$manifest = Get-Content -LiteralPath $manifestAbsolute -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne 'iqs.c06_owned_cleanup/1' -or -not $manifest.known_child_processes_terminal) { throw 'Unproven owner/terminal state' }
$outputName = if ($Apply) { 'cleanup-receipt.json' } else { 'cleanup-dry-run.json' }
$outPath = Join-Path $intakeRoot $outputName
if (Test-Path -LiteralPath $outPath) { throw 'Receipt target already exists' }
$allowedNames = @('c06-context-2026-10-07-producer-cli-01', 'c06-context-2026-10-07-producer-unit-01')
if ($manifest.own_roots.Count -ne 2) { throw 'Unexpected root count' }
$seenRoots = @{}
foreach ($owned in $manifest.own_roots) {
    $resolved = (Resolve-Path -LiteralPath $owned.root).Path
    $name = Split-Path $resolved -Leaf
    if ($name -notin $allowedNames -or $resolved -ne (Join-Path (Join-Path $iqsRoot 'runs') $name) -or $seenRoots.ContainsKey($resolved)) { throw 'Out of scope root' }
    $seenRoots[$resolved] = $true
    $all = @(Get-Item -LiteralPath $resolved -Force) + @(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
    foreach ($entry in $all) {
        if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $entry.LinkType) { throw 'Link refused' }
        if ($entry.FullName -ne $resolved -and -not $entry.FullName.StartsWith($resolved + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Scope escape' }
    }
    $actualFiles = @($all | Where-Object { -not $_.PSIsContainer })
    $actualDirs = @($all | Where-Object { $_.PSIsContainer -and $_.FullName -ne $resolved })
    if ($actualFiles.Count -ne $owned.files.Count -or $actualDirs.Count -ne $owned.directories.Count) { throw 'Inventory changed' }
    $seenFiles = @{}
    foreach ($file in $owned.files) {
        $filePath = [IO.Path]::GetFullPath($file.path)
        if (-not $filePath.StartsWith($resolved + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or $seenFiles.ContainsKey($filePath)) { throw 'Out of scope/duplicate file' }
        $seenFiles[$filePath] = $true
        $item = Get-Item -LiteralPath $filePath -Force
        if ($item.PSIsContainer -or $item.Length -ne $file.bytes -or (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) { throw 'Owned bytes changed' }
    }
    foreach ($directory in $owned.directories) {
        $directoryPath = [IO.Path]::GetFullPath($directory)
        if (-not $directoryPath.StartsWith($resolved + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or -not (Get-Item -LiteralPath $directoryPath -Force).PSIsContainer) { throw 'Out of scope directory' }
    }
}
# Strict process check is read-only and fails closed; argv tokens cannot identify
# every environment-only association, so terminal subprocess handles are also required.
$processes = @(Get-CimInstance Win32_Process)
$live = @($processes | Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -and
    ($_.CommandLine.Contains('c06_context_guarded.py') -or $_.CommandLine.Contains('iqs_c06_cli_e2e.py') -or
     $_.CommandLine.Contains($manifest.own_roots[0].root) -or $_.CommandLine.Contains($manifest.own_roots[1].root))
})
if ($live.Count -ne 0) { throw 'Potential test process still live; do not delete' }
if (-not (Test-Path -LiteralPath $manifest.old_phase92_root_must_preserve)) { throw 'Old Phase92 root unexpectedly missing' }
$deleted = @()
if ($Apply) {
    foreach ($owned in $manifest.own_roots) {
        foreach ($file in $owned.files) {
            Remove-Item -LiteralPath $file.path -Force
            $deleted += $file
        }
        foreach ($directory in @($owned.directories | Sort-Object { $_.Length } -Descending)) {
            Remove-Item -LiteralPath $directory -Force
        }
        Remove-Item -LiteralPath $owned.root -Force
    }
    foreach ($owned in $manifest.own_roots) {
        if (Test-Path -LiteralPath $owned.root) { throw 'Cleanup incomplete' }
    }
}
$receipt = [ordered]@{
    schema = 'iqs.c06_cleanup_receipt/1'
    applied = [bool]$Apply
    file_manifest_sha256 = (Get-FileHash -LiteralPath $manifestAbsolute -Algorithm SHA256).Hash.ToLowerInvariant()
    matched_live_argv_processes = $live.Count
    known_subprocess_handles_terminal = [bool]$manifest.known_child_processes_terminal
    process_check_limit = 'literal argv scan plus recorded terminal handles, not arbitrary environment detection'
    files_deleted = $deleted.Count
    removed_paths = $deleted
    roots = @($manifest.own_roots.root)
    old_phase92_root_preserved = (Test-Path -LiteralPath $manifest.old_phase92_root_must_preserve)
    shared_temp_or_external_repo_deleted = $false
}
[IO.File]::WriteAllText($outPath, ($receipt | ConvertTo-Json -Depth 10) + "`n", (New-Object Text.UTF8Encoding($false)))
Write-Output "C06 cleanup apply=$Apply files=$($deleted.Count) old_phase92_preserved=$($receipt.old_phase92_root_preserved)"
