import importlib.util,os
from pathlib import Path
root=Path(os.environ["IQS_CONTINUATION_OWN"])
spec=importlib.util.spec_from_file_location("write_audit",root/"guard/write_audit.py")
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
import src,src.utils,sys
src.utils.__path__.insert(0,str(root/"qa/src/utils"))
original=Path(src.__file__).resolve().parent/"runners"
spec=importlib.util.spec_from_file_location("src.runners",original/"__init__.py",submodule_search_locations=[str(root/"qa/src/runners"),str(original)])
module=importlib.util.module_from_spec(spec);sys.modules["src.runners"]=module;spec.loader.exec_module(module)
