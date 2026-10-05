"""Architectural checks are constraints, not proofs of arbitrary behavior."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.contracts import ROOT, graph_violations, validate_manifest


class ArchitectureTests(unittest.TestCase):
    def test_contract_targets_exist(self):
        self.assertEqual(validate_manifest()["system"], "refund-request-ledger")

    def test_declared_graph(self):
        self.assertEqual(graph_violations(), [])

    def test_forbidden_import_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "refunds", root / "refunds")
            path = root / "refunds" / "domain.py"
            path.write_text(path.read_text() + "\nimport sqlite3\n")
            self.assertIn("forbidden import: refunds.domain -> sqlite3",
                          graph_violations(root, validate_manifest()))

    def test_dangling_owner_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "refunds", root / "refunds")
            manifest = validate_manifest()
            manifest["tasks"]["refund-window"]["owner"] = "refunds/domain.py:missing_rule"
            (root / "contract.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "missing symbol"):
                validate_manifest(root)


if __name__ == "__main__":
    unittest.main()
