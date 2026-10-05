"""Check manifest references and a deliberately limited static import graph."""

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"missing or out-of-scope file: {value}")
    return path


def symbol_exists(root: Path, target: str) -> None:
    filename, separator, qualified_name = target.partition(":")
    if not separator or not qualified_name:
        raise ValueError(f"expected path:symbol: {target}")
    tree = ast.parse(source_path(root, filename).read_text(encoding="utf-8"))
    body = tree.body
    for name in qualified_name.split("."):
        node = next((node for node in body if isinstance(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name == name), None)
        if node is None:
            raise ValueError(f"missing symbol: {target}")
        body = node.body


def check_test_target(root: Path, selector: str) -> None:
    parts = selector.split(".")
    if len(parts) != 4 or parts[0] != "tests" or not parts[-1].startswith("test_"):
        raise ValueError(f"expected tests.module.Class.test_method: {selector}")
    symbol_exists(root, "/".join(parts[:2]) + ".py:" + ".".join(parts[2:]))


def validate_manifest(root: Path = ROOT) -> dict:
    manifest = json.loads((root / "contract.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported contract schema_version")
    if not manifest.get("tasks") or not manifest.get("effects"):
        raise ValueError("tasks and effects must be nonempty")
    for task_id, task in manifest["tasks"].items():
        for field in ("entrypoint", "owner"):
            symbol_exists(root, task[field])
        for field in ("context", "change_scope"):
            if not task[field] or len(task[field]) != len(set(task[field])):
                raise ValueError(f"{task_id}: {field} must be nonempty and unique")
            for filename in task[field]:
                source_path(root, filename)
        owner_file = task["owner"].partition(":")[0]
        if owner_file not in task["context"] or owner_file not in task["change_scope"]:
            raise ValueError(f"{task_id}: owner must belong to context and change_scope")
        if task["entrypoint"].partition(":")[0] not in task["context"]:
            raise ValueError(f"{task_id}: entrypoint must belong to context")
        if not task["intent"] or not task["invariants"]:
            raise ValueError(f"{task_id}: intent and invariants are required")
        ids = [invariant["id"] for invariant in task["invariants"]]
        if len(set(ids)) != len(ids):
            raise ValueError(f"{task_id}: duplicate invariant ID")
        for invariant in task["invariants"]:
            if not invariant["claim"] or not invariant["checks"]:
                raise ValueError(f"{task_id}: each invariant needs a claim and checks")
            for check in invariant["checks"]:
                check_test_target(root, check)
        for effect in task["effects"]:
            if effect not in manifest["effects"]:
                raise ValueError(f"{task_id}: missing effect: {effect}")
    for effect in manifest["effects"].values():
        symbol_exists(root, effect["implementation"])
    for binding in manifest["bindings"]:
        for field in ("port", "implementation", "composition"):
            symbol_exists(root, binding[field])
    if not manifest.get("allowed_imports"):
        raise ValueError("allowed_imports must declare the production graph")
    return manifest


def imported_modules(node: ast.AST, module: str, is_package: bool) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if any(alias.name == "*" for alias in node.names):
        raise ValueError(f"wildcard import is not allowed in {module}")
    if node.level:
        package = module.split(".") if is_package else module.split(".")[:-1]
        if node.level > len(package):
            raise ValueError(f"relative import escapes package in {module}")
        base = package[:len(package) - node.level + 1]
        if node.module:
            return [".".join(base + node.module.split("."))]
        return [".".join(base + [alias.name]) for alias in node.names]
    return [node.module] if node.module else []


def graph_violations(root: Path = ROOT, manifest: dict | None = None) -> list[str]:
    manifest = manifest or validate_manifest(root)
    rules = manifest["allowed_imports"]
    violations = []
    seen_modules = set()
    for path in sorted((root / "refunds").rglob("*.py")):
        relative = path.relative_to(root).with_suffix("")
        is_package = path.name == "__init__.py"
        module = ".".join(relative.parts[:-1] if is_package else relative.parts)
        seen_modules.add(module)
        if module not in rules:
            violations.append(f"undeclared module: {module}")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            for dependency in imported_modules(node, module, is_package):
                if dependency not in rules[module]:
                    violations.append(f"forbidden import: {module} -> {dependency}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"__import__", "eval", "exec"}:
                    violations.append(f"dynamic execution is not allowed: {module}:{node.lineno}")
    for module in sorted(set(rules) - seen_modules):
        violations.append(f"manifest declares missing module: {module}")
    return violations
