$ErrorActionPreference = 'Stop'
$swrRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$swrRun = [IO.Path]::GetFullPath((Join-Path $swrRepo 'runs/sw-repair-2026-10-08-01'))
$swrEvidence = Join-Path $swrRepo 'docs/implementation/intake/SW-REPAIR-02/2026-10-08'
if (-not $swrRun.StartsWith((Join-Path $swrRepo 'runs') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Wrong private root' }
$swrProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.ProcessId -ne $PID -and ($_.CommandLine -like '*sw-repair-2026-10-08-01*' -or
    ($_.CommandLine -like '*SW-REPAIR-02*' -and $_.CommandLine -like '*guarded_run.py*'))
})
if ($swrProcesses.Count) { throw 'Private runner/browser still active' }
$swrResult = Get-Content -LiteralPath (Join-Path $swrEvidence 'verification/result.json') -Raw -Encoding utf8 | ConvertFrom-Json
$swrPorts = @($swrResult.browser.ports)
$swrListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $swrPorts })
if ($swrListeners.Count) { throw 'Acceptance listener still active' }
$swrLinks = Get-Content -LiteralPath (Join-Path $swrRun 'junction-fixtures.json') -Raw -Encoding utf8 | ConvertFrom-Json
$swrRemoved = @()
$swrReceiptPath = Join-Path $swrEvidence 'junction-removal.json'
if (Test-Path -LiteralPath $swrReceiptPath) {
    $swrRemoved = @((Get-Content -LiteralPath $swrReceiptPath -Raw -Encoding utf8 | ConvertFrom-Json).links)
}
foreach ($swrLink in $swrLinks) {
    $swrKind = $swrLink.kind
    if ($swrKind -notin @('root','parent')) { throw 'Unknown fixture' }
    $swrExpectedTarget = [IO.Path]::GetFullPath((Join-Path $swrRun "junction-fixtures/$swrKind/foreign"))
    $swrSuffix = if ($swrKind -eq 'root') { 'workspace/backups/quick_scan' } else { 'workspace/backups' }
    $swrExpectedLink = [IO.Path]::GetFullPath((Join-Path $swrRun "junction-fixtures/$swrKind/$swrSuffix"))
    if ([IO.Path]::GetFullPath($swrLink.link) -ne $swrExpectedLink -or [IO.Path]::GetFullPath($swrLink.target) -ne $swrExpectedTarget) { throw 'Fixture mapping changed' }
    foreach ($swrPath in @($swrExpectedLink, $swrExpectedTarget)) {
        if (-not $swrPath.StartsWith($swrRun + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Fixture escaped' }
    }
    if (-not (Test-Path -LiteralPath $swrExpectedLink)) {
        if (-not @($swrRemoved | Where-Object { $_.link -eq $swrExpectedLink -and $_.node_removed -and $_.target_preserved }).Count) { throw 'Missing link without earlier removal receipt' }
        continue
    }
    $swrItem = Get-Item -LiteralPath $swrExpectedLink -Force
    $swrActualTargets = @($swrItem.Target)
    if ($swrItem.LinkType -ne 'Junction' -or $swrActualTargets.Count -ne 1 -or [IO.Path]::GetFullPath($swrActualTargets[0]) -ne $swrExpectedTarget) { throw 'Not the known junction' }
    $swrTargetItem = Get-Item -LiteralPath $swrExpectedTarget -Force
    if (($swrTargetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Target itself is a reparse point' }
    $swrSentinel = Join-Path $swrExpectedTarget 'sentinel.txt'
    $swrHashBefore = (Get-FileHash -LiteralPath $swrSentinel -Algorithm SHA256).Hash.ToLowerInvariant()
    # Nonrecursive native removal deletes the junction node, never the target tree.
    [IO.Directory]::Delete($swrExpectedLink, $false)
    if (Test-Path -LiteralPath $swrExpectedLink) { throw 'Junction remains' }
    $swrHashAfter = (Get-FileHash -LiteralPath $swrSentinel -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($swrHashBefore -ne $swrHashAfter) { throw 'Sentinel changed' }
    $swrRemoved += [pscustomobject]@{kind=$swrKind;link=$swrExpectedLink;target=$swrExpectedTarget;node_removed=$true;target_preserved=$true;sentinel_sha256=$swrHashAfter}
}
# Four original worker tests also deliberately created junctions in this private basetemp.
# These exact pairs were inventoried without descending into any link.
$swrTestPairs = @(
    @('pytest-core/test_restore_refuses_a_junctio1/target_jctp_ok/data', 'pytest-core/test_restore_refuses_a_junctio1/elsewhere_parent'),
    @('pytest-core/test_restore_refuses_a_junctio0/target_jct_ok/data/quick_scan', 'pytest-core/test_restore_refuses_a_junctio0/elsewhere'),
    @('pytest-core/test_prune_skips_damaged_unkno0/mixed/backups/quick_scan/linked_dir', 'pytest-core/test_prune_skips_damaged_unkno0/linked_elsewhere'),
    @('pytest-core/test_restore_of_a_link_inside_0/target_src_link_ok/backups/quick_scan/src_link_ok', 'pytest-core/test_restore_of_a_link_inside_0/target_src_link_ok/backups/quick_scan/real_elsewhere')
)
foreach ($swrPair in $swrTestPairs) {
    $swrLinkPath = [IO.Path]::GetFullPath((Join-Path $swrRun $swrPair[0]))
    $swrTargetPath = [IO.Path]::GetFullPath((Join-Path $swrRun $swrPair[1]))
    foreach ($swrPath in @($swrLinkPath,$swrTargetPath)) {
        if (-not $swrPath.StartsWith($swrRun + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Test link escaped' }
    }
    if (-not (Test-Path -LiteralPath $swrLinkPath)) {
        if (-not @($swrRemoved | Where-Object { $_.link -eq $swrLinkPath -and $_.node_removed -and $_.target_preserved }).Count) { throw 'Test link missing without proof' }
        continue
    }
    $swrNode = Get-Item -LiteralPath $swrLinkPath -Force
    $swrTargets = @($swrNode.Target)
    if ($swrNode.LinkType -ne 'Junction' -or $swrTargets.Count -ne 1 -or [IO.Path]::GetFullPath($swrTargets[0]) -ne $swrTargetPath) { throw 'Test junction changed' }
    $swrTargetNode = Get-Item -LiteralPath $swrTargetPath -Force
    if (($swrTargetNode.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrTargetNode.LinkType) { throw 'Test target linked' }
    $swrBeforeCount = @(Get-ChildItem -LiteralPath $swrTargetPath -Force).Count
    [IO.Directory]::Delete($swrLinkPath, $false)
    if ((Test-Path -LiteralPath $swrLinkPath) -or -not (Test-Path -LiteralPath $swrTargetPath) -or @(Get-ChildItem -LiteralPath $swrTargetPath -Force).Count -ne $swrBeforeCount) { throw 'Test target changed on unlink' }
    $swrRemoved += [pscustomobject]@{kind='worker_test_fixture';link=$swrLinkPath;target=$swrTargetPath;node_removed=$true;target_preserved=$true;target_immediate_children=$swrBeforeCount}
}
[ordered]@{schema='swr_junction_unlink/1';created_at=[DateTime]::UtcNow.ToString('o');process_matches=0;listener_matches=0;links=$swrRemoved} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $swrReceiptPath -Encoding utf8
$swrQueue = [Collections.Generic.Queue[string]]::new()
$swrQueue.Enqueue($swrRun)
$swrFiles = @()
$swrDirectories = @()
while ($swrQueue.Count) {
    $swrDirectory = $swrQueue.Dequeue()
    $swrNode = Get-Item -LiteralPath $swrDirectory -Force
    if (($swrNode.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrNode.LinkType) { throw 'Directory reparse refused before traversal' }
    foreach ($swrChild in @(Get-ChildItem -LiteralPath $swrDirectory -Force)) {
        $swrFull = [IO.Path]::GetFullPath($swrChild.FullName)
        if (-not $swrFull.StartsWith($swrRun + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or ($swrChild.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrChild.LinkType) { throw 'Unsafe child' }
        $swrRelative = $swrFull.Substring($swrRun.Length + 1).Replace('\','/')
        if ($swrChild.PSIsContainer) { $swrDirectories += $swrRelative; $swrQueue.Enqueue($swrFull) }
        else { $swrFiles += [pscustomobject]@{path=$swrRelative;bytes=$swrChild.Length;sha256=(Get-FileHash -LiteralPath $swrFull -Algorithm SHA256).Hash.ToLowerInvariant()} }
    }
}
[ordered]@{schema='swr_owned_cleanup_baseline/1';created_at=[DateTime]::UtcNow.ToString('o');absolute_root=$swrRun;process_matches=0;listener_matches=0;known_sessions_exited=@('2953','66093','78000');junction_nodes_unlinked=$swrRemoved.Count;files=@($swrFiles | Sort-Object path);directories=@($swrDirectories | Sort-Object)} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $swrEvidence 'cleanup-baseline.json') -Encoding utf8
Write-Output ('junction_nodes_unlinked=' + $swrRemoved.Count + ' owned_files=' + $swrFiles.Count + ' process_matches=0 listener_matches=0')
