from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
QA=ROOT.parents[3]/'StockQAbyLLM'
sys.path.insert(0,str(QA))
sys.path.insert(0,str(QA.parent/'iqs-agent-runtime-lab/src'))
sys.path.insert(0,str(QA.parent/'iqs-company-agent-lab/src'))
if '--overlay' in sys.argv:
    sys.argv.remove('--overlay')
    import src.utils
    src.utils.__path__.insert(0,str(ROOT/'src/utils'))
    import src.providers
    src.providers.__path__.insert(0,str(ROOT/'src/providers'))
    import iqs_agent_runtime_lab
    iqs_agent_runtime_lab.__path__.insert(0,str(ROOT/'runtime/iqs_agent_runtime_lab'))
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(ROOT/('green6-temp' if '--green' in sys.argv else 'red-temp')),str(ROOT/'tests/unit/test_research_diagnostic_durability.py'),str(ROOT/'runtime/tests/test_research_response_taxonomy.py')]+([] if '--green' not in sys.argv else [str(QA/'tests/unit/test_research_validation_policy.py'),str(QA/'tests/unit/test_llm_research_client.py'),str(ROOT/'tests/unit/test_research_visible_output.py')])) )
