"""Surface CLI — neuf commandes (CONCEPTION_FINALE.md §7, étendue en V2 par 1.4, 2.3 et
la GUI V1, lots 3 et 4).

`new` obtient sa demande puis délègue la création à `facade.create_collaboration`
(§6.1, §6.5 : « validation autoritaire », partagée avec la GUI) ; `run` est l'unique
moteur synchrone ; `resume` n'en contient pas un second — il **transmet**
l'intervention humaine au moteur, qui l'applique sous le verrou, remet l'état dans
une phase admissible, puis enchaîne le cycle ; `status` est strictement en lecture
seule.

Aucune commande ne mute la collaboration hors du verrou : `resume` ne garde
que la validation de ses arguments (D-4).
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import (
    decisions,
    demande,
    facade,
    lock,
    planlink,
    settings,
    storage,
    transport,
    workflow,
)
from .adapters.base import AdapterError
from .models import (
    Configuration,
    MissionKind,
    ReviewerAccess,
    SchemaError,
    State,
    Status,
    positive_seconds,
)
from .registry import ADAPTERS

_KIND = {"conception": MissionKind.CONCEPTION, "recherche": MissionKind.RECHERCHE}
_ACCESS = {"context-only": ReviewerAccess.CONTEXT_ONLY, "consult": ReviewerAccess.CONSULT}

# D-5 : le code décrit le **résultat de la commande**, jamais l'approbation du
# livrable. `AWAITING_APPROVAL` vaut 0 parce que le cycle s'est arrêté où il
# devait, pas parce que le document est approuvé. `1` est le refus avant
# mutation, `2` reste réservé à `argparse` — le programme ne le produit jamais.
_EXIT_CODE = {
    Status.AWAITING_APPROVAL: 0,
    Status.INTERRUPTED: 3,
    Status.ERROR: 4,
    Status.WAITING_HUMAN: 5,
    Status.READY: 6,  # pause demandée par l'humain (Ctrl+C) : reprendre par `run`
}

# Réglages que le fichier de configuration peut fournir à `new`. Une clé absente
# d'ici reste hors de sa portée, même si `settings` sait la lire. Le délai des
# commandes qui lancent le cycle se résout à part (`settings.resolve_timeout`).
_SETTABLE_NEW = ("agent_a", "agent_b", "model_a", "model_b", "effort_a", "effort_b",
                 "web_access", "kind", "reviewer_access", "max_revisions")
_LAUNCHING = ("run", "resume", "decide")

# Défauts du programme, dernier maillon : drapeau CLI > fichier > ceci >
# `default_model()` de l'adaptateur pour les modèles. Ils ne sont plus déclarés
# à `argparse`, qui doit rendre `None` pour qu'on sache si l'humain a tranché.
_FALLBACK: dict[str, object] = {"max_revisions": 2}

# Sans valeur, la commande `new` n'a pas de sens : ni drapeau, ni fichier, ni
# défaut du programme ne peut la deviner.
_REQUIRED_NEW = ("agent_a", "agent_b", "kind", "reviewer_access")

# Domaines vérifiés pour une valeur **venue du fichier** : `argparse` fait déjà
# ce travail pour la ligne de commande, en code 2. Une mauvaise valeur dans le
# fichier n'est pas une erreur d'usage — c'est un refus avant mutation, code 1.
_DOMAINS: dict[str, dict[str, Any]] = {"kind": _KIND, "reviewer_access": _ACCESS}


def _merge_settings(args: argparse.Namespace) -> str | None:
    """Complète ce que l'humain n'a pas tranché sur la ligne de commande.

    Ordre : **drapeau CLI > fichier de configuration > `_FALLBACK` > défaut de
    l'adaptateur** (ce dernier pour les modèles seuls, plus bas). Un drapeau
    donné vaut toujours plus que le fichier, et le fichier ne complète que ce
    qui vaut `None`.

    Rend la ligne à afficher sur `stderr`, ou `None`. **Le programme dit
    toujours quel fichier a servi et ce qu'il en a pris** : un réglage qui agit
    sans se montrer est la moitié d'un état caché.
    """
    applied: list[str] = []
    if args.command in _LAUNCHING:
        timeout = settings.resolve_timeout(args.config, args.timeout)
        args.timeout, found = timeout.seconds, timeout.settings
        if timeout.origin == str(found.path):
            applied.append("timeout")
    elif args.command == "new":
        found = settings.load(args.config)
        for key in _SETTABLE_NEW:
            if getattr(args, key) is not None:
                continue
            if key in found.values:
                setattr(args, key, _from_settings(found.path, key, found.values[key]))
                applied.append(key)
            elif key in _FALLBACK:
                setattr(args, key, _FALLBACK[key])
    else:
        return None
    if found.path is None:
        return None
    retenu = ", ".join(applied) if applied else "rien de neuf"
    line = f"configuration : {found.path} ({retenu})"
    # L'ancien nom de fichier est lu, **et dit** : un réglage qui cesserait
    # d'agir en silence ferait chercher la panne ailleurs.
    return line if found.legacy_note is None else f"{found.legacy_note}\n{line}"


def _from_settings(path: Path | None, key: str, value: Any) -> Any:
    """Le domaine d'une valeur venue du fichier, que `argparse` n'a pas vue."""
    if key in ("agent_a", "agent_b") and value not in ADAPTERS:
        raise settings.SettingsError(
            f"{path} : {key} = {value!r} — attendu : {sorted(ADAPTERS)}"
        )
    domain = _DOMAINS.get(key)
    if domain is not None and value not in domain:
        raise settings.SettingsError(
            f"{path} : {key} = {value!r} — attendu : {sorted(domain)}"
        )
    if key == "max_revisions" and int(value) < 0:
        raise settings.SettingsError(f"{path} : max_revisions : entier positif ou nul attendu")
    return value


def cmd_new(args: argparse.Namespace) -> int:
    dest = Path(args.collab)
    missing = [f"--{key.replace('_', '-')}" for key in _REQUIRED_NEW if getattr(args, key) is None]
    if missing:
        return _fail(
            f"valeur(s) absente(s) : {' '.join(missing)} — sur la ligne de commande"
            " ou dans le fichier de configuration"
        )
    # La demande est obtenue **avant** la création : un cadrage interrompu ne
    # laisse rien derrière lui.
    try:
        demande_text, origin = _obtain_demande(args)
    except EOFError:
        return _fail("cadrage interrompu : rien n'a été créé")
    except (OSError, ValueError) as exc:
        return _fail(str(exc))
    request = facade.CreationRequest(
        collab=dest,
        demande=facade.DemandeSource(demande_text, str(origin["source"]), origin["path"]),
        kind=_KIND[args.kind], reviewer_access=_ACCESS[args.reviewer_access],
        agent_a=args.agent_a, agent_b=args.agent_b, max_revisions=args.max_revisions,
        model_a=args.model_a, model_b=args.model_b,
        effort_a=args.effort_a, effort_b=args.effort_b, web_access=bool(args.web_access),
        source_root=Path(args.source_root) if args.source_root else None,
        source_list=Path(args.source_list) if args.source_list else None,
        source_label=args.source_label,
    )
    try:
        result = facade.create_collaboration(request, adapters=ADAPTERS)
    except facade.CreationError as exc:
        return _fail(str(exc))
    print(f"collaboration creee : {result.path}")
    if result.missing_sections:
        # Un repère, pas une porte : A rend une QUESTION si l'absence compte.
        print(
            f"demande : section(s) absente(s) ou vide(s) — {', '.join(result.missing_sections)}."
            " La production démarre quand même.", file=sys.stderr,
        )
    return 0


def _obtain_demande(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    """Le texte de la demande et sa provenance : un fichier fourni tel quel, ou le
    cadrage guidé. Ni l'un ni l'autre n'appelle un modèle."""
    if args.cadrer:
        return demande.guide(input, print), {"source": "cadrage", "path": None}
    path = Path(args.demande)
    text, _ = storage.read_text(path)
    return text, {"source": "fichier", "path": str(path.resolve())}


