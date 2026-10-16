# Reproducing the independent acceptance checks

The archived records preserve the actual argv, cwd, UTC start/end, exit status, and raw stdout/stderr hashes. Relative stdout/stderr references are retained at their original relative paths inside each case archive. Absolute cwd/argv paths describe the executed review environment, not a new path to write on another machine.

Only reports, exact CAS bytes/checks, guards, minimal counterexamples, and test evidence are selected. Complete duplicate source trees and frozen input files are intentionally excluded. Reproduction requires the reviewed package commit/CAS and the original published frozen input subset, whose raw SHA is recorded in the review.

Use a new writable scratch area. Reconstruct the reviewed package into the tester's expected `catl2/`, `csc2/`, or final `desk3/` directory, or adjust those explicit local paths in a copy of the harness. Never run the guard or suite in an original read-only package or against live inputs. The original tests are in the reviewed package; the small probe scripts import their fixture helpers. Run with `C:/Miniconda/python.exe -B -X utf8`, a minimal environment, explicit TEMP/TMP under scratch, and the archived guard. Browser checks use the existing offline Chromium installation and route blocking. No dependency download, API/key, private/DB/T4 source is required.

Review status concerns engineering/material-contract acceptance for this fixed frozen snapshot. It does not grant financial qualification, production readiness, a rating, whole-question sufficiency, or web authenticity.
