"""Introduce known faults in disposable copies and require targeted rejection."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from verify import ROOT, fingerprint


CONTROLS = [
    {
        "id": "inclusive-window-boundary",
        "file": "refunds/domain.py",
        "before": "elapsed < REFUND_WINDOW",
        "after": "elapsed <= REFUND_WINDOW",
        "test": "tests.test_refunds.PolicyTests.test_window_boundaries",
        "expected_failure": "Ineligible not raised",
    },
    {
        "id": "domain-depends-on-storage",
        "file": "refunds/domain.py",
        "before": "from dataclasses import dataclass",
        "after": "import sqlite3\nfrom dataclasses import dataclass",
        "test": "tests.test_architecture.ArchitectureTests.test_declared_graph",
        "expected_failure": "forbidden import: refunds.domain -> sqlite3",
    },
    {
        "id": "dangling-policy-owner",
        "file": "contract.json",
        "before": '"owner": "refunds/domain.py:approve"',
        "after": '"owner": "refunds/domain.py:missing_rule"',
        "test": "tests.test_architecture.ArchitectureTests.test_contract_targets_exist",
        "expected_failure": "missing symbol: refunds/domain.py:missing_rule",
    },
    {
        "id": "commit-before-outbox",
        "file": "refunds/sqlite_ledger.py",
        "before": "            payload = json.dumps({",
        "after": "            self.connection.commit()\n            payload = json.dumps({",
        "test": "tests.test_refunds.LedgerContractTests.test_outbox_failure_rolls_back_request",
        "expected_failure": "is not None",
    },
    {
        "id": "undiscovered-policy-tests",
        "file": "tests/test_refunds.py",
        "before": "class PolicyTests(unittest.TestCase):",
        "after": "class PolicyTests:",
        "command": ["-m", "tools.run_checks"],
        "expected_failure": "declared checks not discovered",
    },
    {
        "id": "skipped-policy-tests",
        "file": "tests/test_refunds.py",
        "before": "class PolicyTests(unittest.TestCase):",
        "after": '@unittest.skip("injected missing evidence")\nclass PolicyTests(unittest.TestCase):',
        "command": ["-m", "tools.run_checks"],
        "expected_failure": "required_checks_not_passed",
    },
    {
        "id": "source-changed-with-stale-bytecode",
        "file": "refunds/domain.py",
        "before": "REFUND_WINDOW = timedelta(days=30)",
        "after": "REFUND_WINDOW = timedelta(days=60)",
        "command": ["verify.py"],
        "prime_module": "refunds.domain",
        "preserve_timestamp": True,
        "expected_failure": "Ineligible not raised",
    },
]


def main() -> None:
    _, live_before = fingerprint()
    reports = []
    for control in CONTROLS:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "reference"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
            arguments = control["command"] if "command" in control else ["-m", "unittest", control["test"], "-v"]
            command = [sys.executable] + arguments
            baseline = subprocess.run(command, cwd=copied, capture_output=True, text=True, timeout=30)
            if baseline.returncode:
                raise RuntimeError(f"baseline failed for {control['id']}: {baseline.stderr}")
            if "prime_module" in control:
                subprocess.run([sys.executable, "-c", "import " + control["prime_module"]],
                               cwd=copied, check=True, capture_output=True, text=True, timeout=30)
            path = copied / control["file"]
            before_stat = path.stat()
            text = path.read_text(encoding="utf-8")
            if text.count(control["before"]) != 1:
                raise ValueError(f"expected exactly one mutation target: {control['id']}")
            path.write_text(text.replace(control["before"], control["after"]), encoding="utf-8")
            if control.get("preserve_timestamp"):
                os.utime(path, ns=(before_stat.st_atime_ns, before_stat.st_mtime_ns))
            else:
                # Most controls test a rule directly; the final control specifically
                # retains stale bytecode to check verifier source identity.
                for cache in copied.rglob("__pycache__"):
                    shutil.rmtree(cache)
            mutated = subprocess.run(command, cwd=copied, capture_output=True, text=True, timeout=30)
            rejected = mutated.returncode != 0 and control["expected_failure"] in (mutated.stderr + mutated.stdout)
            reports.append({"control": control["id"], "baseline_passed": True,
                            "mutant_exit_code": mutated.returncode,
                            "expected_reason_observed": rejected})
    _, live_after = fingerprint()
    passed = all(report["expected_reason_observed"] for report in reports) and live_before == live_after
    print(json.dumps({"result": "pass" if passed else "fail", "controls": reports,
                      "live_sources_unchanged": live_before == live_after,
                      "input_tree_sha256": live_before,
                      "note": "Targeted controls test checker sensitivity. This is not exhaustive mutation coverage."}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
