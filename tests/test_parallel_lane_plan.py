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

    def test_independent_packages_match_owner_dependencies_and_disjoint_write_scopes(self):
        package_dir = LANE_DIR / "packages"
        catalog = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
        task_by_id = {task["id"]: task for task in self.tasks["tasks"]}
        lane_by_id = {lane["id"]: lane for lane in self.manifest["lanes"]}
        packages = catalog["packages"]
        self.assertEqual({"QA-04", "SW-IDENT", "TH-01", "IN-02"}, {p["id"] for p in packages})
        assigned = []
        scopes = []
        for package in packages:
            body = (package_dir / package["document"]).read_text(encoding="utf-8")
            self.assertIn(package["id"], body)
            self.assertIn("TDD", body)
            self.assertTrue(package["task_ids"])
            self.assertIn(package["lane_id"], lane_by_id)
            scope = PurePosixPath(package["write_scope"].casefold()).as_posix().rstrip("/")
            scopes.append((package["id"], scope))
            for task_id in package["task_ids"]:
                self.assertEqual(package["lane_id"], task_by_id[task_id]["owner"])
                assigned.append(task_id)
            self.assertEqual(
                set(package["depends_on"]),
                set().union(*(task_by_id[task_id]["depends_on"] for task_id in package["task_ids"]))
                - set(package["task_ids"]),
            )
        self.assertEqual(len(assigned), len(set(assigned)))
        for index, (first_id, first_path) in enumerate(scopes):
            for second_id, second_path in scopes[index + 1 :]:
                self.assertFalse(
                    first_path == second_path
                    or first_path.startswith(second_path + "/")
                    or second_path.startswith(first_path + "/"),
                    f"package write scopes overlap: {first_id}/{second_id}",
                )

    def test_package_links_and_readiness_gates(self):
        package_dir = LANE_DIR / "packages"
        catalog = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("1.0.0", catalog["format_version"])
        self.assertEqual(2, sum(p["readiness"].startswith("read_only") for p in catalog["packages"]))
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for document in [LANE_DIR / "README.md", *package_dir.glob("*.md")]:
            for target in link_pattern.findall(document.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target.split("#", 1)[0]).exists(), f"{document.name}: {target}")


if __name__ == "__main__":
    unittest.main()