def cmd_run(args: argparse.Namespace) -> int:
    return _drive(Path(args.collab), timeout_seconds=args.timeout, command_label="run")


def cmd_resume(args: argparse.Namespace) -> int:
    """Valide les arguments, construit l'intervention, la transmet. Aucune
    lecture d'état, aucune écriture : tout cela appartient au verrou."""
    if args.answer and (args.retry_call or args.reprocess or args.reason_file):
        return _fail("--answer est incompatible avec --retry-call/--reprocess/--reason-file")
    if args.retry_call and args.reprocess:
        return _fail("--retry-call (nouvel appel payant) et --reprocess (local) s'excluent")
    if bool(args.retry_call or args.reprocess) != bool(args.reason_file):
        return _fail("--retry-call ou --reprocess vont avec --reason-file, et inversement")
    intervention: workflow.Intervention | None = None
    if args.answer:
        intervention = workflow.Answer(Path(args.answer))
    elif args.retry_call:
        intervention = workflow.RetryCall(args.retry_call, Path(args.reason_file))
    elif args.reprocess:
        intervention = workflow.Reprocess(args.reprocess, Path(args.reason_file))
    return _drive(
        Path(args.collab), timeout_seconds=args.timeout, command_label="resume",
        intervention=intervention,
    )


def _drive(
    collab: Path, *, timeout_seconds: float, command_label: str,
    intervention: workflow.Intervention | None = None,
) -> int:
    ctrl_c = _CtrlC()
    previous = _install(ctrl_c)
    try:
        state = workflow.run(
            collab, adapters=ADAPTERS, timeout_seconds=timeout_seconds,
            command_label=command_label, intervention=intervention, control=ctrl_c.control,
        )
    except workflow.Stopped:
        # Arrêt demandé **hors** d'un appel (préflight, verrou, écriture) : aucun
        # appel n'était en cours, l'état est celui d'avant ou d'après une
        # publication atomique — rien n'est perdu et rien n'a été payé.
        print(
            "arrêt immédiat entre deux appels : aucun appel n'était en cours, rien n'est perdu ;"
            f" `run {collab}` reprend", file=sys.stderr,
        )
        return _EXIT_CODE[Status.READY]
    except _BORDER_ERRORS as exc:
        return _fail(_describe(exc))
    finally:
        _restore(previous)
    print(f"statut : {state.status.value} · phase : {state.phase.value}")
    if state.status is Status.READY:
        print(
            "pause : le cycle s'est arrêté à la frontière d'appel — le dernier appel est appliqué,"
            " rien n'est perdu ; `run` reprend au même endroit"
        )
    print(f"prochaine action : {decisions.next_action(collab, state)}")
    # Indexation directe, sans défaut : `run` ne rend jamais `RUNNING`, et masquer
    # un statut inattendu derrière un code plausible recréerait l'indiscernabilité
    # que D-5 corrige. `READY` n'est rendu que par une **pause** demandée.
    return _EXIT_CODE[state.status]


