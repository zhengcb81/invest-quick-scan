from pathlib import Path
import subprocess,sys,shutil,json
OUT=Path(__file__).parent;P=OUT/'perf'
for ext in ['json','log']:shutil.copyfile(P/('tests.'+ext),P/('tests-suite64.'+ext))
try:
    subprocess.run([sys.executable,'-B',str(OUT/'run_perf.py'),'tests/unit/test_benchmark_provenance.py',*sys.argv[1:]],check=True)
    result=json.loads((P/'tests.json').read_bytes())
    for ext in ['json','log']:shutil.copyfile(P/('tests.'+ext),P/('provenance-tests.'+ext))
    if result['exit_code']!=0:raise RuntimeError('provenance delta failed')
finally:
    for ext in ['json','log']:shutil.copyfile(P/('tests-suite64.'+ext),P/('tests.'+ext))
