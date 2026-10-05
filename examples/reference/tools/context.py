"""Return a task's declared context and navigation targets as JSON."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.contracts import ROOT, validate_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="task ID from contract.json")
    arguments = parser.parse_args()
    manifest = validate_manifest()
    if arguments.task not in manifest["tasks"]:
        parser.error("unknown task; choose " + ", ".join(manifest["tasks"]))
    task = manifest["tasks"][arguments.task]
    result = {
        "task_id": arguments.task,
        "task": task,
        "files": [{"path": path, "lines": len((ROOT / path).read_text().splitlines())}
                  for path in task["context"]],
        "effects": {effect: manifest["effects"][effect] for effect in task["effects"]},
        "bindings": manifest["bindings"],
        "note": "Declared starting context. Expand along explicit references when the task requires it. Line counts are not token counts or a completeness guarantee.",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
