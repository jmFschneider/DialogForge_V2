"""Scénario de bout en bout **sans aucun fournisseur** — référence J0.

Il pilote les vraies commandes `new` puis `run` de la CLI, avec les faux
adaptateurs du projet substitués à `cli.ADAPTERS`, exactement comme le fait la
suite de tests. Aucun exécutable `claude` ou `codex` présent sur le `PATH` n'est
résolu : les deux agents sont des sous-processus Python scriptés.

    python reference/cycle_sans_fournisseur.py [dossier_de_sortie]

Sans argument, la collaboration est créée dans un dossier temporaire conservé et
affiché en fin d'exécution, pour inspection des artefacts sur disque.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from tempfile import mkdtemp
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Le faux agent ecrit sa reponse avec `sys.stdout.write` : sous Windows, un
# tube herite de l'encodage local (cp1252) alors que les adaptateurs decodent
# en UTF-8. C'est une propriete du faux agent, pas du moteur ; les reponses
# accentuees de ce scenario exigent donc de fixer l'encodage des enfants.
os.environ["PYTHONIOENCODING"] = "utf-8"

from iabinome import cli, decisions, objections, settings  # noqa: E402
from tests import fakes  # noqa: E402

DEMANDE = """\
# Demande

## Objectif
Décrire le cache local de FloraPi.

## Livrable
Une note de conception d'une page.

## Sources
Aucune : le cache est décrit à partir de la demande seule.

## Contraintes
Une page au plus.

## Non-objectifs
Aucune implémentation.

## Critères de fin
La note énonce la politique d'invalidation et ses limites.
"""

DOCUMENT_A = """\
IABINOME:DOCUMENT
# Cache local de FloraPi

Le cache conserve les réponses sur disque, indexées par requête normalisée.
Invalidation : à l'échéance, et à la main via `floracli cache purge`.
"""

DOCUMENT_A_CORRIGE = """\
IABINOME:DOCUMENT
# Cache local de FloraPi

Le cache conserve les réponses sur disque, indexées par requête normalisée.
Invalidation : à l'échéance, et à la main via `floracli cache purge`.

