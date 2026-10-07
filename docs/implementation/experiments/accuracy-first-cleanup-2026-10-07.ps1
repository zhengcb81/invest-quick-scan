param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$iqsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$archiveRoot = Join-Path $iqsRoot 'docs/implementation/experiments/artifacts/accuracy-first-2026-10-07'
$runPrefix = [IO.Path]::GetFullPath((Join-Path $iqsRoot 'runs')) + [IO.Path]::DirectorySeparatorChar
$roots = [ordered]@{main='accuracy-pilot-2026-10-07-01';followup='accuracy-pilot-followup-2026-10-07-01';diagnostic='accuracy-pilot-zai-diagnostic-2026-10-07-01';validation='accuracy-validation-2026-10-07-01'}
$index = Get-Content -LiteralPath (Join-Path $archiveRoot 'index.json') -Encoding UTF8 -Raw | ConvertFrom-Json
foreach ($property in $index.files.psobject.Properties) {
    $target = [IO.Path]::GetFullPath((Join-Path $archiveRoot $property.Name))
    if (-not $target.StartsWith($archiveRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Archive escape' }
    $item = Get-Item -LiteralPath $target
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.LinkType) { throw 'Archive link' }
    if ($item.Length -ne $property.Value.size -or (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value.sha256) { throw 'Archive hash drift' }
}
$disposition = Get-Content -LiteralPath (Join-Path $archiveRoot 'unknown-disposition.json') -Encoding UTF8 -Raw | ConvertFrom-Json
if ($disposition.attempt_id -ne 'ATT_0668931b18ec49be99137252163a00c2' -or $disposition.state -ne 'outcome_unknown' -or $disposition.reserve_usd -ne 0.03 -or $disposition.budget_released -ne $false -or $disposition.send_repeated -ne $false) { throw 'Unknown budget not preserved' }
# Fail closed if process enumeration is unavailable. Never print/save other processes' argv.
$processes = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -match '^(python|pythonw)(\.exe)?$' -and (
        $_.CommandLine -match 'accuracy_(pilot|followup|report)\.py|zai_route_diagnostic\.py|accuracy-archive-2026-10-07\.py' -or
        $_.CommandLine -match 'refinement(-resume)?\.py|precision-search\.py|additional-models\.py' -or
        $_.CommandLine -match 'accuracy-pilot(-followup|-zai-diagnostic)?-2026-10-07-01|accuracy-validation-2026-10-07-01')
})
if ($processes.Count) { throw 'An owned runner is active' }
$records = @()
foreach ($label in $roots.Keys) {
    $run = [IO.Path]::GetFullPath((Join-Path $iqsRoot ('runs/' + $roots[$label])))
    if (-not $run.StartsWith($runPrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Root escape' }
    $manifest = Get-Content -LiteralPath (Join-Path $archiveRoot ($label + '/archive-manifest.json')) -Encoding UTF8 -Raw | ConvertFrom-Json
    if ($manifest.run_name -ne $roots[$label] -or [IO.Path]::GetFullPath($manifest.run_path) -ne $run) { throw 'Wrong owned root' }
    $expectedUnknown = if ($label -eq 'followup') { 1 } else { 0 }
    if ($label -ne 'validation' -and $manifest.budget.unresolved_attempts -ne $expectedUnknown) { throw 'Unexpected unknown attempt' }
    if (Test-Path -LiteralPath (Join-Path $run 'orchestrator.lock')) { throw 'Owned lock still present' }
    $items = @(Get-ChildItem -LiteralPath $run -Recurse -Force)
    foreach ($item in @((Get-Item -LiteralPath $run)) + $items) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.LinkType) { throw 'Owned link/reparse refused' }
        $absolute = [IO.Path]::GetFullPath($item.FullName)
        if ($absolute -ne $run -and -not $absolute.StartsWith($run + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Owned child escape' }
    }
    $files = @($items | Where-Object { -not $_.PSIsContainer })
    if ($files.Count -ne @($manifest.cleanup_baseline.psobject.Properties).Count) { throw 'File set changed after archival' }
    foreach ($property in $manifest.cleanup_baseline.psobject.Properties) {
        $path = [IO.Path]::GetFullPath((Join-Path $run $property.Name))
        if (-not $path.StartsWith($run + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Baseline escape' }
        $item = Get-Item -LiteralPath $path
        $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($item.Length -ne $property.Value.size -or $hash -ne $property.Value.sha256) { throw 'Baseline file changed' }
        $records += [pscustomobject]@{root=$roots[$label];path=$path;size=$item.Length;sha256=$hash}
    }
}
$receiptPath = Join-Path $iqsRoot 'docs/implementation/reviews/B01/accuracy-first-cleanup-receipt-2026-10-07.json'
$receipt = [ordered]@{schema='phase96_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;files=$records;roots=$roots;archive_index_sha256=(Get-FileHash -LiteralPath (Join-Path $archiveRoot 'index.json') -Algorithm SHA256).Hash.ToLowerInvariant();process_scan_matches=0;unknown_budget_released=$false;held_attempt=$disposition.attempt_id;scope='Four exact IQS roots only; old Phase92, shared TEMP, other repositories and opencode.json untouched'}
if (-not $Apply) {
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
    Write-Output ('dry_run verified_files=' + $records.Count)
    exit 0
}
foreach ($record in $records) {
    $item = Get-Item -LiteralPath $record.path
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.LinkType -or $item.Length -ne $record.size -or (Get-FileHash -LiteralPath $record.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $record.path -Force
}
foreach ($label in $roots.Keys) {
    $run = [IO.Path]::GetFullPath((Join-Path $iqsRoot ('runs/' + $roots[$label])))
    foreach ($directory in @(Get-ChildItem -LiteralPath $run -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)) {
        if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count) { throw 'Nonempty child' }
        Remove-Item -LiteralPath $directory.FullName -Force
    }
    if (@(Get-ChildItem -LiteralPath $run -Force).Count) { throw 'New unregistered file' }
    Remove-Item -LiteralPath $run -Force
}
$receipt.applied=$true
$receipt['files_deleted']=$records.Count
$receipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output ('deleted_owned_files=' + $records.Count + '; unknown_budget_still_held')
