"""Regression checks for the cross-harness lane ownership plan."""

import json
import re
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
LANE_DIR = ROOT / "docs" / "implementation" / "parallel-lanes"


class ParallelLanePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((LANE_DIR / "lane-manifest.json").read_text(encoding="utf-8"))
        cls.tasks = json.loads((ROOT / "docs" / "implementation" / "tasks.json").read_text(encoding="utf-8"))
        cls.handoff = json.loads((LANE_DIR / "handoff.schema.json").read_text(encoding="utf-8"))

    def test_every_planned_task_has_exactly_one_matching_owner_lane(self):
        task_owner = {task["id"]: task["owner"] for task in self.tasks["tasks"]}
        assignments = [
            (lane["id"], lane["task_owner"], task_id)
            for lane in self.manifest["lanes"]
            for task_id in lane["task_ids"]
        ]
        assigned_ids = [task_id for _lane_id, _owner, task_id in assignments]

        self.assertEqual(len(assigned_ids), len(set(assigned_ids)), "a task is assigned to more than one lane")
        self.assertEqual(set(task_owner), set(assigned_ids), "the lane map must cover the full plan")
        for _lane_id, owner, task_id in assignments:
            self.assertEqual(task_owner[task_id], owner, f"{task_id} was assigned outside its task owner")

    def test_owned_project_scopes_are_disjoint_and_docs_exist(self):
        scopes = []
        lane_ids = set()
        for lane in self.manifest["lanes"]:
            self.assertNotIn(lane["id"], lane_ids)
            lane_ids.add(lane["id"])
            self.assertTrue((LANE_DIR / lane["document"]).is_file(), lane["document"])
            project = PurePosixPath(lane["git_root"].replace("\\", "/").casefold())
            for owned_path in lane["owned_paths"]:
                scope = (project / PurePosixPath(owned_path.replace("\\", "/"))).as_posix().rstrip("/")
                scopes.append((lane["id"], scope))

        for index, (lane_a, path_a) in enumerate(scopes):
            for lane_b, path_b in scopes[index + 1 :]:
                if lane_a == lane_b:
                    continue
                self.assertFalse(
                    path_a == path_b or path_a.startswith(path_b + "/") or path_b.startswith(path_a + "/"),
                    f"owned project paths overlap: {lane_a}:{path_a} and {lane_b}:{path_b}",
                )

    def test_handoff_contract_has_reproducibility_and_scope_fields(self):
        self.assertEqual("object", self.handoff["type"])
        self.assertIn("snapshot", self.handoff["properties"])
        self.assertIn("scope", self.handoff["properties"])
        self.assertIn("verification", self.handoff["properties"])
        self.assertIn("review", self.handoff["properties"])
        self.assertIn("worktree_before", self.handoff["properties"]["snapshot"]["required"])
        self.assertIn(
            "manifest_sha256",
            self.handoff["properties"]["snapshot"]["properties"]["worktree_before"]["required"],
        )
        self.assertIn("authorization_scope_ref", self.handoff["properties"]["scope"]["required"])
        self.assertIn("authorized_paths", self.handoff["properties"]["scope"]["required"])
        self.assertIn("external_writes", self.handoff["properties"]["verification"]["required"])
        self.assertIn(
            {"const": "1.0.0"},
            [self.handoff["properties"]["schema_version"]],
        )
        self.assertEqual(
            {"snapshot", "scope", "interfaces", "verification", "review"},
            set(self.handoff["required"]) & {"snapshot", "scope", "interfaces", "verification", "review"},
        )

    def test_lane_docs_define_readme_contract_review_and_tdd(self):
        for filename in ["README.md", "lane-iqs.md", "lane-stockqa.md", "lane-stockwiki.md", "lane-theme.md", "lane-industry.md", "review-protocol.md"]:
            body = (LANE_DIR / filename).read_text(encoding="utf-8")
            self.assertTrue(body.strip(), filename)
        master = (LANE_DIR / "README.md").read_text(encoding="utf-8")
        for required_phrase in ["TDD", "handoff.schema.json", "tasks.json", "G0—G6"]:
            self.assertIn(required_phrase, master)

    def test_local_markdown_links_resolve(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for document in LANE_DIR.glob("*.md"):
            body = document.read_text(encoding="utf-8")
            for target in link_pattern.findall(body):
                if target.startswith(("http://", "https://", "#")):
                    continue
                target_path = target.split("#", 1)[0]
                self.assertTrue((document.parent / target_path).exists(), f"{document.name}: {target}")


if __name__ == "__main__":
    unittest.main()
