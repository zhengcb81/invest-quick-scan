param([switch]$Resume)
$ErrorActionPreference = 'Stop'
$swrRepository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../../..')).Path
$swrOwn = (Resolve-Path -LiteralPath (Join-Path $swrRepository 'runs/sw-repair-remediation-2026-10-08-01')).Path
$swrJunctionRecords = @()
foreach ($swrKind in @('root', 'parent')) {
    $swrBase = [IO.Path]::GetFullPath((Join-Path $swrOwn "junction-fixtures/$swrKind"))
    if (-not $swrBase.StartsWith($swrOwn + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe junction fixture' }
    if (Test-Path -LiteralPath $swrBase) {
        if (-not $Resume -or $swrKind -ne 'root') { throw 'Unexpected preexisting fixture' }
        $swrFiles=@(Get-ChildItem -LiteralPath $swrBase -File -Recurse -Force)
        if ($swrFiles.Count -ne 2 -or [IO.File]::ReadAllText((Join-Path $swrBase 'foreign/sentinel.txt')) -ne 'foreign-to-workspace but controller-owned' -or [IO.File]::ReadAllText((Join-Path $swrBase 'workspace/data/quick_scan/marker.txt')) -ne 'owned fixture') { throw 'Unexpected partial fixture' }
        if (@(Get-ChildItem -LiteralPath $swrBase -Recurse -Force | Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count) { throw 'Unexpected existing link' }
    }
    $swrWorkspace = Join-Path $swrBase 'workspace'
    $swrForeign = Join-Path $swrBase 'foreign'
    New-Item -ItemType Directory -Path (Join-Path $swrWorkspace 'data/quick_scan') -Force | Out-Null
    New-Item -ItemType Directory -Path $swrForeign -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $swrWorkspace 'data/quick_scan/marker.txt'), 'owned fixture')
    [IO.File]::WriteAllText((Join-Path $swrForeign 'sentinel.txt'), 'foreign-to-workspace but controller-owned')
    if ($swrKind -eq 'root') {
        New-Item -ItemType Directory -Path (Join-Path $swrWorkspace 'backups') -Force | Out-Null
        $swrLink = Join-Path $swrWorkspace 'backups/quick_scan'
    } else {
        $swrLink = Join-Path $swrWorkspace 'backups'
    }
    New-Item -ItemType Junction -Path $swrLink -Target $swrForeign | Out-Null
    $swrItem = Get-Item -LiteralPath $swrLink -Force
    if ($swrItem.LinkType -ne 'Junction') { throw 'Real Windows junction not created' }
    $swrJunctionRecords += [pscustomobject]@{kind=$swrKind;link=$swrLink;target=$swrForeign;link_type=$swrItem.LinkType}
}
$swrJunctionRecords | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $swrOwn 'junction-fixtures.json') -Encoding UTF8
$swrJunctionRecords | ConvertTo-Json -Depth 4 -Compress
