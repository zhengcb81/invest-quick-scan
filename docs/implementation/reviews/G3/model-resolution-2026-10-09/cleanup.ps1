param([switch]$Apply)
$ErrorActionPreference='Stop'
$mrRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$mrRoot=[IO.Path]::GetFullPath((Join-Path $mrRepo 'runs/model-resolution-2026-10-09-01'))
$mrOut=Join-Path $mrRepo 'docs/implementation/intake/G3/2026-10-09-model-resolution'
$mrManifestPath=Join-Path $mrOut 'cleanup-baseline.json'
$mrManifest=Get-Content -LiteralPath $mrManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$mrProof=Get-Content -LiteralPath (Join-Path $mrOut 'cleanup-lstat.json') -Raw -Encoding utf8 | ConvertFrom-Json
$mrResult=Get-Content -LiteralPath (Join-Path $mrOut 'verification/final-verification.json') -Raw -Encoding utf8 | ConvertFrom-Json
$mrHash=(Get-FileHash -LiteralPath $mrManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $mrRoot.StartsWith((Join-Path $mrRepo 'runs')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($mrManifest.absolute_root) -ne $mrRoot -or [IO.Path]::GetFullPath($mrProof.root) -ne $mrRoot) { throw 'Wrong exact cleanup root' }
if ($mrProof.baseline_sha256 -ne $mrHash -or $mrProof.files_verified -ne $mrManifest.files.Count -or $mrProof.directories_verified -ne $mrManifest.directories.Count -or $mrProof.hardlinks -ne 0 -or $mrProof.reparse_points -ne 0) { throw 'Incomplete lstat proof' }
if ($mrResult.authorized_changed_files -le 0 -or $mrResult.original_source_unchanged_files -le 0 -or $mrResult.compared_source_files -lt 137 -or -not $mrResult.original_untracked_preserved -or -not $mrResult.exact_final_raw_files_match -or $mrResult.final_regression_exit -ne 0 -or $mrResult.external_http -ne 0 -or $mrResult.paid_calls -ne 0 -or $mrResult.production_db_written) { throw 'Final source/test proof incomplete' }
$mrActive=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.ProcessId -ne $PID -and ($_.CommandLine -like '*model-resolution-2026-10-09-01*' -or
    ($_.Name -like 'python*' -and $_.CommandLine -like '*G3*model-resolution-2026-10-09*'))
})
if ($mrActive.Count) { throw 'Owned runner still active' }
$mrQueue=[Collections.Generic.Queue[string]]::new()
$mrQueue.Enqueue($mrRoot)
$mrFiles=@()
$mrDirs=@()
while ($mrQueue.Count) {
    $mrDirectory=$mrQueue.Dequeue()
    $mrItem=Get-Item -LiteralPath $mrDirectory -Force
    if (($mrItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $mrItem.LinkType) { throw 'Reparse before traversal' }
    foreach ($mrChild in @(Get-ChildItem -LiteralPath $mrDirectory -Force)) {
        $mrFull=[IO.Path]::GetFullPath($mrChild.FullName)
        if (-not $mrFull.StartsWith($mrRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or ($mrChild.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $mrChild.LinkType) { throw 'Unsafe child' }
        $mrRelative=$mrFull.Substring($mrRoot.Length+1).Replace('\','/')
        if ($mrChild.PSIsContainer) { $mrDirs += $mrRelative; $mrQueue.Enqueue($mrFull) }
        else { $mrFiles += $mrRelative }
    }
}
if ($mrFiles.Count -ne $mrManifest.files.Count -or @(Compare-Object @($mrFiles | Sort-Object) @($mrManifest.files.path | Sort-Object)).Count) { throw 'File set drift' }
if ($mrDirs.Count -ne $mrManifest.directories.Count -or @(Compare-Object @($mrDirs | Sort-Object) @($mrManifest.directories | Sort-Object)).Count) { throw 'Directory set drift' }
foreach ($mrFile in $mrManifest.files) {
    $mrPath=[IO.Path]::GetFullPath((Join-Path $mrRoot $mrFile.path))
    if (-not $mrPath.StartsWith($mrRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest escaped' }
    $mrItem=Get-Item -LiteralPath $mrPath -Force
    if ($mrItem.Length -ne $mrFile.bytes -or (Get-FileHash -LiteralPath $mrPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $mrFile.sha256) { throw 'Byte drift' }
}
$mrReceipt=[ordered]@{schema='mr_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;root=$mrRoot;baseline_sha256=$mrHash;files_verified=$mrManifest.files.Count;directories_verified=$mrManifest.directories.Count;process_matches=0;hardlinks=0;reparse_points=0;owned_listener_ports=@();scope='Only the exact model resolution private root; no shared TEMP, Phase92, unknown untracked or other repository deletion';listener_note='No server/listener created; guarded asyncio socketpairs only; no matching runner remains'}
$mrReceiptPath=Join-Path $mrOut $(if ($Apply) {'cleanup-receipt.json'} else {'cleanup-dry-run.json'})
if (Test-Path -LiteralPath $mrReceiptPath) { throw 'Receipt already exists; do not overwrite' }
if (-not $Apply) {
    $mrReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $mrReceiptPath -Encoding utf8
    Write-Output ('dry_run verified_files='+$mrManifest.files.Count)
    exit 0
}
foreach ($mrFile in $mrManifest.files) {
    $mrPath=[IO.Path]::GetFullPath((Join-Path $mrRoot $mrFile.path))
    $mrItem=Get-Item -LiteralPath $mrPath -Force
    if (($mrItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $mrItem.LinkType -or $mrItem.Length -ne $mrFile.bytes -or (Get-FileHash -LiteralPath $mrPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $mrFile.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $mrPath -Force
}
foreach ($mrRelative in @($mrManifest.directories | Sort-Object Length -Descending)) {
    $mrPath=[IO.Path]::GetFullPath((Join-Path $mrRoot $mrRelative))
    if (-not $mrPath.StartsWith($mrRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Directory escaped' }
    $mrItem=Get-Item -LiteralPath $mrPath -Force
    if (($mrItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $mrItem.LinkType -or @(Get-ChildItem -LiteralPath $mrPath -Force).Count) { throw 'Changed/nonempty directory' }
    [IO.Directory]::Delete($mrPath,$false)
}
if (@(Get-ChildItem -LiteralPath $mrRoot -Force).Count) { throw 'Root nonempty' }
[IO.Directory]::Delete($mrRoot,$false)
$mrReceipt.applied=$true
$mrReceipt['files_deleted']=$mrManifest.files.Count
$mrReceipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$mrReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $mrReceiptPath -Encoding utf8
Write-Output ('deleted_owned_files='+$mrManifest.files.Count)
