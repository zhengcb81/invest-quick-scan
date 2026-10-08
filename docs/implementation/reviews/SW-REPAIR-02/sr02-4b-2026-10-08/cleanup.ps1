param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$swrRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$swrRun = [IO.Path]::GetFullPath((Join-Path $swrRepo 'runs/sw-sr02-4b-2026-10-08-01'))
$swrEvidence = Join-Path $swrRepo 'docs/implementation/intake/SW-REPAIR-02/2026-10-08-sr02-4b'
$swrBaselinePath = Join-Path $swrEvidence 'cleanup-baseline.json'
$swrManifest = Get-Content -LiteralPath $swrBaselinePath -Raw -Encoding utf8 | ConvertFrom-Json
$swrLstat = Get-Content -LiteralPath (Join-Path $swrEvidence 'cleanup-lstat.json') -Raw -Encoding utf8 | ConvertFrom-Json
$swrResult = Get-Content -LiteralPath (Join-Path $swrEvidence 'verification/result.json') -Raw -Encoding utf8 | ConvertFrom-Json
$swrBaselineHash = (Get-FileHash -LiteralPath $swrBaselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $swrRun.StartsWith((Join-Path $swrRepo 'runs') + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($swrManifest.absolute_root) -ne $swrRun -or [IO.Path]::GetFullPath($swrLstat.root) -ne $swrRun) { throw 'Wrong deletion root' }
if ($swrLstat.baseline_sha256 -ne $swrBaselineHash -or $swrLstat.files_verified -ne $swrManifest.files.Count -or $swrLstat.hardlinks -ne 0 -or $swrLstat.reparse_points -ne 0) { throw 'Missing lstat proof' }
if ($swrResult.snapshot_changes_after_tests.Count -ne 0 -or $swrResult.source_repository_writes -ne 0 -or $swrResult.paid_api_requests -ne 0) { throw 'Acceptance proof incomplete' }
$swrProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.ProcessId -ne $PID -and ($_.CommandLine -like '*sw-sr02-4b-2026-10-08-01*' -or
    ($_.CommandLine -like '*SW-REPAIR-02*sr02-4b-2026-10-08*' -and $_.CommandLine -like '*guarded_run.py*'))
})
if ($swrProcesses.Count) { throw 'Private process active' }
$swrListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in @($swrResult.browser.ports) })
if ($swrListeners.Count) { throw 'Private listener active' }
$swrQueue = [Collections.Generic.Queue[string]]::new()
$swrQueue.Enqueue($swrRun)
$swrActualFiles = @()
$swrActualDirs = @()
while ($swrQueue.Count) {
    $swrDirectory = $swrQueue.Dequeue()
    $swrNode = Get-Item -LiteralPath $swrDirectory -Force
    if (($swrNode.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrNode.LinkType) { throw 'Directory reparse before traversal' }
    foreach ($swrChild in @(Get-ChildItem -LiteralPath $swrDirectory -Force)) {
        $swrFull = [IO.Path]::GetFullPath($swrChild.FullName)
        if (-not $swrFull.StartsWith($swrRun + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or ($swrChild.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrChild.LinkType) { throw 'Unsafe child' }
        $swrRelative = $swrFull.Substring($swrRun.Length + 1).Replace('\','/')
        if ($swrChild.PSIsContainer) { $swrActualDirs += $swrRelative; $swrQueue.Enqueue($swrFull) }
        else { $swrActualFiles += $swrRelative }
    }
}
if ($swrActualFiles.Count -ne $swrManifest.files.Count -or @(Compare-Object @($swrActualFiles | Sort-Object) @($swrManifest.files.path | Sort-Object)).Count) { throw 'File set drift' }
if ($swrActualDirs.Count -ne $swrManifest.directories.Count -or @(Compare-Object @($swrActualDirs | Sort-Object) @($swrManifest.directories | Sort-Object)).Count) { throw 'Directory set drift' }
foreach ($swrFile in $swrManifest.files) {
    $swrPath = [IO.Path]::GetFullPath((Join-Path $swrRun $swrFile.path))
    if (-not $swrPath.StartsWith($swrRun + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest escaped' }
    $swrItem = Get-Item -LiteralPath $swrPath -Force
    if ($swrItem.Length -ne $swrFile.bytes -or (Get-FileHash -LiteralPath $swrPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $swrFile.sha256) { throw 'Preflight byte drift' }
}
$swrReceipt = [ordered]@{schema='swr_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;root=$swrRun;files_verified=$swrManifest.files.Count;baseline_sha256=$swrBaselineHash;process_matches=0;listener_matches=0;known_sessions_exited=$swrManifest.known_sessions_exited;junction_nodes_unlinked=6;scope='Single IQS private test root; StockWiki, shared TEMP, Phase92 and opencode.json untouched'}
$swrReceiptPath = Join-Path $swrEvidence 'cleanup-receipt.json'
if (-not $Apply) {
    $swrReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $swrEvidence 'cleanup-dry-run.json') -Encoding utf8
    Write-Output ('dry_run verified_files=' + $swrManifest.files.Count)
    exit 0
}
foreach ($swrFile in $swrManifest.files) {
    $swrPath = [IO.Path]::GetFullPath((Join-Path $swrRun $swrFile.path))
    $swrItem = Get-Item -LiteralPath $swrPath -Force
    if (($swrItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrItem.LinkType -or $swrItem.Length -ne $swrFile.bytes -or (Get-FileHash -LiteralPath $swrPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $swrFile.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $swrPath -Force
}
foreach ($swrRelative in @($swrManifest.directories | Sort-Object Length -Descending)) {
    $swrPath = [IO.Path]::GetFullPath((Join-Path $swrRun $swrRelative))
    $swrItem = Get-Item -LiteralPath $swrPath -Force
    if (($swrItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrItem.LinkType -or @(Get-ChildItem -LiteralPath $swrPath -Force).Count) { throw 'Changed/nonempty directory' }
    [IO.Directory]::Delete($swrPath,$false)
}
if (@(Get-ChildItem -LiteralPath $swrRun -Force).Count) { throw 'Root not empty' }
[IO.Directory]::Delete($swrRun,$false)
$swrReceipt.applied=$true
$swrReceipt['files_deleted']=$swrManifest.files.Count
$swrReceipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$swrReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $swrReceiptPath -Encoding utf8
Write-Output ('deleted_owned_files=' + $swrManifest.files.Count)
