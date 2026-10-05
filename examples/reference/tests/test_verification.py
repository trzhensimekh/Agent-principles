"""Receipts reject changed inputs and checks that did not pass."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify
from tools.preflight import check_suite


class ReceiptTests(unittest.TestCase):
    def test_symlink_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "inputs"
            root.mkdir()
            outside = Path(directory) / "external"
            outside.mkdir()
            (root / "linked").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink inputs are unsupported"):
                verify.fingerprint(root)

    def test_absent_tests_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "no tests discovered"):
            check_suite({"tasks": {}}, unittest.TestSuite())

    def test_changed_source_invalidates_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "inputs"
            root.mkdir()
            source = root / "policy.py"
            source.write_text("WINDOW_DAYS = 30\n")
            files, tree = verify.fingerprint(root)
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps({
                "schema_version": 1, "result": "pass",
                "inputs_stable_during_checks": True,
                "files_sha256": files, "input_tree_sha256": tree,
                "observed_git_head": "example-revision",
                "python_version": verify.platform.python_version(),
            }))
            original_fingerprint = verify.fingerprint
            with patch("verify.fingerprint", side_effect=lambda: original_fingerprint(root)), \
                 patch("verify.git_observation", return_value={"observed_git_head": "example-revision"}):
                self.assertEqual(verify.check_receipt(path)[1], 0)
                source.write_text("WINDOW_DAYS = 60\n")
                self.assertEqual(verify.check_receipt(path)[1], 1)

    def test_changed_revision_invalidates_receipt(self):
        files, tree = verify.fingerprint()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps({
                "schema_version": 1, "result": "pass",
                "inputs_stable_during_checks": True,
                "files_sha256": files, "input_tree_sha256": tree,
                "observed_git_head": "previous-revision",
                "python_version": verify.platform.python_version(),
            }))
            with patch("verify.git_observation", return_value={"observed_git_head": "new-revision"}):
                self.assertEqual(verify.check_receipt(path)[1], 1)

    def test_changed_inputs_during_checks_prevent_pass(self):
        observed = {"observed_git_head": None, "working_tree_dirty": None}
        with patch("verify.fingerprint", side_effect=[({"a.py": "before"}, "before"),
                                                      ({"a.py": "after"}, "after")]), \
             patch("verify.git_observation", return_value=observed), \
             patch("verify.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "OK")):
            receipt, code = verify.run_checks()
        self.assertEqual(code, 1)
        self.assertEqual(receipt["result"], "unstable-input")

    def test_failed_checks_prevent_pass(self):
        observed = {"observed_git_head": None, "working_tree_dirty": None}
        with patch("verify.fingerprint", return_value=({"a.py": "same"}, "same")), \
             patch("verify.git_observation", return_value=observed), \
             patch("verify.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "FAILED")):
            receipt, code = verify.run_checks()
        self.assertEqual(code, 1)
        self.assertEqual(receipt["result"], "fail")


if __name__ == "__main__":
    unittest.main()
