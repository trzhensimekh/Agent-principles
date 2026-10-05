"""Reject broken manifest references, graph violations, and absent checks."""

import json
import unittest

from .contracts import ROOT, graph_violations, validate_manifest


def test_ids(suite) -> set[str]:
    found = set()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            found.update(test_ids(item))
        else:
            found.add(item.id())
    return found


def check_suite(manifest: dict, suite) -> set[str]:
    discovered = test_ids(suite)
    if not discovered:
        raise ValueError("no tests discovered")
    declared = {check for task in manifest["tasks"].values()
                for invariant in task["invariants"] for check in invariant["checks"]}
    missing = declared - discovered
    if missing:
        raise ValueError("declared checks not discovered: " + ", ".join(sorted(missing)))
    return discovered


def main() -> None:
    manifest = validate_manifest()
    violations = graph_violations(ROOT, manifest)
    if violations:
        raise ValueError("; ".join(violations))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    discovered = check_suite(manifest, suite)
    print(json.dumps({"result": "pass", "discovered_test_count": len(discovered),
                      "declared_checks_are_discovered": True}, sort_keys=True))


if __name__ == "__main__":
    main()
