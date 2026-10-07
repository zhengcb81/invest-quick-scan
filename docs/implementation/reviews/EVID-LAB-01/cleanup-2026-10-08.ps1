param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$iqsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$run = [IO.Path]::GetFullPath((Join-Path $iqsRoot 'runs/evid-lab-2026-10-08-01'))
$prefix = [IO.Path]::GetFullPath((Join-Path $iqsRoot 'runs')) + [IO.Path]::DirectorySeparatorChar
$evidence = Join-Path $iqsRoot 'docs/implementation/intake/EVID-LAB-01/2026-10-08'
$manifest = Get-Content -LiteralPath (Join-Path $evidence 'cleanup-baseline.json') -Encoding UTF8 -Raw | ConvertFrom-Json
if (-not $run.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($manifest.absolute_root) -ne $run) { throw 'Wrong cleanup root' }
$result = Get-Content -LiteralPath (Join-Path $evidence 'verification/result.json') -Encoding UTF8 -Raw | ConvertFrom-Json
if (-not $result.input_bytes_unchanged -or $result.worker_repository_written -or $result.charged_calls -ne 0) { throw 'Acceptance/readonly proof incomplete' }
# Known synchronous sessions have exited; additionally refuse any named owned Python argv.
$processes = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
    $_.Name -match '^(python|pythonw)(\.exe)?$' -and (
        $_.CommandLine -like '*evid-lab-2026-10-08-01*' -or
        $_.CommandLine -like '*EVID-LAB-01*run_acceptance.py*')
})
if ($processes.Count) { throw 'Owned Python runner active' }
$items = @(Get-ChildItem -LiteralPath $run -Recurse -Force)
foreach ($item in @((Get-Item -LiteralPath $run)) + $items) {
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.LinkType) { throw 'Link/reparse refused' }
    $path = [IO.Path]::GetFullPath($item.FullName)
    if ($path -ne $run -and -not $path.StartsWith($run + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Child escaped' }
}
if (@($items | Where-Object { -not $_.PSIsContainer }).Count -ne $manifest.files.Count) { throw 'Owned file set changed' }
foreach ($file in $manifest.files) {
    $path = [IO.Path]::GetFullPath((Join-Path $run $file.path))
    if (-not $path.StartsWith($run + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path escaped' }
    $item = Get-Item -LiteralPath $path
    if ($item.Length -ne $file.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) { throw 'Preflight byte drift' }
}
$receiptPath = Join-Path $evidence 'cleanup-receipt.json'
$receipt = [ordered]@{schema='e97_owned_cleanup/1';created_at=[DateTime]::UtcNow.ToString('o');applied=$false;root=$run;files_verified=$manifest.files.Count;baseline_sha256=(Get-FileHash -LiteralPath (Join-Path $evidence 'cleanup-baseline.json') -Algorithm SHA256).Hash.ToLowerInvariant();process_matches=0;known_sessions_exited=$manifest.known_sessions_exited;scope='Single exact IQS test root; original Lab, Phase92, shared TEMP and opencode.json untouched'}
if (-not $Apply) {
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
    Write-Output ('dry_run verified_files=' + $manifest.files.Count)
    exit 0
}
foreach ($file in $manifest.files) {
    $path = [IO.Path]::GetFullPath((Join-Path $run $file.path))
    $item = Get-Item -LiteralPath $path
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.LinkType -or $item.Length -ne $file.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) { throw 'Pre-delete drift' }
    Remove-Item -LiteralPath $path -Force
}
foreach ($directory in @(Get-ChildItem -LiteralPath $run -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)) {
    if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count) { throw 'Nonempty owned directory' }
    Remove-Item -LiteralPath $directory.FullName -Force
}
if (@(Get-ChildItem -LiteralPath $run -Force).Count) { throw 'Unregistered file appeared' }
Remove-Item -LiteralPath $run -Force
$receipt.applied=$true
$receipt['files_deleted']=$manifest.files.Count
$receipt['completed_at']=[DateTime]::UtcNow.ToString('o')
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output ('deleted_owned_files=' + $manifest.files.Count)
