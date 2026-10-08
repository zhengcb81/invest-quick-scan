$ErrorActionPreference = 'Stop'
$swrRepository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
$swrOwn = (Resolve-Path -LiteralPath (Join-Path $swrRepository 'runs/sw-repair-2026-10-08-01')).Path
$swrJunctionRecords = @()
foreach ($swrKind in @('root', 'parent')) {
    $swrBase = [IO.Path]::GetFullPath((Join-Path $swrOwn "junction-fixtures/$swrKind"))
    if (-not $swrBase.StartsWith($swrOwn + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $swrBase)) { throw 'Unsafe or preexisting junction fixture' }
    $swrWorkspace = Join-Path $swrBase 'workspace'
    $swrForeign = Join-Path $swrBase 'foreign'
    New-Item -ItemType Directory -Path (Join-Path $swrWorkspace 'data/quick_scan') -Force | Out-Null
    New-Item -ItemType Directory -Path $swrForeign | Out-Null
    [IO.File]::WriteAllText((Join-Path $swrWorkspace 'data/quick_scan/marker.txt'), 'owned fixture')
    [IO.File]::WriteAllText((Join-Path $swrForeign 'sentinel.txt'), 'foreign-to-workspace but controller-owned')
    if ($swrKind -eq 'root') {
        New-Item -ItemType Directory -Path (Join-Path $swrWorkspace 'backups') | Out-Null
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
