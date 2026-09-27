"""Mesure reproductible des lignes de code effectif dans src/ contre HEAD."""

from __future__ import annotations

import ast
import io
import subprocess
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
IGNORED = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
           tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING}


def count(data: bytes) -> int:
    source = data.decode("utf-8-sig")
    tree = ast.parse(source)
    docstrings: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and (
                isinstance(first.value.value, str)
            ):
                docstrings.add((first.value.lineno, first.value.end_lineno))
    lines: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in IGNORED or token.type == tokenize.STRING and (
            token.start[0], token.end[0]
        ) in docstrings:
            continue
        lines.update(range(token.start[0], token.end[0] + 1))
    return len(lines)


def main() -> None:
    current = {p.relative_to(ROOT).as_posix(): count(p.read_bytes())
               for p in SRC.rglob("*.py")}
    tracked = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-tree", "-r", "--name-only",
         "HEAD", "src"], cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode().splitlines()
    baseline = {}
    for name in tracked:
        data = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "show", f"HEAD:{name}"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
        baseline[name] = count(data)
    print(f"HEAD: {sum(baseline.values())}")
    print(f"Actuel: {sum(current.values())}")
    print(f"Ajout net: {sum(current.values()) - sum(baseline.values())}")
    for name in sorted(current.keys() | baseline.keys()):
        delta = current.get(name, 0) - baseline.get(name, 0)
        if delta:
            print(f"{delta:+} {name}")


if __name__ == "__main__":
    main()
