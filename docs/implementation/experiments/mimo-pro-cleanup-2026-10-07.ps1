param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$pilotRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$pilotNames = @('mimo-pro-pilot-2026-10-07-01','mimo-pro-pilot-2026-10-07-thinking-all','mimo-pro-pilot-2026-10-07-jsonoff')
$pilotRunsPrefix = [IO.Path]::GetFullPath((Join-Path $pilotRoot 'runs')) + [IO.Path]::DirectorySeparatorChar
$pilotArchivePrefix = Join-Path $pilotRoot 'docs/implementation/experiments/artifacts'
$pilotReviewPrefix = Join-Path $pilotRoot 'docs/implementation/reviews/B01'
foreach ($pilotReport in @('mimo-pilot-primary-source-support-2026-10-07.json','mimo-pilot-extension-source-support-2026-10-07.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $pilotReviewPrefix $pilotReport))) { throw 'Source audit not finished; keep source context.' }
    $pilotAudit = Get-Content -LiteralPath (Join-Path $pilotReviewPrefix $pilotReport) -Encoding UTF8 -Raw | ConvertFrom-Json
    $pilotExpected = if ($pilotReport -like '*primary*') { 196 } else { 130 }
    if ($pilotAudit.summary.complete -eq $false -or $pilotAudit.judgments.Count -ne $pilotExpected -or @($pilotAudit.judgments.review_id | Select-Object -Unique).Count -ne $pilotExpected) { throw 'Source audit not signed complete.' }
}
# Inspect only our named Python runners. Command lines are never printed/saved.
$pilotProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -match '^(python|pythonw)(\.exe)?$' -and (
      $_.CommandLine -like '*mimo_pro_pilot.py*' -or $_.CommandLine -like '*mimo_pilot_extension.py*' -or $_.CommandLine -like '*mimo_json_mode_probe.py*')
})
if ($pilotProcesses.Count -ne 0) { throw 'An owned runner may still be running; no deletion.' }
$pilotRecords = @()
foreach ($pilotName in $pilotNames) {
    $pilotRun = [IO.Path]::GetFullPath((Join-Path $pilotRoot ('runs/' + $pilotName)))
    if (-not $pilotRun.StartsWith($pilotRunsPrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Resolved root escaped runs.' }
    $pilotArchive = Join-Path $pilotArchivePrefix $pilotName
    $pilotManifest = Get-Content -LiteralPath (Join-Path $pilotArchive 'archive-manifest.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    if ([IO.Path]::GetFullPath($pilotManifest.run_path) -ne $pilotRun -or $pilotManifest.budget.unresolved_attempts -ne 0) { throw 'Wrong owner or unresolved requests.' }
    foreach ($pilotProperty in $pilotManifest.retained_files.psobject.Properties) {
        $pilotArchiveFile = [IO.Path]::GetFullPath((Join-Path $pilotArchive $pilotProperty.Name))
        if (-not $pilotArchiveFile.StartsWith($pilotArchive + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Archive file escaped.' }
        if ((Get-FileHash -LiteralPath $pilotArchiveFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pilotProperty.Value) { throw 'Archive hash mismatch.' }
    }
    if (Test-Path -LiteralPath (Join-Path $pilotRun 'orchestrator.lock')) { throw 'Owned lock still present.' }
    $pilotItems = @(Get-ChildItem -LiteralPath $pilotRun -Recurse -Force)
    foreach ($pilotItem in @((Get-Item -LiteralPath $pilotRun)) + $pilotItems) {
        if (($pilotItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point refused.' }
        if ($pilotItem.PSObject.Properties['LinkType'] -and $pilotItem.LinkType) { throw 'Link refused.' }
        $pilotAbsolute = [IO.Path]::GetFullPath($pilotItem.FullName)
        if ($pilotAbsolute -ne $pilotRun -and -not $pilotAbsolute.StartsWith($pilotRun + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Owned path escaped.' }
    }
    foreach ($pilotFile in $pilotItems | Where-Object { -not $_.PSIsContainer }) {
        $pilotRecords += [pscustomobject]@{run=$pilotName;path=$pilotFile.FullName;size=$pilotFile.Length;sha256=(Get-FileHash -LiteralPath $pilotFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    }
}
$pilotReceiptPath = Join-Path $pilotReviewPrefix 'mimo-pro-cleanup-receipt-2026-10-07.json'
$pilotReceipt = [ordered]@{schema='owned_pilot_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');roots=$pilotNames;process_scan='strict CIM of named Python runners, 0 matches; known tool sessions exited';scope='Only these three exact IQS roots; Phase92/shared TEMP/other repositories untouched';files=$pilotRecords;deleted=$false}
$pilotReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $pilotReceiptPath -Encoding utf8
if (-not $Apply) { Write-Output ('verified_files=' + $pilotRecords.Count + '; dry_run'); exit 0 }
foreach ($pilotRecord in $pilotRecords) {
    if ((Get-FileHash -LiteralPath $pilotRecord.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pilotRecord.sha256) { throw 'File changed since preflight; stopped.' }
    Remove-Item -LiteralPath $pilotRecord.path -Force
}
foreach ($pilotName in $pilotNames) {
    $pilotRun = [IO.Path]::GetFullPath((Join-Path $pilotRoot ('runs/' + $pilotName)))
    foreach ($pilotDirectory in @(Get-ChildItem -LiteralPath $pilotRun -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)) {
        if (@(Get-ChildItem -LiteralPath $pilotDirectory.FullName -Force).Count) { throw 'Nonempty owned directory; stopped.' }
        Remove-Item -LiteralPath $pilotDirectory.FullName -Force
    }
    if (@(Get-ChildItem -LiteralPath $pilotRun -Force).Count) { throw 'New unregistered files appeared; stopped.' }
    Remove-Item -LiteralPath $pilotRun -Force
    if (Test-Path -LiteralPath $pilotRun) { throw 'Owned root survived.' }
}
$pilotReceipt.deleted=$true
$pilotReceipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$pilotReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $pilotReceiptPath -Encoding utf8
Write-Output ('deleted_owned_files=' + $pilotRecords.Count)