## Limites
Aucune invalidation par événement amont : une donnée changée à la source reste
servie jusqu'à l'échéance. C'est la réserve soulevée par B (B-001).
IABINOME:REPONSES
""" + json.dumps({"schema_version": 1, "responses": [{
    "id": "B-001", "response": "CORRIGE",
    "justification": "Section « Limites » ajoutée.",
}]}, ensure_ascii=False)

ENONCE = "Les limites de l'invalidation ne sont pas énoncées."

# Revue v2 : l'énoncé reste celui du premier tour, la raison va dans `justification`.
REVUE_REVISER = json.dumps({
    "schema_version": 2, "decision": "REVISER",
    "analysis": "La note tient, mais le critère de fin n'est pas atteint.",
    "findings": [{
        "id": "B-001", "severity": "MAJOR", "disposition": "OPEN", "statement": ENONCE,
        "justification": "Aucune section ne dit ce que le cache ne sait pas invalider.",
    }],
}, ensure_ascii=False)

REVUE_ACCEPTER = json.dumps({
    "schema_version": 2, "decision": "ACCEPTER",
    "analysis": "La réserve est traitée, sans régression sur le reste.",
    "findings": [{
        "id": "B-001", "severity": "MAJOR", "disposition": "RESOLVED", "statement": ENONCE,
        "justification": "La section « Limites » énonce l'invalidation par événement absente.",
    }],
}, ensure_ascii=False)


class ScenarioAdapter(fakes.FakeAdapter):
    """Faux adaptateur à réponse de repli explicite : une liste épuisée ne doit
    pas transformer B en producteur de document hors contrat."""

    def __init__(self, adapter_id: str, responses: tuple[str, ...], fallback: str) -> None:
        super().__init__(adapter_id, responses)
        self.fallback = fallback

    def command(self, call: fakes.CallSpec) -> list[str]:
        if not self.responses:
            self.responses = [self.fallback]
        return super().command(call)


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path(mkdtemp(prefix="df2-reference-"))
    root.mkdir(parents=True, exist_ok=True)
    demande = root / "demande-source.md"
    demande.write_text(DEMANDE, encoding="utf-8")
    collab = root / "collaboration"

    agent_a = ScenarioAdapter("fake-a", (DOCUMENT_A, DOCUMENT_A_CORRIGE), DOCUMENT_A_CORRIGE)
    agent_b = ScenarioAdapter("fake-b", (REVUE_REVISER, REVUE_ACCEPTER), REVUE_ACCEPTER)

    with (
        mock.patch.object(cli, "ADAPTERS", {"fake-a": agent_a, "fake-b": agent_b}),
        mock.patch.object(settings, "SEARCH_PATHS", ()),
    ):
        exemples = Path(__file__).resolve().parent.parent / "exemples"
        code = cli.main([
            "new", str(collab), "--demande", str(demande),
            "--kind", "conception", "--reviewer-access", "consult",
            "--source-root", str(exemples), "--source-list", str(exemples / "corpus.txt"),
            "--agent-a", "fake-a", "--agent-b", "fake-b", "--max-revisions", "1",
        ])
        if code != 0:
            print(f"ECHEC : `new` a rendu {code}")
            return code
        code = cli.main(["run", str(collab)])
        cli.main(["status", str(collab)])
        # Le parcours de l'humain, par les vraies commandes, sans rien recopier :
        # lire le résultat, décider, retrouver la collaboration.
        print("\n--- show ---")
        cli.main(["show", str(collab), "--no-document"])
        print("--- decide --accept ---")
        decision_code = cli.main(["decide", str(collab), "--accept"])
        print("--- list ---")
        cli.main(["list", str(root)])

    etat = json.loads((collab / "etat.json").read_text(encoding="utf-8"))
    print("\n--- Bilan du scenario ---")
    print(f"code de sortie `run` : {code}")
    print(f"statut               : {etat['status']}")
    print(f"phase                : {etat['phase']}")
    print(f"appels resolus       : A={agent_a.calls}  B={agent_b.calls}")
    print(f"appels reellement lances : {fakes.launched_calls(collab)}")
    print("artefacts :")
    for path in sorted(collab.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(collab).as_posix()}")
    print("\nobjections (registre) :")
    for objection in objections.ledger(collab):
        print(f"  {objection['id']} : {objection['disposition']} — {objection['statement']}")
        for event in objection["history"]:
            what = event.get("response") or event.get("disposition")
            print(f"      {event['call']} {event['by']} {what} : {event['justification']}")
    print(f"\ncollaboration conservee ici : {collab}")
    # Un scénario de référence qui n'échoue jamais ne prouve rien : le cycle doit
    # aller à son terme, sans objection ouverte.
    if etat["status"] != "AWAITING_APPROVAL" or etat["open_finding_ids"]:
        print("ECHEC : le cycle n'est pas arrive a AWAITING_APPROVAL sans objection ouverte")
        return 1
    # Proposition, correction : deux appels de A, deux de B. Un troisieme appel de
    # A serait une finalisation qui reecrit apres la derniere revue (1.3).
    if (agent_a.calls, agent_b.calls) != (2, 2):
        print(f"ECHEC : appels A={agent_a.calls} B={agent_b.calls}, attendu 2 et 2")
        return 1
    # « Terminé » n'est pas « accepté » : l'acceptation est une décision consignée,
    # et le statut du moteur n'a pas bougé.
    accepted = decisions.latest(collab)
    if decision_code != 0 or accepted is None or accepted["decision"] != "ACCEPTE":
        print("ECHEC : la decision d'acceptation n'est pas consignee")
        return 1
    if json.loads((collab / "etat.json").read_text(encoding="utf-8"))["status"] != (
        "AWAITING_APPROVAL"
    ):
        print("ECHEC : accepter a change le statut du moteur")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
