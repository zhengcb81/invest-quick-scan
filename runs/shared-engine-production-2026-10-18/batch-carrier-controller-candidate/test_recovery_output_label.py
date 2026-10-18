"""Real CLI refusal at startup, never an owner/API positive."""
from pathlib import Path
import subprocess
import sys
import pytest

@pytest.mark.parametrize("phase,label",[("cold","good"),("recover","../escape"),("recover","中文"),("recover","a"*33)])
def test_recovery_label_cannot_widen_mode_or_output_path(tmp_path,phase,label):
 driver=Path(__file__).with_name("run_real_profile_smoke.py")
 r=subprocess.run([sys.executable,"-B","-X","utf8",str(driver),"--config",str(tmp_path/"absent.json"),"--phase",phase,"--recovery-label",label],cwd=tmp_path,capture_output=True,check=False)
 assert r.returncode==2
 assert b'"error_type": "ValueError"' in r.stdout
 assert list(tmp_path.iterdir())==[]


@pytest.mark.parametrize("name",["recovered-session","recovered-export","recovered-report","recovery-observation.json"])
def test_omitted_label_cannot_overwrite_existing_recovery(tmp_path,name):
 import importlib.util
 spec=importlib.util.spec_from_file_location("recovery_output_candidate",Path(__file__).with_name("run_real_profile_smoke.py"))
 driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
 original=tmp_path/name;original.write_bytes(b"preserved partial")
 with pytest.raises(ValueError,match="existing_recovery_outputs_require_fresh_label"):
  driver.recovery_output_root(tmp_path,None)
 assert original.read_bytes()==b"preserved partial"
 assert not (tmp_path/"recovery-carrier02").exists()
 assert driver.recovery_output_root(tmp_path,"carrier02")==tmp_path/"recovery-carrier02"