_PAUSE_ASKED = (
    "pause demandée : l'appel en cours va se terminer, puis le cycle s'arrête à la frontière"
    " d'appel. Ctrl+C encore = arrêt immédiat : l'appel en cours sera interrompu et pourra avoir"
    " été payé (INTERRUPTED, aucun rejeu automatique)"
)


class _CtrlC:
    """Le Ctrl+C à deux temps, traduit en `ExecutionControl` — le mécanisme même
    de la GUI. Le premier demande une **pause à la frontière d'appel** : l'appel
    en cours se termine, rien n'est perdu. Le second demande l'**arrêt immédiat** :
    l'appel en cours est interrompu, ses conséquences sont affichées (`incidents`).
    Aucune exception n'est levée depuis le gestionnaire de signal."""

    def __init__(self) -> None:
        self.control = transport.ExecutionControl()

    def on_signal(self, signum: int, frame: Any) -> None:
        if not self.control.pause_requested.is_set():
            self.control.pause_requested.set()
            print(_PAUSE_ASKED, file=sys.stderr)
            return
        self.control.interrupt_requested.set()


def _install(ctrl_c: _CtrlC) -> Any:
    try:
        return signal.signal(signal.SIGINT, ctrl_c.on_signal)
    except ValueError:  # hors du fil principal : pas de gestion de Ctrl+C
        return None


def _restore(previous: Any) -> None:
    if previous is not None:
        signal.signal(signal.SIGINT, previous)


def cmd_status(args: argparse.Namespace) -> int:
    try:
        return _status(Path(args.collab), json_output=args.json)
    except _BORDER_ERRORS as exc:
        return _fail(_describe(exc))


