"""Guard: repository code must not depend on private-runtime modules.

Incident (2026-09-22): a master convergence commit added a call-time
``from cron.jobs import parse_schedule`` inside
``operator_cron.hermes_cron_create``. ``cron`` exists only in the private
Hermes agent runtime installed on deployed boxes — it is not part of this
repository — so every clean install failed five ``test_operator_cron.py``
cron-create tests (all 9 CI test lanes red) while the deployed box stayed
green. The repair (rm-032) replaced the import with a repo-local parser port.

Rules enforced here, deterministically (no environment probing for rule 1):

1. No repository file may import ``cron`` (guarded or not, any depth). The
   deployed scheduler's contract is served by repo-local code only.
2. Any *module-level, unguarded* import in a shipped py-module (the
   ``py-modules`` list in ``pyproject.toml``) must resolve to a repo module, a
   stdlib module, or a module supplied by the declared dependency closure.
   Function-level imports in unshipped helper entry points are out of scope
   for rule 2 but still covered by rule 1.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Modules that exist only in the private Hermes agent runtime. Importing any
# of these from repository code breaks clean installs (the rm-032 incident).
PRIVATE_RUNTIME_MODULES = {"cron"}

# Dependency name -> import-name aliases (declared name is not the import name).
DEP_IMPORT_ALIASES = {"pyyaml": "yaml", "hermes-gpt": None}

# Distribution requirement lines look like "mcp[cli]>=1.28.1,<3 ; extra == 'cli'".
_DEP_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def _dep_name(requirement):
    match = _DEP_NAME_RE.match(requirement.strip())
    return match.group(1) if match else ""


def _iter_repo_python_files():
    yield from sorted(REPO_ROOT.glob("*.py"))
    tools = REPO_ROOT / "tools"
    if tools.is_dir():
        yield from sorted(tools.glob("*.py"))


def _top_level_imports(tree):
    """Yield (lineno, module_name) for every import statement in ``tree``."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                yield node.lineno, node.module.split(".")[0]


def test_no_private_runtime_module_imports():
    violations = []
    for path in _iter_repo_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno, name in _top_level_imports(tree):
            if name in PRIVATE_RUNTIME_MODULES:
                violations.append(f"{path.name}:{lineno}: imports {name!r}")
    assert not violations, (
        "Repository code must not import private Hermes runtime modules "
        f"({sorted(PRIVATE_RUNTIME_MODULES)}): they do not exist in clean "
        "installs and break CI. Offenders:\n" + "\n".join(violations)
    )


def _shipped_modules():
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10 lane
        import tomli as tomllib
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return list(data["tool"]["setuptools"]["py-modules"])


def _dependency_closure_import_names():
    """Import names provided by the declared dependency closure.

    Deterministic: built from pyproject declarations plus each installed
    distribution's ``requires`` metadata / ``top_level.txt``. Core
    dependencies (mcp, packaging, uvicorn, cryptography, pyyaml, tomli) are
    installed in every CI lane, so this resolves identically there.
    """
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10 lane
        import tomli as tomllib
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = [_dep_name(dep) for dep in data["project"]["dependencies"]]

    names = set()
    pending = []
    for dep in declared:
        raw = dep.split(" ")[0].strip()
        alias = DEP_IMPORT_ALIASES.get(raw.lower(), raw)
        if alias is None:
            continue
        names.add(alias)
        pending.append(raw)

    try:
        from importlib import metadata
    except ModuleNotFoundError:  # pragma: no cover
        return names

    seen = set(pending)
    while pending:
        pkg = pending.pop()
        try:
            dist = metadata.distribution(pkg)
        except metadata.PackageNotFoundError:
            continue
        top_level = dist.read_text("top_level.txt")
        if top_level:
            names.update(
                line.strip() for line in top_level.splitlines() if line.strip()
            )
        for req in dist.requires or []:
            raw = _dep_name(req)
            if not raw:
                continue
            alias = DEP_IMPORT_ALIASES.get(raw.lower(), raw)
            if alias and alias not in names:
                names.add(alias)
            if raw not in seen:
                seen.add(raw)
                # Only follow the runtime closure one distribution deep from
                # core deps; deeper levels are not imported at module level.
                if len(seen) <= 24:
                    pending.append(raw)
    return names


def _import_nodes(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node


def _module_level(node, parents):
    """True when the import sits at module/class level (not in a function)."""
    p = parents.get(node)
    while p is not None:
        if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return False
        p = parents.get(p)
    return True


def _guarded(node, parents):
    """True when the import is wrapped in a try/except ImportError guard."""

    def handler_ok(handler):
        t = handler.type
        if t is None:
            return True
        members = []
        if isinstance(t, ast.Name):
            members = [t.id]
        elif isinstance(t, ast.Tuple):
            members = [e.id for e in t.elts if isinstance(e, ast.Name)]
        elif isinstance(t, ast.Attribute):
            members = [t.attr]
        return any(
            m in ("ImportError", "ModuleNotFoundError", "Exception") for m in members
        )

    p = parents.get(node)
    while p is not None:
        if isinstance(p, ast.ExceptHandler) and handler_ok(p):
            return True
        if isinstance(p, ast.Try) and any(handler_ok(h) for h in p.handlers):
            return True
        p = parents.get(p)
    return False


def test_shipped_modules_module_level_imports_resolve():
    shipped = set(_shipped_modules())
    allowed = shipped | set(sys.stdlib_module_names) | _dependency_closure_import_names()
    allowed |= {"__future__"}

    violations = []
    for module in sorted(shipped):
        path = REPO_ROOT / f"{module}.py"
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        for node in _import_nodes(tree):
            if not _module_level(node, parents):
                continue
            if _guarded(node, parents):
                continue
            if isinstance(node, ast.Import):
                tops = [a.name.split(".")[0] for a in node.names]
            elif node.level == 0 and node.module:
                tops = [node.module.split(".")[0]]
            else:  # relative import
                continue
            unresolved = [t for t in tops if t not in allowed]
            if unresolved:
                violations.append(
                    f"{module}.py:{node.lineno}: unguarded module-level import of "
                    f"non-dependency module(s) {unresolved}"
                )
    assert not violations, (
        "Shipped modules must not import modules outside the repo, the "
        "standard library, or the declared dependency closure at module "
        "level without an ImportError guard (clean-install breakage; the "
        "rm-032 incident class). Offenders:\n" + "\n".join(violations)
    )
