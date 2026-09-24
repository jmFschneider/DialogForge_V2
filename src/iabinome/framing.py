"""Le cadrage avec agent F, avant toute collaboration (`conception/CADRAGE_AGENT.md`).

Ce module possède la session de F — rien d'autre ne la touche : ni A, ni B, ni le
moteur A/B, qui garde son verrou et `current_call` (§8.2). Un cadrage n'est pas une
collaboration : aucun `etat.json`, aucune phase, aucune reprise après la fin du
processus (§6.1).

**Session par reprise d'identifiant** (amendement A3) : chaque tour relance l'outil
sur la même session fournisseur, par le transport commun — délai dur, flux bornés,
arbre terminé, `resultat.json` seulement pour une sortie propre. Le premier tour en
ouvre une neuve ; l'identifiant que l'outil déclare est gardé **en mémoire** pour les
suivants, masqué dans les traces, et oublié à la fermeture.

**La conversation** (`Framing`) se mène par étapes, une opération à la fois, pour que
la CLI et le fil moteur de la GUI l'appellent pareil. Le programme ne classe jamais les
réponses humaines (§2.3) : il compte, il vérifie les balises, il consigne. Le compteur
d'un groupe dénombre les réponses humaines, sans exception (amendement A1) : limite 3
pour le premier groupe, 2 ensuite ; une question rendue à la limite est non conforme.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import contracts, corpus, isolation, prompts, storage, transport
from .adapters.base import AgentAdapter, EnvPolicy, FramingSessionSpec, ObservedCli
from .demande import validate_framed
from .models import SCHEMA_VERSION, AgentPurpose, MissionKind

_MASK = "<session>"
_TAG = "IABINOME:"
QUESTION, READY, DRAFT = "CADRAGE_QUESTION", "CADRAGE_PRET", "DEMANDE"
_CONVERSATION = (QUESTION, READY)
_REQUIRED = {
    QUESTION: ("QUESTION", "POURQUOI", "ETAT_CADRAGE"),
    READY: ("RESUME", "SANS_REPONSE", "APERCU", "ETAT_CADRAGE"),
}
_TITLES = {QUESTION: "F — question", READY: "F — proposition de clôture", DRAFT: "F — brouillon"}
_WARNING = "> Historique non normatif ; seul `demande.md` fait autorité."


class FramingError(RuntimeError):
    """Refus lisible du cadrage — prévol, ou session déjà fermée."""


@dataclass(frozen=True)
class Exchange:
    """Un tour de F. `outcome` vaut `COMPLETED` quand `text` porte sa réponse ;
    sinon, il nomme l'incident, et le tour n'est **jamais relancé tout seul** (§2.4) :
    l'humain relance dans la même session, clôt ou annule."""

    call_dir: Path
    outcome: str
    text: str | None = None
    detail: str = ""


def check_adapter(
    adapter_id: str, adapters: Mapping[str, AgentAdapter], model: str | None,
    effort: str | None,
) -> tuple[str, ObservedCli]:
    """Le prévol de F (§3.2, étapes 3 et 4) : il précède toute ouverture de session et
    tout appel. Rend le modèle effectif et la version observée."""
    adapter = adapters.get(adapter_id)
    if adapter is None:
        raise FramingError(f"adaptateur de cadrage inconnu : {adapter_id!r}")
    caps = adapter.capabilities
    missing = [
        label for label, present in (
            ("lecture seule", caps.enforces_read_only),
            ("session persistante de cadrage", caps.supports_persistent_framing_session),
        ) if not present
    ]
    if missing:
        raise FramingError(f"{adapter_id} : cadrage non supporté ({', '.join(missing)})")
    default = adapter.default_model(AgentPurpose.FRAMING)
    if model is not None and model != default and not caps.supports_model_override:
        raise FramingError(f"{adapter_id} : modèle non remplaçable")
    if effort is not None and effort not in caps.effort_levels:
        accepted = ", ".join(caps.effort_levels) or "aucun : réglage non supporté"
        raise FramingError(f"{adapter_id} : effort {effort!r} refusé — attendu : {accepted}")
    seen = adapter.probe()
    if not seen.present:
        raise FramingError(f"{adapter_id} : CLI absente")
    return model or default, seen


