"""Independent hook/source equivalence; no implementation writes."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path.cwd()
OWN=Path(__file__).resolve().parent
BASE=OWN.parent
C=BASE/"native-continuation-candidate"
REPOS={"qa":ROOT.parent/"StockQAbyLLM","sw":ROOT.parent/"StockWiki","iqs":ROOT}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def norm(tree):
    for node in ast.walk(tree):
        for field,values in list(ast.iter_fields(node)):
            if not isinstance(values,list) or not values or not all(isinstance(n,ast.stmt) for n in values):continue
            out=[]; pending=[]
            def flush():
                out.extend(sorted(pending,key=lambda n:ast.dump(n,include_attributes=False)));pending.clear()
            for value in values:
                if isinstance(value,(ast.Import,ast.ImportFrom)):
                    for alias in value.names:
                        new=copy.deepcopy(value);new.names=[alias];pending.append(new)
                else:
                    flush();out.append(value)
            flush();setattr(node,field,out)
    return ast.dump(tree,include_attributes=False)
cas=json.loads((C/"candidate-cas.json").read_text())
rows=[]
for entry in cas["files"]:
    candidate=Path(entry["candidate_path"]); actual=REPOS[entry["repository"]]/entry["path"]
    result={"repository":entry["repository"],"path":entry["path"],"candidate_sha256":sha(candidate),"actual_sha256":sha(actual),"exact":candidate.read_bytes()==actual.read_bytes()}
    if actual.suffix==".py":
        a,b=[ast.parse(p.read_text(encoding="utf-8-sig")) for p in (candidate,actual)]
        changed_annotations=[]
        for fn in [n for n in ast.walk(b) if isinstance(n,ast.FunctionDef) and n.name in {"_physical_ids","risk_hold_total"}]:
            for i,n in enumerate(fn.body):
                if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in {"ids","holds"}:
                    assert (fn.name,n.target.id,ast.unparse(n.annotation)) in {("_physical_ids","ids","set[str]"),("risk_hold_total","holds","dict[str, int]")}
                    changed_annotations.append([fn.name,n.target.id,ast.unparse(n.annotation)])
                    fn.body[i]=ast.Assign(targets=[n.target],value=n.value)
        result.update(equivalent=norm(a)==norm(b),local_annotation_changes=changed_annotations)
        assert result["equivalent"],entry["path"]
    else:assert result["exact"]
    rows.append(result)
drivers={name:sha(BASE/name) for name in ["activate_real_native_smoke.py","run_real_admitted_smoke.py"]}
assert drivers=={"activate_real_native_smoke.py":"aabdb73ca3387462d0951da27f81876fbd9b8710e746f1e4632e546d8597aef4","run_real_admitted_smoke.py":"318e30309ea84de13555664019d8a194343608d45a73cd12bfd716288413fbf6"}
output=dict(protocol="iqs.independent_native_delivery_equivalence/1.0.0",rows=rows,driver_sha256=drivers,annotation_rule="only two exact local variable annotations; no runtime effect",import_rule="only adjacent standalone import groups, alias/module/level retained; no executable statement crossed",paid_calls=0)
(OWN/"delivery-equivalence.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf8")
print(json.dumps({"paths":len(rows),"equivalent":True,"driver_hashes":drivers}))
