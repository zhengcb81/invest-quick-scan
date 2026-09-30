"""Reproduce S06 first-segment green suite or five assertion-killing mutants.

All generated test data goes into a unique TEMP/CWD, then is removed. This
runner never invokes a model/provider. The invoking shell may tee stdout into
the review directory. Mutants use in-memory mocks; production code is untouched.
"""
import contextlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import re
import subprocess


ROOT = Path(__file__).resolve().parents[4]
mode = sys.argv[1] if len(sys.argv) > 1 else "green"
if mode not in {"green", "mutants", "junction", "security", "regression", "integration", "full"}:
    raise SystemExit("expected green, mutants, junction, security, regression, integration or full")


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


with tempfile.TemporaryDirectory(prefix="iqs-s06-isolated-") as task_temp:
    isolated = Path(task_temp).resolve()
    os.environ["TEMP"] = os.environ["TMP"] = str(isolated)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    tempfile.tempdir = str(isolated)
    os.chdir(isolated)

    def allowed(path):
        if isinstance(path, (str, bytes, os.PathLike)):
            if not Path(os.fsdecode(path)).resolve().is_relative_to(isolated):
                raise RuntimeError("mutation outside isolated TEMP: " + str(path))

    def audit(event, args):
        if event.startswith("socket.") or event == "os.system":
            raise RuntimeError("offline test denies " + event)
        if event == 'subprocess.Popen':
            # The regression suite and dedicated junction mode use one reviewed
            # TEMP-only directory-junction fixture. Full adds two more offline
            # child-process fixtures: child ownership and a relative TEMP write.
            executable, argv, cwd, _ = args
            command = subprocess.list2cmdline(argv) if isinstance(argv, (list, tuple)) else argv
            scripts = ('import time; time.sleep(60)',
                       "from pathlib import Path; Path('relative-output.txt').write_text('isolated', encoding='utf-8')")
            expected = {subprocess.list2cmdline([sys.executable, '-c', code]) for code in scripts}
            junction = re.fullmatch(r'cmd\.exe /c mklink /J (\S+) (\S+)', command, flags=re.IGNORECASE)
            reviewed_fixture = mode == 'full' and command in expected
            reviewed_junction = mode in {'junction', 'regression', 'full'} and junction is not None
            if not (reviewed_fixture or reviewed_junction):
                raise RuntimeError('offline test denies unreviewed child: ' + command)
            allowed(cwd if cwd else Path.cwd())
            if junction:
                allowed(junction[1]); allowed(junction[2])
            print('ALLOW_REVIEWED_OFFLINE_CHILD', 'junction' if junction else 'python_fixture', flush=True)
        if event == "open" and isinstance(args[2], int):
            if args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                # subprocess.DEVNULL uses the OS null device, not a stored file.
                if not isinstance(args[0], str) or args[0].lower() != os.devnull.lower():
                    allowed(args[0])
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "shutil.rmtree"}:
            allowed(args[0])
        if event in {"os.rename", "os.link", "os.symlink"}:
            allowed(args[0]); allowed(args[1])

    sys.addaudithook(audit)
    module = load("test_routing")
    print("MODE", mode, "NETWORK_DENIED", True, "WRITES_TEMP_ONLY", True,
          "REVIEWED_SANDBOX_CHILDREN_ONLY", mode == 'full',
          "REVIEWED_JUNCTION_ONLY", mode in {'junction', 'regression'}, flush=True)
    if mode in {"green", "regression", "integration", "full", "junction", "security"}:
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        if mode == "security":
            suite = unittest.TestSuite([
                module.RouteSchemaTests("test_router_21_schema_rejects_router_22_confidence_field"),
                module.RoutingTests("test_mod19_a09_policy_versions_and_confidence_threshold_are_exact"),
                module.RoutingTests("test_mod19_v23_execution_receipt_requires_hash_of_parsed_native_answer"),
                module.RoutingTests("test_mod19_stockqa_public_result_adapter_binds_answer_and_execution_receipt"),
                module.RoutingTests("test_mod19_previous_router_policy_requires_explicit_migration"),
                module.RoutingTests("test_mod19_previous_route_requires_independent_id_before_hysteresis"),
                module.RoutingTests("test_mod19_rejects_answer_from_another_execution_attempt"),
            ])
            adapter_tests = load("test_stockqa_adapter")
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(adapter_tests))
        elif mode == "junction":
            registry_tests = load("test_module_registry")
            suite = unittest.TestSuite([registry_tests.ModuleRegistryTests(
                "test_release_and_catalog_paths_reject_parent_directory_symlinks")])
        elif mode == "regression":
            for name in ("test_module_contract", "test_module_registry", "test_standard_answers"):
                suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(name)))
        elif mode == "integration":
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(load('test_question_sets').RouteCompositionTests)
        elif mode == "full":
            suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        ok = result.wasSuccessful() and not result.skipped
        print("RESULT", result.testsRun, "failures", len(result.failures), "errors", len(result.errors),
              "skipped", len(result.skipped), flush=True)
    else:
        router = module.routing
        original = router.resolve_route_decision

        def mutate_order(inputs, **kwargs):
            result = original(inputs, **kwargs)
            if inputs.get("verified_facts", [{}])[0].get("module_id") == "scaling":
                result["module_decisions"].reverse()
            return result

        def price_means_cycle(inputs, **kwargs):
            import copy
            inputs = copy.deepcopy(inputs)
            for fact in inputs.get("verified_facts", []):
                if fact["evidence_type"] == "price_decline":
                    fact["evidence_type"] = "business_cycle"
            return original(inputs, **kwargs)

        def truncate_industries(inputs, **kwargs):
            result = original(inputs, **kwargs)
            result["profile_context"]["industry_modules"] = result["profile_context"]["industry_modules"][:2]
            return result

        mutants = [
            ("T1_input_order_leaks", "test_t1_semiconductor_scaling_is_deterministic_and_dual_listing_one_entity",
             "resolve_route_decision", mutate_order),
            ("T2_price_is_cycle", "test_t2_mature_cycle_trough_preserves_stage_and_adds_recovery",
             "resolve_route_decision", price_means_cycle),
            ("T3_budget_drops_risk", "test_t3_distressed_scaling_six_mandatory_questions_budget_and_manual_veto",
             "enforce_route_budget", lambda decision, maximum: maximum),
            ("T4_truncate_to_two", "test_t4_three_material_industries_do_not_truncate_and_full_needs_scope",
             "resolve_route_decision", truncate_industries),
            ("T5_history_clock_for_execution", "test_t5_override_expiry_blocks_execution_but_history_remains_readable",
             "validate_route_for_execution", lambda decision, **kwargs: decision),
        ]
        ok = True
        for label, case, name, bad in mutants:
            print("IN_MEMORY_MUTANT", label, flush=True)
            with mock.patch.object(router, name, bad):
                result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite([module.RoutingTests(case)]))
            killed = len(result.failures) > 0 and not result.errors and result.testsRun == 1
            print("EXPECTED_ASSERTION_RED", label, killed, flush=True)
            ok = ok and killed
    os.chdir(ROOT)
print("TEMP_CLEANED", not isolated.exists(), flush=True)
sys.exit(0 if ok else 1)