class FramingSession:
    """La session de F : possédée par une seule commande ou un seul contrôleur, un
    `send` à la fois, jamais reprise après `close` (§6.1)."""

    def __init__(
        self, adapter: AgentAdapter, spec: FramingSessionSpec, *,
        others: Iterable[EnvPolicy] = (), control: transport.ExecutionControl | None = None,
    ) -> None:
        self._adapter, self.spec, self._control = adapter, spec, control
        self.adapter_id = adapter.adapter_id
        rest = tuple(others)
        self._env = isolation.clean_env(os.environ, adapter.env, rest)
        self._removed = isolation.refused_names(os.environ, adapter.env, rest)
        self._session: str | None = None
        self.exchanges = 0
        self.closed = False

    def send(self, prompt: str, call_dir: Path) -> Exchange:
        """Un tour : le prompt par stdin, les traces sous `call_dir` (§8.1)."""
        if self.closed:
            raise FramingError("session de cadrage fermée : elle ne se reprend pas")
        # Résolu avant le premier octet écrit, comme pour A et B : un exécutable disparu
        # est un refus qui ne laisse aucun dossier d'appel orphelin.
        argv = self._adapter.framing_command(self.spec, self._session, prompt)
        call_dir.mkdir(parents=True)
        storage.write_atomic_text(call_dir / "prompt.txt", prompt)
        _write_json(call_dir / "intention.json", {
            "schema_version": SCHEMA_VERSION, "purpose": AgentPurpose.FRAMING.value,
            "exchange": self.exchanges + 1, "adapter_id": self._adapter.adapter_id,
            "model": self.spec.model, "effort": self.spec.effort,
            "prompt_sha256": contracts.normalize(prompt).sha256,
            # `argv[0]` retiré (aucun chemin absolu persisté) et l'identifiant de session
            # masqué : il reste encapsulé, jamais une autorité (§6.1, §9.2).
            "invocation_args": [self._mask(arg) for arg in argv[1:]],
            "session": "neuve" if self._session is None else "reprise",
            "workdir": "neutre", "env_removed": self._removed,
            "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        self.exchanges += 1
        try:
            result = transport.run(
                argv, cwd=self.spec.work_root, call_dir=call_dir,
                timeout_seconds=self.spec.timeout_seconds, stdin_text=prompt,
                env=self._env, control=self._control,
            )
        except transport.TransportError as exc:
            return Exchange(call_dir, "LAUNCH_FAILED", detail=str(exc))
        if result.outcome is not transport.Outcome.COMPLETED:
            return Exchange(call_dir, result.outcome.value)
        if result.return_code != 0:
            return Exchange(call_dir, "CLI_FAILED", detail=f"code de retour {result.return_code}")
        try:
            text, session = self._adapter.framing_extract(
                (call_dir / "stdout.txt").read_bytes(), (call_dir / "stderr.txt").read_bytes()
            )
        except (UnicodeDecodeError, ValueError) as exc:
            return Exchange(call_dir, "DECODE_FAILED", detail=str(exc))
        storage.write_atomic_text(call_dir / "reponse_brute.txt", text)
        if session is None or (self._session is not None and session != self._session):
            # Une réponse hors de la session ouverte n'est pas un tour de ce cadrage :
            # la garder ouverte ferait converser F sans le contexte qu'on lui croit.
            self.close()
            return Exchange(call_dir, "SESSION_LOST", text, "l'outil n'a pas repris la session")
        self._session = session
        return Exchange(call_dir, "COMPLETED", text)

    def close(self) -> None:
        """Oublie l'identifiant : plus aucun envoi possible. La trace que l'outil garde
        de sa propre session n'est ni lue ni reprise par DialogForge (A3)."""
        self._session = None
        self.closed = True

    def _mask(self, arg: str) -> str:
        return arg if self._session is None else arg.replace(self._session, _MASK)


def open_session(
    adapter: AgentAdapter, spec: FramingSessionSpec, *,
    others: Iterable[EnvPolicy] = (), control: transport.ExecutionControl | None = None,
) -> FramingSession:
    """Ouvre une session **neuve** : rien n'est repris d'un cadrage antérieur (§5.2).
    L'outil ne la crée qu'au premier `send` — ouvrir ne coûte aucun appel."""
    if not adapter.capabilities.supports_persistent_framing_session:
        raise FramingError(f"{adapter.adapter_id} : session persistante de cadrage non supportée")
    return FramingSession(adapter, spec, others=others, control=control)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


class ProtocolError(ValueError):
    """Une sortie de F hors du contrat de cadrage — conservée, affichée, jamais relancée."""


@dataclass(frozen=True)
class Reply:
    kind: str
    body: str


@dataclass(frozen=True)
class Turn:
    """Un échange jugé : `problem` nomme l'incident de transport ou de protocole ;
    `None`, la sortie est conforme et `reply` la porte."""

    exchange: Exchange
    reply: Reply | None
    problem: str | None = None


@dataclass(frozen=True)
class FramingArtifacts:
    """Ce que la création reçoit du cadrage (§10) : le dossier jetable (appels,
    transcription, corpus préparé), le brouillon validé de F et la provenance, à
    compléter par l'empreinte du texte accepté. Jamais la session."""

    root: Path
    draft: str
    provenance: dict[str, Any]


def parse_reply(text: str, expected: tuple[str, ...]) -> Reply:
    """La balise attendue sur sa propre ligne, puis les sections du contrat (§6.4).
    Une phrase avant la balise d'une réponse conversationnelle est tolérée — balisé,
    donc lisible ; jamais avant `IABINOME:DEMANDE`, qui devient `demande.md`. Aucun
    compte de points d'interrogation ni d'alternatives (test 22)."""
    lines = contracts.normalize(text).text.splitlines()
    index = next((i for i, line in enumerate(lines) if line.strip().startswith(_TAG)), None)
    if index is None:
        raise ProtocolError("aucune balise IABINOME:")
    kind = lines[index].strip().removeprefix(_TAG)
    if kind not in expected:
        raise ProtocolError(f"balise {kind!r} inattendue — attendu : {', '.join(expected)}")
    body = "\n".join(lines[index + 1:]).strip() + "\n"
    if kind == DRAFT:
        problems = validate_framed(body)
        if any(line.strip() for line in lines[:index]):
            problems.insert(0, "texte avant la balise")
    else:
        present = {line.strip() for line in lines[index + 1:]}
        problems = [f"section {name} absente" for name in _REQUIRED[kind] if name not in present]
    if problems:
        raise ProtocolError(" ; ".join(problems))
    return Reply(kind, body)


def prepare(
    kind: MissionKind, source_root: Path | None = None, source_list: Path | None = None,
    source_label: str | None = None,
) -> Path:
    """Le dossier jetable du cadrage (§5.1, §8.1), avant toute session. F travaille dans
    `travail/`, qui ne contient que la copie `corpus/fichiers/` ; manifeste, traces et
    transcription restent à côté, hors de sa racine. Sans source : permis en
    conception, refusé en recherche (§2.2)."""
    root = Path(tempfile.mkdtemp(prefix="framing-"))
    try:
        (root / "travail").mkdir()
        entries: tuple[corpus.ManifestEntry, ...] = ()
        if source_root is not None:
            if source_list is None:
                raise FramingError("--source-root exige --source-list")
            (root / "corpus").mkdir()
            entries = corpus.build(
                source_root, source_list, root / "corpus", source_label or source_root.name
            ).entries
            if entries:
                shutil.copytree(
                    root / "corpus" / "fichiers", root / "travail" / "corpus" / "fichiers"
                )
        if not entries and kind is MissionKind.RECHERCHE:
            raise FramingError("mission de recherche sans corpus")
    except (corpus.CorpusError, OSError) as exc:
        shutil.rmtree(root, ignore_errors=True)
        raise FramingError(str(exc)) from exc
    except FramingError:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


class Framing:
    """La conversation de cadrage, sur une session ouverte et son dossier jetable.

    Une opération par appel : `start`, `answer`, `reopen`, `write_draft`, `retry`. Le
    brouillon (`draft`) n'existe qu'après une sortie `DEMANDE` conforme ; rien n'est
    jamais promu ni relancé d'ici (§2.6)."""

    def __init__(self, session: FramingSession, root: Path, idea: str) -> None:
        self.session, self.root, self.idea = session, root, idea
        self.group, self.answers = 1, 0
        self.draft: str | None = None
        self.last: Turn | None = None
        self.contributions = 0
        self._started = False
        self._closure = "USER_CLOSED"
        self._open_questions: list[str] = []
        self._prompt: tuple[str, tuple[str, ...]] | None = None
        # Relevé **avant** le premier envoi : c'est la référence de `SOURCES_MODIFIED`.
        self._sources = self._snapshot()
        self._entries: list[tuple[str, str]] = [("Idée initiale", idea)]
        _write_json(root / "session.json", {
            "schema_version": SCHEMA_VERSION, "adapter_id": session.adapter_id,
            "model": session.spec.model, "effort": session.spec.effort,
            "persistent": True, "resumable": False,
        })
        self._write_transcript()

    @property
    def limit(self) -> int:
        return 3 if self.group == 1 else 2

    def start(self) -> Turn:
        return self._send(prompts.build_framing_start(self.idea), _CONVERSATION)

    def answer(self, text: str) -> Turn:
        """Répond à la question de F, dans le groupe courant."""
        self._require(QUESTION)
        self.answers += 1
        self.contributions += 1
        self.note("Réponse humaine", text)
        prompt = prompts.build_framing_continue(text, self.group, self.answers, self.limit)
        return self._send(prompt, _CONVERSATION)

    def reopen(self, text: str, *, correction: bool) -> Turn:
        """« Continuer » ou « Corriger un point » après une proposition, ou « continuer
        le cadrage » après le brouillon : un nouveau groupe, dont `text` est la première
        réponse (A1)."""
        self._require(READY, DRAFT)
        self.group, self.answers, self.draft = self.group + 1, 1, None
        self.contributions += 1
        self.note("Correction humaine" if correction else "Poursuite du cadrage", text)
        prompt = prompts.build_framing_reopen(text, self.group, correction=correction)
        return self._send(prompt, _CONVERSATION)

    def write_draft(self) -> Turn:
        """La rédaction, dans la même session ; avant tout échange abouti, le premier
        envoi la porte avec l'idée (A2). N'ouvre aucun groupe (test 34)."""
        last = self.last
        proposed = last is not None and last.problem is None and last.reply is not None and (
            last.reply.kind == READY
        )
        self._closure = "AGENT_PROPOSED" if proposed else "USER_CLOSED"
        prompt = (
            prompts.build_framing_draft() if self._started
            else prompts.build_framing_start(self.idea, draft=True)
        )
        return self._send(prompt, (DRAFT,))

    def retry(self) -> Turn:
        """Relance **explicite** après un incident, dans la même session : le même
        envoi si F ne l'a pas reçu, sinon un rappel du contrat."""
        if self.last is None or self.last.problem is None or self._prompt is None:
            raise FramingError("rien à relancer")
        prompt, expected = self._prompt
        if self.last.exchange.outcome == "COMPLETED":
            prompt = prompts.build_framing_retry(self.last.problem)
        return self._send(prompt, expected)

    def check_sources(self) -> None:
        if self._snapshot() != self._sources:
            raise FramingError("la copie des sources a changé pendant le cadrage")

    def artifacts(self) -> FramingArtifacts:
        """Juste avant la création : le brouillon existe, et la copie des sources n'a
        pas bougé (§5.3, « avant la promotion »). Aucun chemin absolu (§9)."""
        if self.draft is None:
            raise FramingError("aucun brouillon à promouvoir")
        self.check_sources()
        manifest = self.root / "corpus" / "manifeste.json"
        label = manifest_sha = None
        if manifest.is_file():
            text, _ = storage.read_text(manifest)
            label = corpus.read_manifest(manifest).origin_label
            manifest_sha = contracts.normalize(text).sha256
        transcript, _ = storage.read_text(self.root / "transcription.md")
        spec = self.session.spec
        return FramingArtifacts(self.root, self.draft, {
            "schema_version": SCHEMA_VERSION,
            "agent": {"adapter_id": self.session.adapter_id, "model": spec.model,
                      "effort": spec.effort},
            "session": {"persistent": True, "new_for_this_framing": True, "resumable": False},
            "sources": {"provided": manifest_sha is not None, "label": label,
                        "manifest_sha256": manifest_sha},
            "closure": self._closure, "turn_count": self.contributions,
            "exchange_count": self.session.exchanges, "open_questions": self._open_questions,
            "transcription_sha256": contracts.normalize(transcript).sha256,
        })

    def note(self, title: str, text: str) -> None:
        self._entries.append((title, text))
        self._write_transcript()

    def discard(self) -> None:
        """Annulation, fin d'entrée ou interruption : fermer la session, puis détruire
        le dossier jetable. Aucune collaboration n'a existé."""
        self.session.close()
        shutil.rmtree(self.root, ignore_errors=True)

    def _require(self, *kinds: str) -> None:
        last = self.last
        if last is None or last.problem is not None or last.reply is None or (
            last.reply.kind not in kinds
        ):
            raise FramingError("action impossible à ce stade du cadrage")

    def _send(self, prompt: str, expected: tuple[str, ...]) -> Turn:
        self._prompt = (prompt, expected)
        call_dir = self.root / "appels" / f"{self.session.exchanges + 1:04d}-{uuid.uuid4().hex}"
        turn = self._judge(self.session.send(prompt, call_dir), expected)
        self.last = turn
        if turn.problem is not None:
            self.note("F — incident", f"{turn.problem}\n\n{turn.exchange.text or ''}")
        else:
            assert turn.reply is not None
            if turn.reply.kind == DRAFT:
                self.draft = turn.reply.body
            if turn.reply.kind == READY:
                self._open_questions = _unanswered(turn.reply.body)
            self.note(_TITLES[turn.reply.kind], turn.reply.body)
        return turn

    def _judge(self, exchange: Exchange, expected: tuple[str, ...]) -> Turn:
        # Avant de lire la réponse, comme pour A et B : une réponse produite sur des
        # sources changées n'est plus celle qu'on croit. Constaté, jamais empêché.
        try:
            self.check_sources()
        except FramingError as exc:
            self.session.close()
            return Turn(exchange, None, f"SOURCES_MODIFIED : {exc}")
        if exchange.outcome != "COMPLETED" or exchange.text is None:
            return Turn(exchange, None, f"{exchange.outcome} {exchange.detail}".strip())
        self._started = True
        try:
            reply = parse_reply(exchange.text, expected)
        except ProtocolError as exc:
            return Turn(exchange, None, f"sortie hors protocole : {exc}")
        if reply.kind == QUESTION and self.answers >= self.limit:
            return Turn(exchange, reply, "question au-delà de la limite du groupe")
        return Turn(exchange, reply)

    def _snapshot(self) -> dict[str, str]:
        files = self.session.spec.work_root / "corpus" / "fichiers"
        if not files.is_dir():
            return {}
        return {
            p.relative_to(files).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files.rglob("*")) if not p.is_dir()
        }

    def _write_transcript(self) -> None:
        parts = ["# Transcription du cadrage", "", _WARNING, ""]
        for title, text in self._entries:
            parts += [f"## {title}", "", text.strip() or "(vide)", ""]
        storage.write_atomic_text(self.root / "transcription.md", "\n".join(parts))


def shown(turn: Turn) -> str:
    """Ce que l'écran montre d'un tour, en CLI comme en GUI : l'incident et la sortie
    gardée, ou la réponse de F sans son état de cadrage, qui sert aux contrôles et à la
    provenance, pas à la lecture."""
    if turn.problem is not None:
        return "\n".join(filter(None, (f"Incident : {turn.problem}", turn.exchange.text)))
    assert turn.reply is not None
    return turn.reply.body.split("\nETAT_CADRAGE")[0].rstrip()


def _unanswered(body: str) -> list[str]:
    """Les questions restées sans réponse d'une proposition (bloc `SANS_REPONSE`)."""
    found, inside = [], False
    for line in body.splitlines():
        if line.strip() in _REQUIRED[READY]:
            inside = line.strip() == "SANS_REPONSE"
        elif inside and line.startswith("- "):
            found.append(line[2:].strip())
    return found
