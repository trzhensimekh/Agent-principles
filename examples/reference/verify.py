"""Run finite checks and bind their observed results to the measured inputs."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent


def fingerprint(root: Path = ROOT) -> tuple[dict[str, str], str]:
    hashes = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {"__pycache__", ".git"} for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink inputs are unsupported: {relative}")
        if path.suffix in {".pyc", ".pyo"} or not path.is_file():
            continue
        hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    canonical = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    return hashes, hashlib.sha256(canonical).hexdigest()


def git_observation() -> dict:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=10)
        status = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=ROOT,
                                capture_output=True, text=True, timeout=10)
        return {
            "observed_git_head": head.stdout.strip() if head.returncode == 0 else None,
            "working_tree_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        }
    except (OSError, subprocess.TimeoutExpired):
        return {"observed_git_head": None, "working_tree_dirty": None}


def run_checks() -> tuple[dict, int]:
    files_before, tree_before = fingerprint()
    observation_before = git_observation()
    # A fresh cache prefix prevents existing timestamp-based .pyc files from
    # making the executed code differ from the source bytes being hashed.
    with TemporaryDirectory(prefix="agent-check-cache-") as cache:
        command = [sys.executable, "-X", f"pycache_prefix={cache}", "-m", "tools.run_checks"]
        try:
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
            exit_code, stdout, stderr = process.returncode, process.stdout, process.stderr
        except subprocess.TimeoutExpired:
            exit_code, stdout, stderr = 124, "", "Verification exceeded its 60-second timeout."
    try:
        inventory = json.loads(stdout)
    except json.JSONDecodeError:
        inventory = None
    inventory_passed = (
        isinstance(inventory, dict) and inventory.get("result") == "pass"
        and bool(inventory.get("passed"))
        and inventory.get("required_checks_not_passed") == []
    )
    checks = [{
        "command": command,
        "exit_code": exit_code,
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "stdout": stdout,
        "stderr": stderr,
    }]
    files_after, tree_after = fingerprint()
    observation_after = git_observation()
    stable = tree_before == tree_after and observation_before == observation_after
    passed = exit_code == 0 and stable and inventory_passed
    receipt = {
        "schema_version": 1,
        "scope": "examples/reference",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_tree_sha256": tree_before,
        "files_sha256": files_before,
        **observation_before,
        "python_version": platform.python_version(),
        "checks": checks,
        "check_inventory": inventory,
        "inputs_stable_during_checks": stable,
        "post_check_input_tree_sha256": tree_after,
        "result": "pass" if passed else ("unstable-input" if not stable else "fail"),
        "limitations": [
            "An unsigned local observation, not a proof or independent attestation.",
            "Binds scoped files and the observed Git HEAD, including dirty working trees; does not claim the tree was committed.",
            "Pre/post comparison cannot detect inputs changed and restored during execution.",
            "Finite tests and static import checks do not establish complete correctness, security, or actual payment settlement.",
            "Python version is recorded; OS, dependency binaries, and the whole execution environment are not attested.",
        ],
    }
    return receipt, 0 if passed else 1


def check_receipt(path: Path) -> tuple[dict, int]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    files, tree = fingerprint()
    observation = git_observation()
    matches = (
        receipt.get("schema_version") == 1
        and receipt.get("result") == "pass"
        and receipt.get("inputs_stable_during_checks") is True
        and receipt.get("files_sha256") == files
        and receipt.get("input_tree_sha256") == tree
        and receipt.get("observed_git_head") == observation["observed_git_head"]
        and receipt.get("python_version") == platform.python_version()
    )
    return {
        "result": "matching-local-receipt" if matches else "stale-or-failed-receipt",
        "input_tree_sha256": tree,
        "note": "This compares an unsigned receipt with current files, HEAD, and Python version; it does not rerun or authenticate the recorded checks, or attest the full environment.",
    }, 0 if matches else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--receipt", type=Path, help="also write the JSON receipt outside the measured example tree")
    group.add_argument("--check-receipt", type=Path, help="compare an existing receipt with current files and HEAD")
    arguments = parser.parse_args()
    if arguments.receipt and arguments.receipt.resolve().is_relative_to(ROOT):
        parser.error("write receipts outside examples/reference so they do not change the measured inputs")
    if arguments.check_receipt:
        receipt, code = check_receipt(arguments.check_receipt)
    else:
        receipt, code = run_checks()
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if arguments.receipt:
        arguments.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
