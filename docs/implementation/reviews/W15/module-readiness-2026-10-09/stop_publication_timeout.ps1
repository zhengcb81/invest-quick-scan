$ErrorActionPreference='Stop'
$w15Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../..'))
$w15Out=Join-Path $w15Root 'docs/implementation/intake/W15/module-readiness-2026-10-09/source-publication'
$w15Receipt=Join-Path $w15Out 'StockQAbyLLM-commit-timeout-descendants.json'
if (Test-Path -LiteralPath $w15Receipt) { throw 'Once-only timeout receipt already exists' }
$w15All=@(Get-CimInstance Win32_Process -ErrorAction Stop)
$w15Top=@($w15All | Where-Object ProcessId -eq 73628)
if ($w15Top.Count -ne 1 -or $w15Top[0].Name -ne 'git.exe' -or
    $w15Top[0].ParentProcessId -ne 104160 -or
    $w15Top[0].CommandLine -notlike '*Persist modular quick scan routes and execute incremental refresh safely*' -or
    [Math]::Abs(($w15Top[0].CreationDate.ToUniversalTime()-[DateTimeOffset]::Parse('2026-10-09T21:34:52.294177Z').UtcDateTime).TotalSeconds) -gt 1) { throw 'Original exact commit process not verified; do not stop guessed PID' }
$w15Ids=@(73628)
do {
    $w15New=@($w15All | Where-Object { $w15Ids -contains $_.ParentProcessId -and $w15Ids -notcontains $_.ProcessId } | Select-Object -ExpandProperty ProcessId)
    $w15Ids+=$w15New
} while ($w15New.Count -gt 0)
$w15Owned=@($w15All | Where-Object { $w15Ids -contains $_.ProcessId })
foreach ($w15Process in $w15Owned) {
    if ($w15Process.CreationDate -lt $w15Top[0].CreationDate -or $w15Process.Name -notin @('git.exe','conhost.exe','sh.exe','python.exe')) { throw 'Unrecognized descendant; refuse broad termination' }
}
$w15Stopped=@()
foreach ($w15Id in @($w15Ids | Sort-Object -Descending)) {
    $w15Before=@($w15Owned | Where-Object ProcessId -eq $w15Id)[0]
    $w15Now=@(Get-CimInstance Win32_Process -Filter "ProcessId=$w15Id")
    if ($w15Now.Count) {
        if ($w15Now[0].CreationDate -ne $w15Before.CreationDate -or $w15Now[0].Name -ne $w15Before.Name) { throw 'PID reuse; refuse termination' }
        Stop-Process -Id $w15Id -Force -ErrorAction Stop
        $w15Stopped+=$w15Id
    }
}
$w15Remaining=@(Get-CimInstance Win32_Process | Where-Object { $w15Ids -contains $_.ProcessId -and $_.CreationDate -ge $w15Top[0].CreationDate })
if ($w15Remaining.Count) { throw 'Original descendants remain alive' }
[ordered]@{controller_exit=1;reason='Original normal git commit communicate timed out at 600s';controller_pid=104160;original_commit_pid=73628;normal_hooks_not_skipped=$true;verified_descendants=@($w15Owned | ForEach-Object { [ordered]@{pid=$_.ProcessId;parent=$_.ParentProcessId;name=$_.Name;created_at=$_.CreationDate.ToUniversalTime().ToString('o')} });stopped_verified_pids=$w15Stopped;remaining_verified_processes=0;created_at=[DateTime]::UtcNow.ToString('o');source_files_deleted=0} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $w15Receipt -Encoding utf8
Write-Output ('verified_owned_processes_stopped='+$w15Stopped.Count)
