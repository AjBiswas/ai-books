"""Book 1, Chapter 40 lab (part 1): map a codebase with static and dynamic analysis.

Target: the Python harness from Book 2 (code/harness). Static analysis reads the code without
running it, through Python's AST: which module imports which (a dependency graph), how big each
function is, and a few smells. Dynamic analysis runs the tests and watches what happens.
This is what a coding agent does before it touches a brownfield codebase.
Run from the repo root:  python code2/ch40/code_map.py
"""
import ast
import pathlib
import subprocess
import sys
import time

PKG = pathlib.Path("code/harness")
modules = {p.stem: ast.parse(p.read_text(encoding="utf-8")) for p in sorted(PKG.glob("*.py")) if p.stem != "__init__"}

print("1) dependency graph (who imports whom inside the package)")
deps = {}
for name, tree in modules.items():
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            found.add(node.module.split(".")[0])
    deps[name] = sorted(found & set(modules))
for name, ds in deps.items():
    print(f"   {name:10} -> {', '.join(ds) if ds else '(nothing)'}")
used_by = {m: [n for n, ds in deps.items() if m in ds] for m in modules}
hub = max(used_by, key=lambda m: len(used_by[m]))
print(f"   most depended-on: {hub} (used by {len(used_by[hub])} modules) -> change it with care")

print("\n2) size and shape")
funcs = []
for name, tree in modules.items():
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append((node.end_lineno - node.lineno + 1, f"{name}.{node.name}"))
funcs.sort(reverse=True)
print(f"   {len(modules)} modules, {len(funcs)} functions; longest: " + ", ".join(f"{f} ({n} lines)" for n, f in funcs[:3]))

print("\n3) smells found by static checks")
smells = 0
for name, tree in modules.items():
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            print(f"   {name}.py:{node.lineno}  bare 'except:' hides every error"); smells += 1
        if isinstance(node, ast.Import):
            for a in node.names:
                imported[(a.asname or a.name).split(".")[0]] = node.lineno
        if isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for a in node.names:
                imported[a.asname or a.name] = node.lineno
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.value.id for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    src = ast.unparse(tree)
    for imp, line in imported.items():
        if imp not in names and src.count(imp) <= 1:
            print(f"   {name}.py:{line}  import '{imp}' is never used"); smells += 1
if not smells:
    print("   none")

print("\n4) dynamic analysis: run the test suite")
t0 = time.perf_counter()
r = subprocess.run([sys.executable, "-m", "pytest", "-q", "code/tests"], capture_output=True, text=True)
print("   " + r.stdout.strip().splitlines()[-1] + f"   ({time.perf_counter() - t0:.1f}s wall)")
