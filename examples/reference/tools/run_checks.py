"""Run tests and require an observed success for every manifest-declared check."""

import json
import sys
import unittest

from .contracts import ROOT, graph_violations, validate_manifest
from .preflight import check_suite


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.started_ids = []
        self.passed_ids = []
        self.skipped_owner_ids = set()

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)

    def addSkip(self, test, reason):
        # A skipped subtest leaves its parent incomplete even if unittest later
        # reports the enclosing method as successful.
        owner = getattr(test, "test_case", test)
        self.skipped_owner_ids.add(owner.id())
        super().addSkip(test, reason)


def main() -> None:
    manifest = validate_manifest()
    violations = graph_violations(ROOT, manifest)
    if violations:
        raise ValueError("; ".join(violations))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    discovered = check_suite(manifest, suite)
    required = {check for task in manifest["tasks"].values()
                for invariant in task["invariants"] for check in invariant["checks"]}
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=EvidenceResult)
    result = runner.run(suite)
    not_passed = sorted((required - set(result.passed_ids)) | (required & result.skipped_owner_ids))
    passed = result.wasSuccessful() and not not_passed
    report = {
        "result": "pass" if passed else "fail",
        "discovered": sorted(discovered),
        "started": result.started_ids,
        "passed": result.passed_ids,
        "skipped": [{"check": test.id(), "reason": reason} for test, reason in result.skipped],
        "failed": [test.id() for test, _ in result.failures],
        "errors": [test.id() for test, _ in result.errors],
        "expected_failures": [test.id() for test, _ in result.expectedFailures],
        "required_checks_not_passed": not_passed,
    }
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
