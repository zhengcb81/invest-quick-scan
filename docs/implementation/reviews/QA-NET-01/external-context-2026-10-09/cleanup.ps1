param([switch]$Apply)
$ErrorActionPreference='Stop'
$iqsRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$iqsRoot=[IO.Path]::GetFullPath((Join-Path $iqsRepo 'runs/n111a'))
$iqsOut=Join-Path $iqsRepo 'docs/implementation/intake/QA-NET-01/2026-10-09-external-context'
$iqsManifestPath=Join-Path $iqsOut 'cleanup-baseline.json'
$iqsManifest=Get-Content -LiteralPath $iqsManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$iqsProof=Get-Content -LiteralPath (Join-Path $iqsOut 'cleanup-lstat.json') -Raw -Encoding utf8 | ConvertFrom-Json
$iqsResultPath=Join-Path $iqsOut 'publication/result.json'
$iqsResult=Get-Content -LiteralPath $iqsResultPath -Raw -Encoding utf8 | ConvertFrom-Json
$iqsHash=(Get-FileHash -LiteralPath $iqsManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $iqsRoot.StartsWith((Join-Path $iqsRepo 'runs')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($iqsManifest.absolute_root) -ne $iqsRoot -or [IO.Path]::GetFullPath($iqsProof.root) -ne $iqsRoot) { throw 'Wrong exact cleanup root' }
if ($iqsProof.baseline_sha256 -ne $iqsHash -or $iqsProof.files_verified -ne $iqsManifest.files.Count -or $iqsProof.directories_verified -ne $iqsManifest.directories.Count -or $iqsProof.hardlinks -ne 0 -or $iqsProof.reparse_points -ne 0 -or $iqsManifest.files.Count -le 0) { throw 'Incomplete real lstat proof' }
if (-not $iqsResult.source_published -or $iqsResult.approved_paths -ne 38 -or $iqsResult.source_commit -ne $iqsResult.remote_head -or $iqsResult.real_api_requests -ne 0 -or $iqsResult.production_database_changes -ne 0 -or $iqsResult.whole_project_gates_closed -or $iqsManifest.publication_receipt_sha256 -ne (Get-FileHash -LiteralPath $iqsResultPath -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'Publication proof incomplete' }
$iqsActive=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.ProcessId -ne $PID -and ($_.CommandLine -like '*n111a*' -or
        ($_.Name -like 'python*' -and $_.CommandLine -like '*external-context-2026-10-09*'))
})
if ($iqsActive.Count) { throw 'Owned runner/controller still active' }
$iqsQueue=[Collections.Generic.Queue[string]]::new()
$iqsQueue.Enqueue($iqsRoot)
$iqsFiles=[Collections.Generic.List[string]]::new()
$iqsDirs=[Collections.Generic.List[string]]::new()
while ($iqsQueue.Count) {
    $iqsDirectory=$iqsQueue.Dequeue()
    $iqsItem=Get-Item -LiteralPath $iqsDirectory -Force
    if (($iqsItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $iqsItem.LinkType) { throw 'Reparse before traversal' }
    foreach ($iqsChild in @(Get-ChildItem -LiteralPath $iqsDirectory -Force)) {
        $iqsFull=[IO.Path]::GetFullPath($iqsChild.FullName)
        if (-not $iqsFull.StartsWith($iqsRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or ($iqsChild.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $iqsChild.LinkType) { throw 'Unsafe child' }
        $iqsRelative=$iqsFull.Substring($iqsRoot.Length+1).Replace('\','/')
        if ($iqsChild.PSIsContainer) { $iqsDirs.Add($iqsRelative); $iqsQueue.Enqueue($iqsFull) }
        else { $iqsFiles.Add($iqsRelative) }
    }
}
if ($iqsFiles.Count -ne $iqsManifest.files.Count -or @(Compare-Object @($iqsFiles | Sort-Object) @($iqsManifest.files.path | Sort-Object)).Count) { throw 'File set drift' }
if ($iqsDirs.Count -ne $iqsManifest.directories.Count -or @(Compare-Object @($iqsDirs | Sort-Object) @($iqsManifest.directories | Sort-Object)).Count) { throw 'Directory set drift' }
$iqsVerified=0
foreach ($iqsFile in $iqsManifest.files) {
    $iqsPath=[IO.Path]::GetFullPath((Join-Path $iqsRoot $iqsFile.path))
    if (-not $iqsPath.StartsWith($iqsRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $iqsFile.actual_lstat_nlink -ne 1) { throw 'Manifest escaped or link proof missing' }
    $iqsItem=Get-Item -LiteralPath $iqsPath -Force
    if ($iqsItem.Length -ne $iqsFile.bytes -or (Get-FileHash -LiteralPath $iqsPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $iqsFile.sha256) { throw 'Byte drift' }
    $iqsVerified++
    if ($iqsVerified % 5000 -eq 0) { Write-Output ('verified_owned_files='+$iqsVerified) }
}
$iqsReceipt=[ordered]@{schema='phase111_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;root=$iqsRoot;baseline_sha256=$iqsHash;files_verified=$iqsManifest.files.Count;directories_verified=$iqsManifest.directories.Count;process_matches=0;hardlinks=0;reparse_points=0;source_commit=$iqsResult.source_commit;scope='Only exact IQS runs/n111a; no shared TEMP, unknown untracked, production data or foreign repository deletion';no_listener_created=$true}
$iqsReceiptPath=Join-Path $iqsOut $(if ($Apply) {'cleanup-receipt.json'} else {'cleanup-dry-run.json'})
if (Test-Path -LiteralPath $iqsReceiptPath) { throw 'Receipt already exists; do not overwrite' }
if (-not $Apply) {
    $iqsReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $iqsReceiptPath -Encoding utf8
    Write-Output ('dry_run_verified_files='+$iqsManifest.files.Count)
    exit 0
}
$iqsDry=Get-Content -LiteralPath (Join-Path $iqsOut 'cleanup-dry-run.json') -Raw -Encoding utf8 | ConvertFrom-Json
if ($iqsDry.baseline_sha256 -ne $iqsHash -or $iqsDry.applied -or $iqsDry.process_matches -ne 0) { throw 'Matching completed dry-run required' }
$iqsDeleted=0
foreach ($iqsFile in $iqsManifest.files) {
    $iqsPath=[IO.Path]::GetFullPath((Join-Path $iqsRoot $iqsFile.path))
    $iqsItem=Get-Item -LiteralPath $iqsPath -Force
    if (($iqsItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $iqsItem.LinkType -or $iqsItem.Length -ne $iqsFile.bytes -or (Get-FileHash -LiteralPath $iqsPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $iqsFile.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $iqsPath -Force
    $iqsDeleted++
    if ($iqsDeleted % 5000 -eq 0) { Write-Output ('deleted_owned_files='+$iqsDeleted) }
}
foreach ($iqsRelative in @($iqsManifest.directories | Sort-Object Length -Descending)) {
    $iqsPath=[IO.Path]::GetFullPath((Join-Path $iqsRoot $iqsRelative))
    if (-not $iqsPath.StartsWith($iqsRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Directory escaped' }
    $iqsItem=Get-Item -LiteralPath $iqsPath -Force
    if (($iqsItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $iqsItem.LinkType -or @(Get-ChildItem -LiteralPath $iqsPath -Force).Count) { throw 'Changed/nonempty directory' }
    [IO.Directory]::Delete($iqsPath,$false)
}
if (@(Get-ChildItem -LiteralPath $iqsRoot -Force).Count) { throw 'Root nonempty' }
[IO.Directory]::Delete($iqsRoot,$false)
$iqsReceipt.applied=$true
$iqsReceipt['files_deleted']=$iqsDeleted
$iqsReceipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$iqsReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $iqsReceiptPath -Encoding utf8
Write-Output ('deleted_owned_files='+$iqsDeleted)
