import importlib.util
import os
from pathlib import Path
root=Path(os.environ["IQS_CONTINUATION_OWN"])
spec=importlib.util.spec_from_file_location("continuation_write_audit",root/"guard/sitecustomize.py")
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
import src.utils
src.utils.__path__.insert(0,str(root/"qa/src/utils"))

import tests
tests.__path__.insert(0,str(root/"qa/tests"))
import tests.unit
tests.unit.__path__.insert(0,str(root/"qa/tests/unit"))
