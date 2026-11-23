"""Scoped 007787a combo probe for THREE-MARKET-COVERAGE-20261121.

Runs the REAL Dashboard adapter stack (build_ports mode=owner + TestClient) at
the acceptance commit and exercises the cross-ID listing resolution plus the
quick-scan read for the three card companies + the AMEC control.  Read-only:
no IQS/StockWiki writes, no model or paid calls, the app data dir is a fresh
temp root under the IQS runs tree.

Mirrors the five-card acceptance probe (.test-runs/five21/candidate_probe.py)
but only the quick-scan section; identity/citation/statement sections are out
of scope here.
"""
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DASH_ROOT = Path(r"C:\Users\郑曾波\Projects\investment-dashboard")
IQS_ROOT = Path(r"C:\Users\郑曾波\Projects\invest-quick-scan")
OUT = IQS_ROOT / "docs/implementation/reviews/THREE-MARKET-COVERAGE-20261121/evidence/combo-probe-quickscan.json"

sys.path.insert(0, str(DASH_ROOT))
from backend.dashboard.adapters.factory import build_ports  # noqa: E402
from backend.dashboard.transport.http import create_app  # noqa: E402

dashboard_commit = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=DASH_ROOT).decode().strip()
assert dashboard_commit == "007787aa411b79f65d944145598f7a91ce27a069", dashboard_commit

iqs_cfg = json.loads((IQS_ROOT / "config/dashboard.local.json").read_text(encoding="utf-8-sig"))
business = Path(r"C:\Users\郑曾波\Projects\StockWiki")
stage = Path(tempfile.mkdtemp(prefix="tmc-combo-probe-"))
links = stage / "stockwiki-source-settings.json"
links.write_text(json.dumps({
    "cwp_python": r"C:\Users\郑曾波\Projects\company-wiki\.venv\Scripts\python.exe",
    "cwp_root": r"C:\Users\郑曾波\Projects\investment-dashboard\.test-runs\five21\cwp",
    "cwp_config": r"C:\Users\郑曾波\Projects\company-wiki\config\source_catalog.yaml",
    "sw_python": iqs_cfg["stockwiki_python"], "sw_cli": str(business / "dashboard_issuer_proof_cli.py"),
    "sw_root": str(business),
}, ensure_ascii=False), encoding="utf-8")
params = {
    "iqs_origin": "http://127.0.0.1:8766", "iqs_universe_id": iqs_cfg["universe_id"],
    "stockwiki_identity_python": iqs_cfg["stockwiki_python"],
    "stockwiki_identity_root": str(business),
    "stockwiki_identity_workspace": str(business),
    "stockwiki_iqs_identity_workspace": iqs_cfg["workspace_root"],
    "stockwiki_python": iqs_cfg["stockwiki_python"], "stockwiki_root": str(business),
    "stockwiki_workspace": str(business),
    "stockwiki_source_link_settings": str(links),
    "cwp_python": r"C:\Users\郑曾波\Projects\company-wiki\.venv\Scripts\python.exe",
    "cwp_root": r"C:\Users\郑曾波\Projects\investment-dashboard\.test-runs\five21\cwp",
    "cwp_config": r"C:\Users\郑曾波\Projects\company-wiki\config\source_catalog.yaml",
    "cwp_proof_python": iqs_cfg["stockwiki_python"],
    "cwp_proof_cli": str(business / "dashboard_issuer_proof_cli.py"),
    "cwp_proof_workspace": str(business),
}

scope = {
    "wuxi": ("ENT_2a41e04d-8679-4be5-9e30-3aaf89bdd00e", "LST_f26e4cea-69f3-4525-885f-c13885c731f8"),
    "alibaba": ("ENT_e4d964f0-ed84-43b5-a9c7-c9b4b38d8101", "LST_591474dd-2778-46ce-8b42-ad5fc483d64d"),
    "mongodb": ("ENT_41250504-734e-4460-9843-86c4e1f3851d", "LST_2d86780f-c98e-49cc-a214-34885c8820fa"),
    "amec_iqs": ("ENT_99deceb6-f58a-48b1-bd6b-437621015d76", "LST_4b1d9b36-f70b-4c7b-b107-4ceb5bfa1b59"),
}
evidence = {"tested": datetime.now(timezone.utc).isoformat(), "dashboard": dashboard_commit,
            "iqs_origin": params["iqs_origin"], "data_dir": str(stage), "companies": {}}

from fastapi.testclient import TestClient  # noqa: E402

with TestClient(create_app(build_ports(params, mode="owner"), stage / "probe-data", mode="owner",
                           allow_test_origin=True), base_url="http://127.0.0.1") as client:
    for name, (entity, listing) in scope.items():
        return_to = f"http://127.0.0.1:48766/company/{entity}/quickscan?listing_id={listing}"
        response = client.get(f"/api/v1/companies/{entity}/quick-scan",
                              params={"listing_id": listing, "return_to": return_to})
        body = response.json()
        snapshot = body.get("snapshot") or {}
        out = {"http": response.status_code,
               "state": snapshot.get("state"), "reasons": snapshot.get("reason_codes"),
               "error": body.get("code"),
               "company_preserved": (body.get("company") or {}).get("entity_id") == entity
                                    and (body.get("company") or {}).get("listing_id") == listing,
               "formal_id": ((body.get("latest_formal") or {}) or {}).get("observation_id"),
               "history": len(body.get("history") or []),
               "link_status": (body.get("link") or {}).get("status"),
               "return_available": bool((body.get("link") or {}).get("return_to"))}
        evidence["companies"][name] = out
        print(name, json.dumps(out, ensure_ascii=False), flush=True)

OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("saved", OUT, flush=True)
