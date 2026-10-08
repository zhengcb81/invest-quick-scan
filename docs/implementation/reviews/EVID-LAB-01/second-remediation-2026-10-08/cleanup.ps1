param([switch]$Apply)
$ErrorActionPreference='Stop'
$elRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$elRoot=[IO.Path]::GetFullPath((Join-Path $elRepo 'runs/evid-lab-second-remediation-2026-10-08-01'))
$elEvidence=Join-Path $elRepo 'docs/implementation/intake/EVID-LAB-01/2026-10-08-second-remediation'
$elBaselinePath=Join-Path $elEvidence 'cleanup-baseline.json'
$elManifest=Get-Content -LiteralPath $elBaselinePath -Raw -Encoding utf8 | ConvertFrom-Json
$elProof=Get-Content -LiteralPath (Join-Path $elEvidence 'cleanup-lstat.json') -Raw -Encoding utf8 | ConvertFrom-Json
$elResult=Get-Content -LiteralPath (Join-Path $elEvidence 'verification/result.json') -Raw -Encoding utf8 | ConvertFrom-Json
$elHash=(Get-FileHash -LiteralPath $elBaselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $elRoot.StartsWith((Join-Path $elRepo 'runs')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($elManifest.absolute_root) -ne $elRoot -or [IO.Path]::GetFullPath($elProof.root) -ne $elRoot) { throw 'Wrong cleanup root' }
if ($elProof.baseline_sha256 -ne $elHash -or $elProof.files_verified -ne $elManifest.files.Count -or $elProof.hardlinks -ne 0 -or $elProof.reparse_points -ne 0) { throw 'Missing lstat proof' }
if (-not $elResult.input_bytes_unchanged -or $elResult.snapshot_changed_after_all_cases.Count -ne 0 -or $elResult.worker_repository_written -or $elResult.paid_calls -ne 0) { throw 'Acceptance proof incomplete' }
$elProcesses=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.ProcessId -ne $PID -and ($_.CommandLine -like '*evid-lab-second-remediation-2026-10-08-01*' -or
    ($_.CommandLine -like '*EVID-LAB-01*second-remediation-2026-10-08*' -and ($_.CommandLine -like '*run.py*' -or $_.CommandLine -like '*run_archive_binding.py*' -or $_.CommandLine -like '*collect.py*')))
})
if ($elProcesses.Count) { throw 'Private runner still active' }
$elQueue=[Collections.Generic.Queue[string]]::new()
$elQueue.Enqueue($elRoot)
$elFiles=@()
$elDirs=@()
while ($elQueue.Count) {
    $elDirectory=$elQueue.Dequeue()
    $elItem=Get-Item -LiteralPath $elDirectory -Force
    if (($elItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $elItem.LinkType) { throw 'Reparse before traversal' }
    foreach ($elChild in @(Get-ChildItem -LiteralPath $elDirectory -Force)) {
        $elFull=[IO.Path]::GetFullPath($elChild.FullName)
        if (-not $elFull.StartsWith($elRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or ($elChild.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $elChild.LinkType) { throw 'Unsafe child' }
        $elRelative=$elFull.Substring($elRoot.Length+1).Replace('\','/')
        if ($elChild.PSIsContainer) { $elDirs += $elRelative; $elQueue.Enqueue($elFull) }
        else { $elFiles += $elRelative }
    }
}
if ($elFiles.Count -ne $elManifest.files.Count -or @(Compare-Object @($elFiles | Sort-Object) @($elManifest.files.path | Sort-Object)).Count) { throw 'File set drift' }
if ($elDirs.Count -ne $elManifest.directories.Count -or @(Compare-Object @($elDirs | Sort-Object) @($elManifest.directories | Sort-Object)).Count) { throw 'Directory set drift' }
foreach ($elFile in $elManifest.files) {
    $elPath=[IO.Path]::GetFullPath((Join-Path $elRoot $elFile.path))
    if (-not $elPath.StartsWith($elRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest escaped' }
    $elItem=Get-Item -LiteralPath $elPath -Force
    if ($elItem.Length -ne $elFile.bytes -or (Get-FileHash -LiteralPath $elPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $elFile.sha256) { throw 'Byte drift' }
}
$elReceipt=[ordered]@{schema='e102_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;root=$elRoot;baseline_sha256=$elHash;files_verified=$elManifest.files.Count;process_matches=0;hardlinks=0;reparse_points=0;known_sessions_exited=$elManifest.known_session_exits;scope='Only exact IQS second remediation test root; original Lab, Phase92, shared TEMP and opencode.json untouched'}
$elReceiptPath=Join-Path $elEvidence 'cleanup-receipt.json'
if (-not $Apply) {
    $elReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $elReceiptPath -Encoding utf8
    Write-Output ('dry_run verified_files='+$elManifest.files.Count)
    exit 0
}
foreach ($elFile in $elManifest.files) {
    $elPath=[IO.Path]::GetFullPath((Join-Path $elRoot $elFile.path))
    $elItem=Get-Item -LiteralPath $elPath -Force
    if (($elItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $elItem.LinkType -or $elItem.Length -ne $elFile.bytes -or (Get-FileHash -LiteralPath $elPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $elFile.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $elPath -Force
}
foreach ($elRelative in @($elManifest.directories | Sort-Object Length -Descending)) {
    $elPath=[IO.Path]::GetFullPath((Join-Path $elRoot $elRelative))
    if (-not $elPath.StartsWith($elRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Directory escaped' }
    $elItem=Get-Item -LiteralPath $elPath -Force
    if (($elItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $elItem.LinkType -or @(Get-ChildItem -LiteralPath $elPath -Force).Count) { throw 'Changed/nonempty directory' }
    [IO.Directory]::Delete($elPath,$false)
}
if (@(Get-ChildItem -LiteralPath $elRoot -Force).Count) { throw 'Root nonempty' }
[IO.Directory]::Delete($elRoot,$false)
$elReceipt.applied=$true
$elReceipt['files_deleted']=$elManifest.files.Count
$elReceipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$elReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $elReceiptPath -Encoding utf8
Write-Output ('deleted_owned_files='+$elManifest.files.Count)
