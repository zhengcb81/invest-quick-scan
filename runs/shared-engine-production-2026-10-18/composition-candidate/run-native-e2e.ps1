param([string]$TempName = 't03', [string]$EvidenceName = 'native-e2e-03')
$ErrorActionPreference = 'Stop'
if ($TempName -notmatch '^t[a-zA-Z0-9-]+$' -or $EvidenceName -notmatch '^[a-zA-Z0-9-]+$') { throw 'simple owned test labels required' }
$compositionCode = $PSScriptRoot
$nativeOwned = Join-Path $compositionCode 'n'
$candidateRoot = Split-Path $compositionCode -Parent
Copy-Item -LiteralPath (Join-Path $candidateRoot 'owner-services-candidate/src/utils/quick_scan_owner_research.py') -Destination (Join-Path $nativeOwned 'qa/src/utils/quick_scan_owner_research.py')
Copy-Item -LiteralPath (Join-Path $candidateRoot 'owner-services-candidate/runtime-port-candidate/src/iqs_agent_runtime_lab/port.py') -Destination (Join-Path $nativeOwned 'bridge/src/iqs_agent_runtime_lab/port.py')
Copy-Item -LiteralPath (Join-Path $candidateRoot 'owner-services-candidate/fixture-candidate/tests/integration/test_c06_refresh_admission.py') -Destination (Join-Path $nativeOwned 'qa/tests/integration/test_c06_refresh_admission.py')
Copy-Item -LiteralPath (Join-Path $compositionCode 'fixture-candidate/tests/integration/test_c06_subject_public_e2e.py') -Destination (Join-Path $nativeOwned 'qa/tests/integration/test_c06_subject_public_e2e.py')
Copy-Item -LiteralPath (Join-Path $candidateRoot 'company-native-task-overlay/src/iqs_company_agent_lab/task.py') -Destination (Join-Path $nativeOwned 'company/src/iqs_company_agent_lab/task.py')
$nativeTemp = Join-Path $nativeOwned $TempName
$nativeXml = Join-Path $compositionCode ($EvidenceName + '.xml')
$nativeTest = Join-Path $compositionCode 'tests/test_shared_company_engine_native_e2e.py'
$env:IQS_C06_RUN_INTEGRATION = '1'
$env:IQS_C06_OWN = $nativeOwned
$env:IQS_C06_COMPOSITION_CODE_ROOT = $compositionCode
$env:IQS_C06_COMPANY_ROOT = Join-Path $nativeOwned 'company'
$env:IQS_C06_BRIDGE_ROOT = Join-Path $nativeOwned 'bridge'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = @((Join-Path $nativeOwned 'guard'), (Join-Path $nativeOwned 'qa'), (Join-Path $nativeOwned 'sw'), (Join-Path $nativeOwned 'iqs'), (Join-Path $nativeOwned 'company/src'), (Join-Path $nativeOwned 'bridge/src')) -join ';'
$env:TEMP = Join-Path $nativeOwned 'tmp'
$env:TMP = $env:TEMP
@'
import os, subprocess, sys
names = ("SystemRoot", "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "PYTHONUTF8",
    "PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "IQS_C06_RUN_INTEGRATION", "IQS_C06_OWN",
    "IQS_C06_COMPOSITION_CODE_ROOT", "IQS_C06_COMPANY_ROOT", "IQS_C06_BRIDGE_ROOT")
safe = {name: os.environ[name] for name in names if name in os.environ}
command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", sys.argv[1], "-q",
           "--basetemp", sys.argv[2], "--junitxml", sys.argv[3]]
raise SystemExit(subprocess.run(command, env=safe).returncode)
'@ | python -B -X utf8 - $nativeTest $nativeTemp $nativeXml
exit $LASTEXITCODE
