$ErrorActionPreference='Stop'
$swrRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$swrRoot=[IO.Path]::GetFullPath((Join-Path $swrRepo 'runs/evid-lab-lr02b-2026-10-08-01'))
$swrEvidence=Join-Path $swrRepo 'docs/implementation/intake/EVID-LAB-01/2026-10-08-lr02b'
if (-not $swrRoot.StartsWith((Join-Path $swrRepo 'runs')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Wrong root' }
$swrProcesses=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.ProcessId -ne $PID -and ($_.CommandLine -like '*evid-lab-lr02b-2026-10-08-01*' -or ($_.CommandLine -like '*EVID-LAB-01*lr02b-2026-10-08*' -and ($_.CommandLine -like '*guarded_run.py*' -or $_.CommandLine -like '*run.py*'))) })
if ($swrProcesses.Count) { throw 'Own runner or browser active' }
$swrResult=Get-Content -LiteralPath (Join-Path $swrEvidence 'verification/result.json') -Raw -Encoding utf8 | ConvertFrom-Json
$swrListeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in @($swrResult.browser.ports) })
if ($swrListeners.Count) { throw 'Own listener active' }
$swrInventory=Get-Content -LiteralPath (Join-Path $swrEvidence 'junction-inventory.json') -Raw -Encoding utf8 | ConvertFrom-Json
if ([IO.Path]::GetFullPath($swrInventory.absolute_root) -ne $swrRoot -or $swrInventory.links.Count -ne 0) { throw 'Unexpected link inventory' }
$swrRemoved=@()
foreach ($swrLink in $swrInventory.links) {
    $swrNodePath=[IO.Path]::GetFullPath($swrLink.link)
    $swrTargetPath=[IO.Path]::GetFullPath($swrLink.target)
    foreach ($swrPath in @($swrNodePath,$swrTargetPath)) { if (-not $swrPath.StartsWith($swrRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Link escaped' } }
    $swrNode=Get-Item -LiteralPath $swrNodePath -Force
    $swrNodeTargets=@($swrNode.Target)
    if ($swrNode.LinkType -ne 'Junction' -or $swrNodeTargets.Count -ne 1 -or [IO.Path]::GetFullPath($swrNodeTargets[0]) -ne $swrTargetPath) { throw 'Unexpected link' }
    $swrTarget=Get-Item -LiteralPath $swrTargetPath -Force
    if (($swrTarget.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrTarget.LinkType) { throw 'Linked target' }
    $swrBefore=@(Get-ChildItem -LiteralPath $swrTargetPath -Force | Select-Object Name,Length,Attributes)
    [IO.Directory]::Delete($swrNodePath,$false)
    if ((Test-Path -LiteralPath $swrNodePath) -or -not (Test-Path -LiteralPath $swrTargetPath)) { throw 'Unlink failed or target removed' }
    $swrAfter=@(Get-ChildItem -LiteralPath $swrTargetPath -Force | Select-Object Name,Length,Attributes)
    $swrBeforeText=ConvertTo-Json -InputObject $swrBefore -Compress
    $swrAfterText=ConvertTo-Json -InputObject $swrAfter -Compress
    if ($swrBeforeText -ne $swrAfterText) { throw 'Target changed' }
    $swrRemoved += [pscustomobject]@{link=$swrNodePath;target=$swrTargetPath;node_removed=$true;target_preserved=$true}
}
[ordered]@{schema='iqs_lr02b_unlink/1';process_matches=0;listener_matches=0;links=$swrRemoved} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $swrEvidence 'junction-removal.json') -Encoding utf8
$swrQueue=[Collections.Generic.Queue[string]]::new()
$swrQueue.Enqueue($swrRoot)
$swrFiles=@(); $swrDirs=@()
while ($swrQueue.Count) {
    $swrDirectory=$swrQueue.Dequeue()
    $swrNode=Get-Item -LiteralPath $swrDirectory -Force
    if (($swrNode.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrNode.LinkType) { throw 'Reparse before traversal' }
    foreach ($swrChild in @(Get-ChildItem -LiteralPath $swrDirectory -Force)) {
        $swrFull=[IO.Path]::GetFullPath($swrChild.FullName)
        if (-not $swrFull.StartsWith($swrRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or ($swrChild.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $swrChild.LinkType) { throw 'Unsafe child' }
        $swrRelative=$swrFull.Substring($swrRoot.Length+1).Replace('\','/')
        if ($swrChild.PSIsContainer) { $swrDirs += $swrRelative; $swrQueue.Enqueue($swrFull) }
        else { $swrFiles += [pscustomobject]@{path=$swrRelative;bytes=$swrChild.Length;sha256=(Get-FileHash -LiteralPath $swrFull -Algorithm SHA256).Hash.ToLowerInvariant()} }
    }
}
[ordered]@{schema='iqs_lr02b_cleanup_baseline/1';absolute_root=$swrRoot;process_matches=0;listener_matches=0;known_sessions_exited=@('51936','27960','45434');junction_nodes_unlinked=0;files=@($swrFiles | Sort-Object path);directories=@($swrDirs | Sort-Object)} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $swrEvidence 'cleanup-baseline.json') -Encoding utf8
Write-Output ('unlinked=0 owned_files='+$swrFiles.Count+' process_matches=0 listener_matches=0')
