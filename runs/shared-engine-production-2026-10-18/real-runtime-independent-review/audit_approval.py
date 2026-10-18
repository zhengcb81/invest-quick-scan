"""Read real fixed owner records and original validator; writes thin hashes only."""
from pathlib import Path
import hashlib
import json
import sys

OWN=Path(__file__).resolve().parent;BASE=OWN.parent;ROOT=BASE.parents[1]
OUT=BASE/"actual-native-alphabet-01"
OWNER=ROOT/"runs/c16b/native-owner-alphabet-01/owner-workspace"
sys.path[:0]=[str(ROOT.parent/"StockWiki"),str(ROOT.parent/"StockQAbyLLM")]
from stockwiki.quick_scan_refresh_delegation import validate_grant,validate_delegated_confirmation
from src.utils.quick_scan_owner_budget_continuation import digest
def read(p):return json.loads(p.read_text(encoding="utf8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
confirmed=read(OUT/"delegated-confirm.stdout.json");installed=read(OUT/"delegated-install.stdout.json")
preview=read(OUT/"preview.stdout.json");policy=read(OUT/"owner-policy.installed.json")
request=read(OUT/"refresh-request.json");config=read(OUT/"run-config.json")
state=OWNER/"runs/state/quick_scan_refresh"
grantpath=state/"delegations"/(installed["grant_id"]+".json")
confirmationpath=state/"delegated-confirmations"/(confirmed["confirmation_id"]+".json")
grant=read(grantpath);validate_grant(grant)
confirmation=read(confirmationpath);validate_delegated_confirmation(confirmation,confirmed["confirmation_id"])
assert grant["grant_id"]==confirmed["grant_id"]==installed["grant_id"]
assert confirmed["method"]==confirmation["method"]=="native_owner_delegated_agent"
assert grant["binding"]["preview_id"]==confirmation["preview_id"]==preview["preview_id"]
assert confirmation["delegation"]==grant
assert policy["owner_principal"]==grant["owner_principal"]==confirmation["owner_principal"]
assert sha(OWNER/"config/quick_scan_refresh.json")==sha(OUT/"owner-policy.installed.json")
assert all(value["API_requests"]==0 and value["dispatch_started"] is False for value in [preview,installed,confirmed])
assert preview["request_sha256"]==digest(request)
assert preview["policy_sha256"]==digest(policy)
assert len(request["question_ids"])==len(set(request["question_ids"]))==12
assert policy["budget_exposure_acceptance"]["control"]["cells"][0]["controls"]["max_output_tokens"]==16384
assert config["confirmation_id"]==confirmed["confirmation_id"]
admitted=read(OUT/"admission-result.json")
assert admitted["status"]=="accepted" and admitted["permission_authenticated"] is True
assert admitted["registration"]["confirmation_id"]==confirmed["confirmation_id"]
assert admitted["registration"]["policy_sha256"]==digest(policy)
result=dict(protocol="iqs.independent_real_native_approval_chain/1.0.0",native_fixed_namespace=str(OWNER.relative_to(ROOT)),grant_sha256=sha(grantpath),confirmation_sha256=sha(confirmationpath),grant_id=grant["grant_id"],confirmation_id=confirmed["confirmation_id"],preview_id=preview["preview_id"],original_record_validators_passed=True,fixed_installed_policy_matches=True,original_principal_consistent=True,real_os_native_record_authority_not_profile_authentication=True,request_and_policy_hashes_match=True,approved_question_count=12,all_approval_steps_zero_http=True,admitted=True,profile_is_not_password_or_crypto_identity=True,reviewer_paid_calls=0)
(OWN/"approval-chain.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
print(json.dumps({"approval_chain_valid":True,"question_count":12,"approval_http":0}))
