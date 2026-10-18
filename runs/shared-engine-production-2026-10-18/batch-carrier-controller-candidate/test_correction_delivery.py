"""Pure metadata correction chain; synthetic files, no native authority."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest

OWN=Path(__file__).resolve().parent
PARENT=OWN.parent/"real-profile-smoke-candidate"
sys.path.insert(0,str(PARENT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fixturemod=load("parent_metadata_fixtures",PARENT/"conftest.py")
checker=load("correction_metadata",OWN/"controller_delivery.py")

@pytest.fixture
def correction(tmp_path,monkeypatch):
 d=fixturemod.deployed.__wrapped__(tmp_path,monkeypatch)
 old=fixturemod.delivery
 for key in ("HERE","BASE","REVIEW","SOURCE_CAS","CONTROLLER_CAS","PROOF"):
  monkeypatch.setattr(checker,key,getattr(old,key))
 root=d["root"]; extra=[root/"runtime.py",root/"controller.py"]
 for p in extra:p.write_bytes(b"# old reviewed metadata fixture\n")
 base={p:checker.sha(p) for p in extra}
 rows=d["files"]+[dict(component="synthetic",relative_path=p.name,path=str(p),candidate_sha256=base[p],delivered_sha256=base[p]) for p in extra]
 controller=checker.read(d["paths"]["controller"])
 controller["files"].append(dict(path=str(extra[1]),bytes=extra[1].stat().st_size,sha256=base[extra[1]]))
 d["put"]("controller",controller)
 final=checker.read(d["paths"]["final"]);final["controller_cas"]=d["ref"]("controller");d["put"]("final",final)
 appendix=checker.read(d["paths"]["appendix"]);appendix.update(files=rows,controller_cas=d["ref"]("controller"),review_final=d["ref"]("final"));d["put"]("appendix",appendix)
 parent=checker.read(d["paths"]["proof"]);parent.update(files=rows,controller_cas=d["ref"]("controller"),review_final=d["ref"]("final"),delivery_addendum=d["ref"]("appendix"));d["put"]("proof",parent)
 initial_paths={Path(r["path"]).resolve() for r in rows}
 monkeypatch.setattr(checker,"runtime_paths",lambda:initial_paths)
 for key,name in (("CORRECTION_CAS","delta-cas.json"),("CORRECTION_REVIEW","delta-final.json"),("CORRECTION_DELIVERY","delta-delivery.json"),("CORRECTION_PROOF","delta-proof.json")):
  monkeypatch.setattr(checker,key,root/name)
 def put(path,value):path.write_text(json.dumps(value),encoding="utf8")
 def ref(path):return dict(path=str(path),sha256=checker.sha(path))
 for p in extra:p.write_bytes(b"# exact independent reviewed correction\n")
 cas=dict(files=[dict(kind="product",target=str(p),base_sha256=base[p],candidate_sha256=checker.sha(p)) for p in extra])
 put(checker.CORRECTION_CAS,cas)
 result=dict(status="passed_for_exact_batch_carrier_channel_alignment_and_recovery_provenance",open_findings=[],recovery_only=True,original_run_config={},original_checkpoint={},original_safe_output_proof={},reviewer=dict(agent_id="/root/production_node_review18",author_agent_ids=["/root","/root/author"]),parent_proof=ref(checker.PROOF),parent_review_final=parent["review_final"],source_cas=ref(checker.CORRECTION_CAS))
 put(checker.CORRECTION_REVIEW,result)
 files=copy.deepcopy(rows)
 for row in files:
  path=Path(row["path"])
  if path in extra:row.update(candidate_sha256=checker.sha(path),delivered_sha256=checker.sha(path))
 delivery=dict(status="independently_verified_exact_correction_delivery",open_findings=[],correction_final=ref(checker.CORRECTION_REVIEW),parent_proof=ref(checker.PROOF),source_cas=ref(checker.CORRECTION_CAS),files=files)
 put(checker.CORRECTION_DELIVERY,delivery)
 proof=dict(recovery_only=True,parent_proof=ref(checker.PROOF),correction_final=ref(checker.CORRECTION_REVIEW),correction_delivery=ref(checker.CORRECTION_DELIVERY),files=files)
 put(checker.CORRECTION_PROOF,proof)
 def reseal():
  final=checker.read(checker.CORRECTION_REVIEW);final["source_cas"]=ref(checker.CORRECTION_CAS);put(checker.CORRECTION_REVIEW,final)
  delivery=checker.read(checker.CORRECTION_DELIVERY);delivery.update(correction_final=ref(checker.CORRECTION_REVIEW),source_cas=ref(checker.CORRECTION_CAS));put(checker.CORRECTION_DELIVERY,delivery)
  proof=checker.read(checker.CORRECTION_PROOF);proof.update(correction_final=ref(checker.CORRECTION_REVIEW),correction_delivery=ref(checker.CORRECTION_DELIVERY),files=delivery["files"]);put(checker.CORRECTION_PROOF,proof)
 return dict(original=d,extra=extra,put=put,ref=ref,reseal=reseal)

def test_exact_corrective_chain_keeps_parent_review_immutable(correction):
 original_hash=checker.sha(checker.PROOF)
 result=checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))
 assert len(result["files"])==8 and checker.sha(checker.PROOF)==original_hash
 with pytest.raises(ValueError):checker.verify_deployment()

@pytest.mark.parametrize("field,value",[("status","passed"),("open_findings",["unfixed"]),("reviewer",dict(agent_id="/root",author_agent_ids=["/root"]))])
def test_unaccepted_semantic_correction_refused(correction,field,value):
 final=checker.read(checker.CORRECTION_REVIEW);final[field]=value;correction["put"](checker.CORRECTION_REVIEW,final);correction["reseal"]()
 with pytest.raises(ValueError):checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))

@pytest.mark.parametrize("mode",["omit_product","wrong_base","extra_product"])
def test_correction_cannot_change_its_parent_delta_scope(correction,mode):
 cas=checker.read(checker.CORRECTION_CAS)
 if mode=="omit_product":cas["files"]=cas["files"][:1]
 elif mode=="wrong_base":cas["files"][0]["base_sha256"]="0"*64
 else:cas["files"].append(dict(cas["files"][0],target=str(correction["original"]["source"])))
 correction["put"](checker.CORRECTION_CAS,cas);correction["reseal"]()
 with pytest.raises(ValueError):checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))

def test_unlisted_runtime_change_refused_even_after_operational_reseal(correction):
 path=correction["original"]["source"];path.write_bytes(b"# unreviewed edit\n")
 delivery=checker.read(checker.CORRECTION_DELIVERY)
 for row in delivery["files"]:
  if Path(row["path"])==path:row["delivered_sha256"]=checker.sha(path)
 correction["put"](checker.CORRECTION_DELIVERY,delivery);correction["reseal"]()
 with pytest.raises(ValueError,match="unreviewed_runtime_delta_outside_correction"):
  checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))

def test_wrong_parent_proof_not_substitutable(correction):
 proof=checker.read(checker.CORRECTION_PROOF);proof["parent_proof"]["sha256"]="0"*64;correction["put"](checker.CORRECTION_PROOF,proof)
 with pytest.raises(ValueError):checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))


def test_correction_never_authorizes_a_cold_generation_action(correction):
 proof=checker.read(checker.CORRECTION_PROOF);proof["recovery_only"]=False;correction["put"](checker.CORRECTION_PROOF,proof)
 with pytest.raises(ValueError,match="correction_is_recovery_only"):
  checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))


def test_recovery_correction_cannot_be_moved_to_another_run(correction,tmp_path):
 result=checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))
 with pytest.raises(ValueError,match="correction_is_only_for_original_saved_run"):
  checker.verify_public_inputs({},tmp_path,result)


def correction_context(correction):
 fixed=checker.BASE/"actual-native-catl-profile-01";fixed.mkdir()
 (fixed/"cold-session").mkdir();checkpoint=fixed/"cold-session/checkpoint.json";checkpoint.write_bytes(b'{"saved":"safe-original-only"}')
 safe=fixed/"crash-native-proof.json";safe.write_bytes(b'{"native_reference":"stockqa:SAVED"}')
 bridge=fixed/"public-identity-bridge.json";bridge.write_bytes(b'{"entity_id":"REAL","subject_key":"ASJ@1"}')
 board=correction["original"]["board"]
 refs={key:dict(path=p.name,bytes=p.stat().st_size,raw_sha256=checker.sha(p)) for key,p in (("evidence-board.json",board),("identity.json",bridge))}
 original=dict(run_root=str(fixed),public_board=str(board),public_identity=str(bridge),public_input_refs=refs,
  deployment_proof=correction["ref"](checker.PROOF),question_ids=["A","B"])
 config=fixed/"run-config.json";correction["put"](config,original)
 final=checker.read(checker.CORRECTION_REVIEW);final.update(original_run_config=correction["ref"](config),original_checkpoint=correction["ref"](checkpoint),original_safe_output_proof=correction["ref"](safe));correction["put"](checker.CORRECTION_REVIEW,final);correction["reseal"]()
 corrected=dict(original,deployment_proof=correction["ref"](checker.CORRECTION_PROOF))
 return fixed,corrected,checker.verify_deployment(correction["ref"](checker.CORRECTION_PROOF))


def test_corrected_context_is_same_saved_run_only(correction):
 fixed,config,result=correction_context(correction)
 checker.verify_public_inputs(config,fixed,result)
 assert (fixed/"cold-session").is_dir() # original driver's cold guard refuses


@pytest.mark.parametrize("field,value",[("question_ids",["OTHER"]),("run_root","foreign"),("source_pins",[])])
def test_correction_cannot_reselect_experiment_inputs(correction,field,value):
 fixed,config,result=correction_context(correction);config[field]=value
 with pytest.raises(ValueError,match="correction_cannot_change_original_experiment_inputs"):
  checker.verify_public_inputs(config,fixed,result)


def test_corrected_context_still_requires_original_checkpoint_bytes(correction):
 fixed,config,result=correction_context(correction);(fixed/"cold-session/checkpoint.json").write_bytes(b"{}")
 with pytest.raises(ValueError,match="correction_original_safe_checkpoint_changed"):
  checker.verify_public_inputs(config,fixed,result)
