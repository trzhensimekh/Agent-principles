#!/usr/bin/env python3
"""Recheck frozen source and acceptance outcomes; do not regenerate agent code."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
ARMS = ("inventory_x", "inventory_y", "pricing_x", "pricing_y")
PHASES = ("initial", "maintained")
SOURCES = {
    "guidance.md",
    "tasks/inventory-initial.md",
    "tasks/inventory-change.md",
    "tasks/pricing-initial.md",
    "tasks/pricing-change.md",
}
EVALUATOR_FILES = {"README.txt", "runner.py", "test_inventory.py", "test_pricing.py"}
TIMEOUT_SECONDS = 30


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def exact_set(actual: set[str], expected: set[str], label: str) -> None:
    require(
        actual == expected,
        f"{label}: missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}",
    )


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path.name}: expected a JSON object")
    return value


def read_manifest(path: Path) -> dict[str, str]:
    entries = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split(maxsplit=1)
        require(len(parts) == 2, f"{path.name}:{number}: malformed checksum entry")
        digest, name = parts
        require(name not in entries, f"{path.name}:{number}: duplicate entry {name}")
        entries[name] = digest
    return entries


def verify_hashes(base: Path, entries: dict[str, str]) -> None:
    for name, digest in entries.items():
        require(isinstance(name, str), "Checksum path must be a string")
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts,
                f"Invalid checksum path: {name}")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
                f"Invalid SHA-256 for {name}")
        path = base / relative
        require(path.is_file() and not path.is_symlink(), f"Missing regular file: {path}")
        require(path.resolve().is_relative_to(base.resolve()), f"Path escapes checksum root: {name}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == digest, f"SHA-256 mismatch: {path}")


def semantic_result(report: dict) -> dict:
    require(type(report.get("successful")) is bool, "Report lacks boolean successful")
    require(type(report.get("tests_run")) is int and report["tests_run"] > 0,
            "Report lacks a positive tests_run count")
    result = {"successful": report["successful"], "tests_run": report["tests_run"]}
    # Traceback paths and timing vary by machine. Compare failure identities and
    # skip reasons, preserving multiplicity, instead of diagnostic rendering.
    for field in ("failures", "errors", "skipped", "expected_failures"):
        entries = report.get(field)
        require(isinstance(entries, list), f"Report lacks list field {field}")
        values = []
        for entry in entries:
            require(isinstance(entry, dict) and isinstance(entry.get("test_id"), str),
                    f"Malformed {field} entry")
            if field == "skipped":
                require(isinstance(entry.get("reason"), str), "Skip entry lacks reason")
                values.append((entry["test_id"], entry["reason"]))
            else:
                values.append(entry["test_id"])
        result[field] = sorted(values)
    unexpected = report.get("unexpected_successes")
    require(isinstance(unexpected, list) and all(isinstance(x, str) for x in unexpected),
            "Report lacks valid unexpected_successes")
    result["unexpected_successes"] = sorted(unexpected)
    return result


def main() -> int:
    require(sys.version_info >= (3, 11), "Python 3.11 or later is required")
    sources = read_json(ROOT / "registration.json").get("source_hashes")
    require(isinstance(sources, dict), "registration.json lacks source_hashes")
    exact_set(set(sources), SOURCES, "Registered inputs")
    verify_hashes(ROOT, sources)

    evaluator = ROOT / "evaluator"
    evaluator_hashes = read_manifest(evaluator / "SHA256SUMS")
    exact_set(set(evaluator_hashes), EVALUATOR_FILES, "Evaluator manifest")
    exact_set({p.name for p in evaluator.iterdir()}, EVALUATOR_FILES | {"SHA256SUMS"},
              "Evaluator directory")
    verify_hashes(evaluator, evaluator_hashes)
    python_hashes = {name: digest for name, digest in evaluator_hashes.items()
                     if name.endswith(".py")}

    snapshot_dirs = {f"snapshots/{phase}/{arm}" for phase in PHASES for arm in ARMS}
    actual_dirs = {p.relative_to(ROOT).as_posix()
                   for p in (ROOT / "snapshots").rglob("*") if p.is_dir()}
    exact_set(actual_dirs, snapshot_dirs | {f"snapshots/{phase}" for phase in PHASES},
              "Eight snapshot directories and their two phase directories")
    snapshots = read_manifest(ROOT / "SNAPSHOT-SHA256SUMS")
    expected_snapshot_files = {
        f"{directory}/{name}"
        for directory in snapshot_dirs
        for name in ("README.md", f"{Path(directory).name.split('_')[0]}.py",
                     f"test_{Path(directory).name.split('_')[0]}.py")
    }
    exact_set(set(snapshots), expected_snapshot_files, "Snapshot manifest")
    exact_set({p.relative_to(ROOT).as_posix() for p in (ROOT / "snapshots").rglob("*")
               if p.is_file()}, expected_snapshot_files, "Snapshot files")
    verify_hashes(ROOT, snapshots)

    runs = []
    for phase in PHASES:
        for arm in ARMS:
            for stage in ((1,) if phase == "initial" else (1, 2)):
                suffix = "initial" if phase == "initial" else f"maintained-stage{stage}"
                runs.append((arm, phase, stage, f"{arm}-{suffix}.json"))
    results = ROOT / "results"
    exact_set({p.name for p in results.iterdir()}, {run[3] for run in runs},
              "Twelve committed result files")

    total = 0
    print("Frozen inputs, evaluator, and eight snapshots: SHA-256 verified")
    print(f"{'Candidate':<14} {'Snapshot':<11} {'Stage':>5} {'Tests':>6}  Result")
    with tempfile.TemporaryDirectory(prefix="agent-design-reproduce-") as temporary:
        for index, (arm, phase, stage, filename) in enumerate(runs):
            domain = arm.split("_")[0]
            snapshot = ROOT / "snapshots" / phase / arm
            expected = read_json(results / filename)
            expected_semantics = semantic_result(expected)
            require(expected.get("domain") == domain and expected.get("stage") == stage,
                    f"{filename}: committed domain/stage mismatch")
            require(expected.get("arm") == snapshot.relative_to(ROOT).as_posix(),
                    f"{filename}: committed snapshot path mismatch")
            require(expected.get("evaluator_sha256") == python_hashes,
                    f"{filename}: committed evaluator hashes mismatch")
            command = [sys.executable, "-I", "-X", f"pycache_prefix={temporary}/{index}",
                       str(evaluator / "runner.py"), "--domain", domain,
                       "--stage", str(stage), "--arm", str(snapshot)]
            try:
                completed = subprocess.run(command, cwd=temporary, capture_output=True,
                                           text=True, timeout=TIMEOUT_SECONDS, check=False)
            except subprocess.TimeoutExpired as exc:
                raise ValueError(f"{filename}: evaluator exceeded {TIMEOUT_SECONDS}s timeout") from exc
            require(completed.returncode in (0, 1),
                    f"{filename}: unexpected evaluator exit {completed.returncode}: {completed.stderr}")
            actual = json.loads(completed.stdout)
            require(isinstance(actual, dict), f"{filename}: evaluator did not return a JSON object")
            require(actual.get("domain") == domain and actual.get("stage") == stage
                    and actual.get("arm") == str(snapshot), f"{filename}: evaluator target mismatch")
            require(actual.get("evaluator_sha256") == python_hashes,
                    f"{filename}: executed evaluator hashes mismatch")
            actual_semantics = semantic_result(actual)
            require(completed.returncode == (0 if actual["successful"] else 1),
                    f"{filename}: exit status disagrees with successful field")
            for field, value in expected_semantics.items():
                require(actual_semantics[field] == value,
                        f"{filename}: {field} mismatch: expected {value!r}, got {actual_semantics[field]!r}")
            total += actual["tests_run"]
            print(f"{arm:<14} {phase:<11} {stage:>5} {actual['tests_run']:>6}  MATCH")

    # Candidate code executes locally; verify it did not alter frozen inputs.
    verify_hashes(ROOT, sources)
    verify_hashes(evaluator, evaluator_hashes)
    verify_hashes(ROOT, snapshots)
    print(f"All 12 reports reproduced ({total} test-method executions; stages overlap).")
    print("This rechecks committed code, not agent generation. Durations are not benchmarked.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"Reproduction failed: {error}", file=sys.stderr)
        raise SystemExit(1)
