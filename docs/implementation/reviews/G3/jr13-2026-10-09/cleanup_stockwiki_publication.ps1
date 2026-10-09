param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$iqs = 'C:\Users\郑曾波\Projects\invest-quick-scan'
$sw = 'C:\Users\郑曾波\Projects\StockWiki'
$out = Join-Path $iqs 'docs\implementation\intake\G3\2026-10-09-jr13\stockwiki-publication'
$expectedRoot = Join-Path $iqs 'runs\s13p'
$inventoryPath = Join-Path $out 'cleanup-inventory.json'
$inv = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
$root = (Resolve-Path -LiteralPath $expectedRoot).ProviderPath
if ($root -cne $expectedRoot -or $inv.exact_root -cne $root) { throw 'Exact owned-root boundary mismatch' }
if ((Split-Path -Parent $root) -cne (Join-Path $iqs 'runs')) { throw 'Wrong owned parent' }
$active = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
if ($active.Count -ne 0) { throw 'Owned-root process is still active' }
$rootItem = Get-Item -LiteralPath $root -Force
if ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse root' }
$all = @(Get-ChildItem -LiteralPath $root -Force -Recurse)
if (@($all | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Reparse descendant' }
if (@($all | Where-Object { $_.LinkType }).Count) { throw 'Linked descendant' }
$actualFiles = @($all | Where-Object { -not $_.PSIsContainer })
$actualDirs = @($all | Where-Object { $_.PSIsContainer })
if ($actualFiles.Count -ne $inv.file_count -or $actualDirs.Count -ne $inv.directory_count) { throw 'Owned inventory changed' }
foreach ($f in $inv.files) {
    $path = [IO.Path]::GetFullPath((Join-Path $root $f.path))
    if (-not $path.StartsWith($root + '\', [StringComparison]::Ordinal)) { throw 'File escaped owned root' }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or $item.Length -ne $f.size -or $f.nlink -ne 1) { throw 'File metadata changed' }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $f.sha256) { throw 'File bytes changed' }
}
foreach ($group in @($inv.source_execution_sha256, $inv.protected_nonsecret_source_sha256)) {
    foreach ($p in $group.PSObject.Properties) {
        if ((Get-FileHash -LiteralPath (Join-Path $sw $p.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.Value) { throw 'Source bytes changed' }
    }
}
$receipt = [ordered]@{ schema='owned-publication-cleanup/1'; mode='dry'; exact_root=$root; inventory_sha256=(Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant(); file_count=$actualFiles.Count; directory_count=$actualDirs.Count; matched_active_processes=0; real_lstat_inventory=$inv.real_os_lstat; protected_source_files=331; shared_or_source_paths_deleted=$false }
if ($Apply) {
    $receipt.mode = 'apply'
    if (Test-Path -LiteralPath (Join-Path $out 'cleanup-receipt.json')) { throw 'Cleanup already applied' }
    foreach ($f in $inv.files) { Remove-Item -LiteralPath (Join-Path $root $f.path) -Force }
    foreach ($d in @($actualDirs | Sort-Object { $_.FullName.Length } -Descending)) {
        if (@(Get-ChildItem -LiteralPath $d.FullName -Force).Count) { throw 'Directory not empty' }
        Remove-Item -LiteralPath $d.FullName -Force
    }
    if (@(Get-ChildItem -LiteralPath $root -Force).Count) { throw 'Owned root not empty' }
    Remove-Item -LiteralPath $root -Force
    if (Test-Path -LiteralPath $root) { throw 'Owned root still exists' }
    $receipt.owned_root_absent = $true
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'cleanup-receipt.json') -Encoding utf8
} else {
    if (Test-Path -LiteralPath (Join-Path $out 'cleanup-dry.json')) { throw 'Dry receipt already exists' }
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'cleanup-dry.json') -Encoding utf8
}
$receipt | ConvertTo-Json -Depth 8
