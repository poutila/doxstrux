# map_reexports.py
import ast
import os

repo_root = os.path.dirname(__file__)
src_root = os.path.join(repo_root, "src")


def find_reexports(init_path):
    """Parse an __init__.py and return a list of re-exported names."""
    reexports = []
    try:
        with open(init_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=init_path)
    except (SyntaxError, UnicodeDecodeError):
        return reexports

    for node in tree.body:
        # Look for `from .something import X, Y`
        if isinstance(node, ast.ImportFrom):
            if node.level >= 1:  # relative import
                for alias in node.names:
                    reexports.append(alias.name)
        # Look for assignments to __all__
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Str):
                                reexports.append(elt.s)
    return reexports


print("🔍 Scanning for re-exports...\n")

for root, dirs, files in os.walk(src_root):
    if "__init__.py" in files:
        init_path = os.path.join(root, "__init__.py")
        reexports = find_reexports(init_path)
        if reexports:
            package = os.path.relpath(root, src_root).replace(os.sep, ".")
            print(f"{package} ({init_path}):")
            for name in reexports:
                print(f"  - {name}")
            print()
