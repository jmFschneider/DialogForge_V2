"""`dialogforge new --cadrer-avec-agent` : le cadrage avec agent F en terminal
(`conception/CADRAGE_AGENT.md` §2, §3).

Ordre du §3.2 : tous les refus déterministes — création, adaptateur de F, sources —
passent **avant** la session et le premier appel. La collaboration n'est créée
qu'après la relecture humaine du brouillon ; `Ctrl+C`, fin d'entrée ou `/annuler`
ferment la session, détruisent le dossier jetable et ne créent rien.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from . import facade, framing, settings
from .adapters.base import AgentAdapter, FramingSessionSpec
from .demande import validate_framed
from .framing import DRAFT, QUESTION, READY, Framing, Turn

_END = "(terminez par une ligne contenant uniquement un point)"


def run(
    args: argparse.Namespace, base: facade.CreationRequest,
    adapters: Mapping[str, AgentAdapter],
) -> int:
    try:
        facade.check_creation(base, adapters=adapters)
        model, _ = framing.check_adapter(
            args.agent_cadrage, adapters, args.model_cadrage, args.effort_cadrage
        )
        timeout = settings.resolve_timeout(args.config, None).seconds
        root = framing.prepare(
            base.kind, base.source_root, base.source_list, base.source_label, base.web_access,
        )
    except (facade.CreationError, framing.FramingError, settings.SettingsError) as exc:
        return _fail(str(exc))
    try:
        idea = _block("Décrivez votre idée, même incomplète.")
    except (EOFError, KeyboardInterrupt):
        shutil.rmtree(root, ignore_errors=True)
        return _fail("cadrage interrompu : rien n'a été créé")
    spec = FramingSessionSpec(model, timeout, root / "travail", args.effort_cadrage)
    others = [a.env for key, a in adapters.items() if key != args.agent_cadrage]
    session = framing.open_session(adapters[args.agent_cadrage], spec, others=others)
    f = Framing(session, root, idea)
    try:
        return _converse(f, base, adapters)
    except (EOFError, KeyboardInterrupt, framing.FramingError) as exc:
        f.discard()
        detail = f" ({exc})" if isinstance(exc, framing.FramingError) else ""
        return _fail(f"cadrage interrompu{detail} : rien n'a été créé")


def _converse(
    f: Framing, base: facade.CreationRequest, adapters: Mapping[str, AgentAdapter]
) -> int:
    print("\nF lit les sources et prépare sa première question…")
    turn = f.start()
    while True:
        _show(turn)
        kind = None if turn.problem is not None or turn.reply is None else turn.reply.kind
        if kind is None:
            choice = _choose("[r] Relancer  [c] Clore et rédiger  [a] Annuler", "rca")
            if choice == "a":
                return _cancel(f)
            turn = f.retry() if choice == "r" else f.write_draft()
        elif kind == QUESTION:
            text = _block("Votre réponse (/clore pour rédiger, /annuler pour abandonner).")
            if text == "/annuler":
                return _cancel(f)
            if text != "/clore":
                turn = f.answer(text)
            elif _choose("Clore le cadrage et demander la rédaction ? [o/n]", "on") == "o":
                f.note("Décision", "clôture demandée par l'utilisateur")
                turn = f.write_draft()
        elif kind == READY:
            choice = _choose(
                "[c] Continuer  [p] Corriger un point  [r] Rédiger le brouillon  [a] Annuler",
                "cpra",
            )
            if choice == "a":
                return _cancel(f)
            if choice == "r":
                f.note("Décision", "proposition de clôture acceptée")
                turn = f.write_draft()
            else:
                what = "Votre correction." if choice == "p" else "Votre réponse."
                turn = f.reopen(_block(what), correction=choice == "p")
        else:
            assert kind == DRAFT
            outcome = _review(f, base, adapters)
            if isinstance(outcome, int):
                return outcome
            turn = outcome


def _review(
    f: Framing, base: facade.CreationRequest, adapters: Mapping[str, AgentAdapter]
) -> int | Turn:
    """Relecture avant création (§2.6) : le texte validé devient `demande.md`, et ses
    empreintes initiales sont celles du texte relu."""
    assert f.draft is not None
    text = f.draft
    while True:
        print(f"\nBrouillon prêt.\n\n{text}")
        choice = _choose(
            "[v] Valider et créer  [m] Modifier le texte  [c] Continuer le cadrage  [a] Annuler",
            "vmca",
        )
        if choice == "a":
            return _cancel(f)
        if choice == "c":
            return f.reopen(_block("Ce qu'il faut encore cadrer."), correction=False)
        if choice == "m":
            edited = _block("Texte complet de la demande, qui remplace le brouillon.") + "\n"
            problems = validate_framed(edited)
            if problems:
                print("Texte refusé : " + " ; ".join(problems), file=sys.stderr)
            else:
                text = edited
            continue
        f.note("Décision", "brouillon validé" + (" après modification" if text != f.draft else ""))
        request = replace(
            base, demande=facade.DemandeSource(text, "cadrage"), framing=f.artifacts(),
            source_root=None, source_list=None, source_label=None,
        )
        try:
            result = facade.create_collaboration(request, adapters=adapters)
        except facade.CreationError as exc:
            print(f"erreur : {exc}", file=sys.stderr)
            continue
        f.discard()
        print(f"collaboration creee : {result.path}\ndemande : {Path(result.path, 'demande.md')}")
        return 0


def _show(turn: Turn) -> None:
    if turn.problem is not None or (turn.reply is not None and turn.reply.kind != DRAFT):
        print("\n" + framing.shown(turn))


def _block(prompt: str) -> str:
    """Texte libre sur plusieurs lignes, jusqu'à une ligne `.` ; vide, il est redemandé."""
    while True:
        print(f"\n{prompt}\n{_END}")
        lines: list[str] = []
        while (line := input("> ")).strip() != ".":
            lines.append(line.rstrip())
        text = "\n".join(lines).strip()
        if text:
            return text


def _choose(menu: str, keys: str) -> str:
    while (choice := input(f"\n{menu} > ").strip().lower()) not in set(keys):
        pass
    return choice


def _cancel(f: Framing) -> int:
    f.discard()
    print("cadrage annulé : rien n'a été créé")
    return 1


def _fail(message: str) -> int:
    print(f"erreur : {message}", file=sys.stderr)
    return 1