def _status(collab: Path, *, json_output: bool) -> int:
    config = Configuration.from_dict(_read_json(collab / "configuration.json"))
    state = State.from_dict(_read_json(collab / "etat.json"))
    corpus_age_days: int | None = None
    if config.corpus_manifest_sha256 is not None:
        manifest = _read_json(collab / "corpus" / "manifeste.json")
        captured = datetime.strptime(
            str(manifest["captured_at"]), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=UTC)
        corpus_age_days = (datetime.now(UTC) - captured).days
    payload = {
        "collaboration_id": config.collaboration_id, "mission_kind": config.mission_kind.value,
        "reviewer_access": config.reviewer_access.value, "status": state.status.value,
        "phase": state.phase.value, "revision": state.revision,
        "open_findings": len(state.open_finding_ids), "corpus_age_days": corpus_age_days,
        "last_incident": state.last_incident,
        # Lisible sans ouvrir un journal : la décision, l'incident, la suite.
        "decision": decisions.describe(collab, state),
        "incident": decisions.incident_line(collab, state),
        "next_action": decisions.next_action(collab, state),
    }
    if json_output:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for key, value in payload.items():
            print(f"{key} : {value}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Ce que l'humain lit avant de décider — strictement en lecture seule."""
    collab = Path(args.collab)
    try:
        state = State.from_dict(_read_json(collab / "etat.json"))
        print(decisions.render(collab, state, with_document=not args.no_document), end="")
    except _BORDER_ERRORS as exc:
        return _fail(_describe(exc))
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    """Acceptation, acceptation avec réserves, arrêt : sans appel, sous verrou.
    La correction ciblée passe par le moteur, comme une réponse (`Correct`)."""
    collab = Path(args.collab)
    if args.reason is not None and not args.stop:
        return _fail("--reason ne vaut qu'avec --stop")
    if args.correct:
        return _drive(
            collab, timeout_seconds=args.timeout, command_label="decide",
            intervention=workflow.Correct(Path(args.correct)),
        )
    kind = (
        decisions.ACCEPTED if args.accept else decisions.STOPPED if args.stop
        else decisions.ACCEPTED_WITH_RESERVES
    )
    try:
        state = workflow.decide(
            collab, kind, reserves=args.accept_with_reserves, reason=args.reason
        )
    except _BORDER_ERRORS as exc:
        return _fail(_describe(exc))
    print(decisions.describe(collab, state))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """La liaison **facultative** à un plan PWF (2.3), et le résumé à y reporter à la main.

    Sans option : le résumé — il se lit aussi sans aucune liaison. `--link` résout le plan
    par les scripts publics de PWF *avant* d'écrire quoi que ce soit ; `--unlink` retire
    la liaison et rien d'autre. Aucun de ces gestes n'appelle un agent ni n'écrit dans un plan."""
    collab = Path(args.collab)
    try:
        State.from_dict(_read_json(collab / "etat.json"))  # une collaboration, ou un refus
        if args.unlink:
            print("liaison retirée." if planlink.unlink(collab) else "aucune liaison à retirer.")
            return 0
        if args.link is not None:
            where = planlink.link(collab, args.link, Path(args.plan_root or Path.cwd()))
            print(f"lié au plan {args.link} ({where}). Le plan reste seul propriétaire de"
                  " l'avancement : rien n'y est écrit.")
            return 0
        for line in planlink.summary(collab):
            print(line)
        return 0
    except planlink.PlanLinkError as exc:
        return _fail(str(exc))
    except _BORDER_ERRORS as exc:
        return _fail(_describe(exc))


def cmd_gui(args: argparse.Namespace) -> int:
    """Ouvre la fenêtre Tkinter/ttk locale (`conception/GUI_V1.md`). Importée ici
    seulement : la CLI ne dépend pas de `tkinter` pour le reste de ses commandes."""
    from .gui.app import run

    run()
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Les collaborations d'un dossier, **calculées** depuis les dossiers : pas de
    base, pas d'index, rien à garder à jour."""
    root = Path(args.root)
    if not root.is_dir():
        return _fail(f"{root} n'est pas un dossier")
    found = False
    for candidate in sorted(p for p in root.iterdir() if (p / "etat.json").is_file()):
        found = True
        try:
            state = State.from_dict(_read_json(candidate / "etat.json"))
        except _BORDER_ERRORS as exc:
            print(f"{candidate.name}  illisible : {_describe(exc)}")
            continue
        print(
            f"{candidate.name}  {state.status.value}  {state.phase.value}"
            f"  révision {state.revision}  décision : {decisions.describe(candidate, state)}"
        )
    if not found:
        print(f"aucune collaboration dans {root}")
    return 0


# Types de **frontière**, nommés un par un. Pas de capture globale de
# `ValueError` : un `ValueError` accidentel du moteur doit rester bruyant, sans
# quoi un défaut du programme se déguiserait en refus ordinaire (C-10).
_BORDER_ERRORS = (
    SchemaError,
    AdapterError,
    workflow.WorkflowError,
    lock.LockError,
    transport.TransportError,
    OSError,
    json.JSONDecodeError,
    UnicodeDecodeError,
)


def _describe(exc: BaseException) -> str:
    """Un refus lisible, jamais une traceback — mais jamais muet non plus :
    certaines `OSError` ont un message vide, et « erreur : » seul n'aide
    personne."""
    return str(exc) or type(exc).__name__


def _fail(message: str) -> int:
    print(f"erreur : {message}", file=sys.stderr)
    return 1


def _read_json(path: Path) -> Any:
    text, _ = storage.read_text(path)
    return json.loads(text)


def _timeout(text: str) -> float:
    """Convertisseur `argparse` : une valeur refusée sort en code 2, comme toute
    erreur d'usage — le programme ne la produit jamais lui-même (D-5)."""
    try:
        return positive_seconds(float(text), "--timeout")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _revisions(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--max-revisions : entier attendu, pas {text!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("--max-revisions : entier positif ou nul attendu")
    return value


_EPILOG = """\
codes de sortie : 0 terminé · 1 refus avant toute modification · 2 erreur d'usage
                  3 interrompu · 4 erreur · 5 en attente de vous · 6 pause demandée
documentation   : docs/PRISE_EN_MAIN.md · docs/COMMANDES.md · docs/CONFIGURATION.md"""

_CONFIG_HELP = (
    "fichier de configuration à utiliser"
    " (sinon ./dialogforge.toml, puis ~/.dialogforge/reglages.toml)"
)
_TIMEOUT_HELP = (
    "délai dur par appel, en secondes (défaut : fichier de configuration, sinon"
    f" {settings.DEFAULT_TIMEOUT:g})"
)
_EFFORT_HELP = "effort de raisonnement de {} ; le vocabulaire est celui de l'outil, facultatif"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dialogforge",
        description="Deux agents IA en ligne de commande : A produit, B critique, vous arbitrez.",
        epilog=_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="commande")

    # Ni `required=True` ni `default=` sur ce que le fichier peut fournir : la
    # valeur doit rester `None` pour que `_merge_settings` sache que l'humain
    # n'a rien tranché. Le manque est constaté dans `cmd_new`, donc en code 1 —
    # un refus avant mutation, pas une erreur d'usage.
    p_new = sub.add_parser("new", help="créer une collaboration (aucun appel d'agent)")
    p_new.add_argument("collab", help="dossier de la collaboration, qui ne doit pas exister")
    # Un fichier de demande, ou le cadrage guidé : jamais les deux, jamais aucun.
    source = p_new.add_mutually_exclusive_group(required=True)
    source.add_argument("--demande", help="fichier texte qui contient votre demande")
    source.add_argument(
        "--cadrer", action="store_true",
        help="écrire la demande par un questionnaire de terminal, sans appel de modèle",
    )
    p_new.add_argument("--config", help=_CONFIG_HELP)
    p_new.add_argument(
        "--kind", choices=sorted(_KIND), help="genre de livrable (une recherche exige un corpus)"
    )
    p_new.add_argument(
        "--reviewer-access", choices=sorted(_ACCESS),
        help="consult laisse à B les outils de sa CLI, context-only les lui retire",
    )
    p_new.add_argument("--agent-a", choices=sorted(ADAPTERS), help="l'outil qui produit")
    p_new.add_argument("--agent-b", choices=sorted(ADAPTERS), help="l'outil qui critique")
    p_new.add_argument("--source-root", help="dossier des sources ; va avec --source-list")
    p_new.add_argument(
        "--source-list",
        help="fichier qui liste les sources, un chemin par ligne relatif à --source-root",
    )
    p_new.add_argument("--source-label", help="nom du corpus (défaut : nom de --source-root)")
    p_new.add_argument("--model-a", help="modèle de A (défaut : celui de l'adaptateur)")
    p_new.add_argument("--model-b", help="modèle de B (défaut : celui de l'adaptateur)")
    p_new.add_argument("--effort-a", help=_EFFORT_HELP.format("A"))
    p_new.add_argument("--effort-b", help=_EFFORT_HELP.format("B"))
    p_new.add_argument(
        "--web-access", action=argparse.BooleanOptionalAction, default=None,
        help="autoriser la recherche web, pour A et B ; fermé par défaut",
    )
    p_new.add_argument(
        "--max-revisions", type=_revisions,
        help="nombre maximal de révisions (défaut : fichier de configuration, sinon 2)",
    )
    p_new.set_defaults(func=cmd_new)

    p_run = sub.add_parser("run", help="lancer ou reprendre le cycle (appels payants)")
    p_run.add_argument("collab", help="dossier de la collaboration")
    p_run.add_argument("--config", help=_CONFIG_HELP)
    p_run.add_argument("--timeout", type=_timeout, help=_TIMEOUT_HELP)
    p_run.set_defaults(func=cmd_run)

    p_resume = sub.add_parser(
        "resume", help="sortir d'un arrêt : répondre à une question, relancer, retraiter"
    )
    p_resume.add_argument("collab", help="dossier de la collaboration")
    p_resume.add_argument("--config", help=_CONFIG_HELP)
    p_resume.add_argument("--timeout", type=_timeout, help=_TIMEOUT_HELP)
    p_resume.add_argument(
        "--answer", help="fichier qui complète la demande (statut WAITING_HUMAN)"
    )
    p_resume.add_argument(
        "--retry-call", help="identifiant de l'appel à relancer : nouvel appel payant"
    )
    p_resume.add_argument(
        "--reprocess", metavar="UUID",
        help="identifiant de l'appel dont la réponse conservée est relue en local, sans appel",
    )
    p_resume.add_argument(
        "--reason-file", help="fichier qui dit pourquoi ; exigé avec --retry-call et --reprocess"
    )
    p_resume.set_defaults(func=cmd_resume)

    # `status` est en lecture seule et n'a rien à régler : pas de `--config`.
    p_status = sub.add_parser("status", help="dire où en est la collaboration (lecture seule)")
    p_status.add_argument("collab", help="dossier de la collaboration")
    p_status.add_argument("--json", action="store_true", help="sortie en une ligne JSON")
    p_status.set_defaults(func=cmd_status)

    p_show = sub.add_parser("show", help="lire le résultat avant de décider (lecture seule)")
    p_show.add_argument("collab", help="dossier de la collaboration")
    p_show.add_argument(
        "--no-document", action="store_true", help="le résumé seul, sans le document"
    )
    p_show.set_defaults(func=cmd_show)

    # Une décision et une seule par commande. Trois ne touchent pas au moteur ;
    # `--correct` l'utilise, donc accepte `--timeout` et `--config`.
    p_decide = sub.add_parser("decide", help="consigner votre décision sur la version examinée")
    p_decide.add_argument("collab", help="dossier de la collaboration")
    p_decide.add_argument("--config", help=_CONFIG_HELP)
    p_decide.add_argument("--timeout", type=_timeout, help=_TIMEOUT_HELP)
    choice = p_decide.add_mutually_exclusive_group(required=True)
    choice.add_argument("--accept", action="store_true", help="accepter cette version")
    choice.add_argument(
        "--accept-with-reserves", metavar="TEXTE", help="accepter, avec vos réserves (exigées)"
    )
    choice.add_argument(
        "--correct", metavar="FICHIER",
        help="fichier qui complète la demande : A révise, B relit, un tour au-delà du plafond",
    )
    choice.add_argument("--stop", action="store_true", help="arrêter, définitivement")
    p_decide.add_argument("--reason", help="motif de l'arrêt ; ne vaut qu'avec --stop")
    p_decide.set_defaults(func=cmd_decide)

    p_plan = sub.add_parser(
        "plan", help="résumé à reporter dans un plan PWF, ou liaison facultative à ce plan"
    )
    p_plan.add_argument("collab", help="dossier de la collaboration")
    which = p_plan.add_mutually_exclusive_group()
    which.add_argument("--link", metavar="ID_DU_PLAN", help="lier la collaboration à ce plan")
    which.add_argument("--unlink", action="store_true", help="retirer la liaison")
    p_plan.add_argument("--plan-root", help="racine du projet qui porte `.planning/`")
    p_plan.set_defaults(func=cmd_plan)

    p_list = sub.add_parser("list", help="énumérer les collaborations d'un dossier")
    p_list.add_argument("root", help="dossier qui contient des collaborations")
    p_list.set_defaults(func=cmd_list)

    p_gui = sub.add_parser("gui", help="ouvrir la fenêtre locale (Tkinter)")
    p_gui.set_defaults(func=cmd_gui)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        note = _merge_settings(args)
    except settings.SettingsError as exc:
        return _fail(str(exc))
    if note is not None:
        print(note, file=sys.stderr)
    result: int = args.func(args)
    return result
