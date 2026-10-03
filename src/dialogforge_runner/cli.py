"""Entrée CLI du Runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import core


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dialogforge-run")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="préparer un clone indépendant et le mandat")
    prepare.add_argument("--export", type=Path, required=True)
    prepare.add_argument("--repo", type=Path, required=True)
    prepare.add_argument("--base", required=True)
    prepare.add_argument(
        "--checks", type=Path, required=True,
        help="fichier JSON des commandes de validation (listes d'arguments)",
    )
    prepare.add_argument("--validation-timeout", type=float, default=300)
    prepare.add_argument("--lot", type=Path)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--profile", choices=("local", "claude-wsl"), default="local")
    collect = commands.add_parser("collect", help="valider le candidat et créer un paquet")
    collect.add_argument("run", type=Path)
    launch = commands.add_parser("run-claude", help="lancer Claude dans Ubuntu WSL2")
    launch.add_argument("run", type=Path)
    launch.add_argument("--timeout", type=float, required=True)
    launch.add_argument("--continue", dest="continue_existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            checks = json.loads(args.checks.read_text(encoding="utf-8"))
            if not isinstance(checks, list) or not all(
                isinstance(command, list) and all(isinstance(arg, str) for arg in command)
                for command in checks
            ):
                raise ValueError("checks : liste de listes de chaînes attendue")
            core.prepare(args.export, args.repo, args.base, args.output,
                         validations=checks, validation_timeout=args.validation_timeout,
                         lot=args.lot, profile=args.profile)
            print(f"Dossier préparé : {args.output.resolve()}")
        elif args.command == "run-claude":
            package = core.run_claude(
                args.run, timeout_seconds=args.timeout,
                continue_existing=args.continue_existing,
            )
            print(f"Paquet créé : {package.resolve()}")
        else:
            print(f"Paquet créé : {core.collect(args.run).resolve()}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"dialogforge-run : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
