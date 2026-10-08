param([switch]$Apply)
$ErrorActionPreference='Stop'
$jr2Repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$jr2Root=[IO.Path]::GetFullPath((Join-Path $jr2Repo 'runs/jr2-2026-10-08-01'))
$jr2Out=Join-Path $jr2Repo 'docs/implementation/intake/G3/2026-10-08-jr2'
$jr2ManifestPath=Join-Path $jr2Out 'cleanup-baseline.json'
$jr2Manifest=Get-Content -LiteralPath $jr2ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$jr2Proof=Get-Content -LiteralPath (Join-Path $jr2Out 'cleanup-lstat.json') -Raw -Encoding utf8 | ConvertFrom-Json
$jr2Result=Get-Content -LiteralPath (Join-Path $jr2Out 'verification/final-verification.json') -Raw -Encoding utf8 | ConvertFrom-Json
$jr2Hash=(Get-FileHash -LiteralPath $jr2ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $jr2Root.StartsWith((Join-Path $jr2Repo 'runs')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($jr2Manifest.absolute_root) -ne $jr2Root -or [IO.Path]::GetFullPath($jr2Proof.root) -ne $jr2Root) { throw 'Wrong exact cleanup root' }
if ($jr2Proof.baseline_sha256 -ne $jr2Hash -or $jr2Proof.files_verified -ne $jr2Manifest.files.Count -or $jr2Proof.directories_verified -ne $jr2Manifest.directories.Count -or $jr2Proof.hardlinks -ne 0 -or $jr2Proof.reparse_points -ne 0) { throw 'Incomplete lstat proof' }
if ($jr2Result.authorized_changed_files -ne 7 -or $jr2Result.original_source_unchanged_files -ne 129 -or $jr2Result.compared_source_files -ne 136 -or -not $jr2Result.original_untracked_preserved -or -not $jr2Result.exact_final_raw_files_match -or $jr2Result.final_regression_exit -ne 0 -or $jr2Result.external_http -ne 0 -or $jr2Result.paid_calls -ne 0 -or $jr2Result.production_db_written) { throw 'Final source/test proof incomplete' }
$jr2Active=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.ProcessId -ne $PID -and ($_.CommandLine -like '*jr2-2026-10-08-01*' -or
    ($_.Name -like 'python*' -and $_.CommandLine -like '*G3*jr2-2026-10-08*'))
})
if ($jr2Active.Count) { throw 'Owned runner still active' }
$jr2Queue=[Collections.Generic.Queue[string]]::new()
$jr2Queue.Enqueue($jr2Root)
$jr2Files=@()
$jr2Dirs=@()
while ($jr2Queue.Count) {
    $jr2Directory=$jr2Queue.Dequeue()
    $jr2Item=Get-Item -LiteralPath $jr2Directory -Force
    if (($jr2Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $jr2Item.LinkType) { throw 'Reparse before traversal' }
    foreach ($jr2Child in @(Get-ChildItem -LiteralPath $jr2Directory -Force)) {
        $jr2Full=[IO.Path]::GetFullPath($jr2Child.FullName)
        if (-not $jr2Full.StartsWith($jr2Root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or ($jr2Child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $jr2Child.LinkType) { throw 'Unsafe child' }
        $jr2Relative=$jr2Full.Substring($jr2Root.Length+1).Replace('\','/')
        if ($jr2Child.PSIsContainer) { $jr2Dirs += $jr2Relative; $jr2Queue.Enqueue($jr2Full) }
        else { $jr2Files += $jr2Relative }
    }
}
if ($jr2Files.Count -ne $jr2Manifest.files.Count -or @(Compare-Object @($jr2Files | Sort-Object) @($jr2Manifest.files.path | Sort-Object)).Count) { throw 'File set drift' }
if ($jr2Dirs.Count -ne $jr2Manifest.directories.Count -or @(Compare-Object @($jr2Dirs | Sort-Object) @($jr2Manifest.directories | Sort-Object)).Count) { throw 'Directory set drift' }
foreach ($jr2File in $jr2Manifest.files) {
    $jr2Path=[IO.Path]::GetFullPath((Join-Path $jr2Root $jr2File.path))
    if (-not $jr2Path.StartsWith($jr2Root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest escaped' }
    $jr2Item=Get-Item -LiteralPath $jr2Path -Force
    if ($jr2Item.Length -ne $jr2File.bytes -or (Get-FileHash -LiteralPath $jr2Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $jr2File.sha256) { throw 'Byte drift' }
}
$jr2Receipt=[ordered]@{schema='jr2_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;root=$jr2Root;baseline_sha256=$jr2Hash;files_verified=$jr2Manifest.files.Count;directories_verified=$jr2Manifest.directories.Count;process_matches=0;hardlinks=0;reparse_points=0;known_sessions_exited=$jr2Manifest.known_session_exits;owned_listener_ports=@();scope='Only the exact JR2 private root; no shared TEMP, Phase92, unknown untracked or other repository deletion';listener_note='No server/listener created; guarded asyncio socketpairs only; no matching runner remains'}
$jr2ReceiptPath=Join-Path $jr2Out $(if ($Apply) {'cleanup-receipt.json'} else {'cleanup-dry-run.json'})
if (Test-Path -LiteralPath $jr2ReceiptPath) { throw 'Receipt already exists; do not overwrite' }
if (-not $Apply) {
    $jr2Receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jr2ReceiptPath -Encoding utf8
    Write-Output ('dry_run verified_files='+$jr2Manifest.files.Count)
    exit 0
}
foreach ($jr2File in $jr2Manifest.files) {
    $jr2Path=[IO.Path]::GetFullPath((Join-Path $jr2Root $jr2File.path))
    $jr2Item=Get-Item -LiteralPath $jr2Path -Force
    if (($jr2Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $jr2Item.LinkType -or $jr2Item.Length -ne $jr2File.bytes -or (Get-FileHash -LiteralPath $jr2Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $jr2File.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $jr2Path -Force
}
foreach ($jr2Relative in @($jr2Manifest.directories | Sort-Object Length -Descending)) {
    $jr2Path=[IO.Path]::GetFullPath((Join-Path $jr2Root $jr2Relative))
    if (-not $jr2Path.StartsWith($jr2Root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Directory escaped' }
    $jr2Item=Get-Item -LiteralPath $jr2Path -Force
    if (($jr2Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $jr2Item.LinkType -or @(Get-ChildItem -LiteralPath $jr2Path -Force).Count) { throw 'Changed/nonempty directory' }
    [IO.Directory]::Delete($jr2Path,$false)
}
if (@(Get-ChildItem -LiteralPath $jr2Root -Force).Count) { throw 'Root nonempty' }
[IO.Directory]::Delete($jr2Root,$false)
$jr2Receipt.applied=$true
$jr2Receipt['files_deleted']=$jr2Manifest.files.Count
$jr2Receipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$jr2Receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jr2ReceiptPath -Encoding utf8
Write-Output ('deleted_owned_files='+$jr2Manifest.files.Count)
