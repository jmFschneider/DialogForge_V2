"""Tests de iabinome.workflow : prévol, cycle complet, transitions, frontière.

Tous les appels passent par `FakeAdapter` — aucun fournisseur, aucun réseau,
aucun coût (CONCEPTION_FINALE.md §10)."""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import contracts, workflow
from iabinome.adapters.base import Capabilities
from iabinome.models import Phase, Status
from iabinome.workflow import WorkflowError
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
# Depuis 1.2, une révision répond à chaque objection ouverte : `fakes.review()`
# en ouvre une, `B-001`.
_DOC2 = fakes.revision()
_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"

# B reprend chaque constat antérieur exactement une fois, même pour le fermer :
# le faire disparaître est un échec de contrat (§6).
_RESOLVED = ({
    "id": "B-001", "severity": "MAJOR", "disposition": "RESOLVED", "statement": "Manque X.",
},)


class WorkflowCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def build(self, a: tuple[str, ...], b: tuple[str, ...], **kwargs: object) -> Path:
        self.a = fakes.FakeAdapter("fake-a", a)
        self.b = fakes.FakeAdapter("fake-b", b)
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        return fakes.collaboration(self.root, **kwargs)  # type: ignore[arg-type]

    def run_engine(self, collab: Path, **kwargs: object) -> object:
        return workflow.run(
            collab, adapters=self.adapters, timeout_seconds=30.0, **kwargs  # type: ignore[arg-type]
        )

    def etat(self, collab: Path) -> dict[str, object]:
        raw = fakes.read_json(collab / "etat.json")
        assert isinstance(raw, dict)
        return raw


class TestFullCycle(WorkflowCase):
    def test_cycle_reaches_awaiting_approval(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        state = workflow.run(collab, adapters=self.adapters, timeout_seconds=30.0)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        self.assertIs(state.phase, Phase.CLOSED)
        self.assertIsNone(state.current_call)
        self.assertEqual(state.current_document, "livrables/version_finale.md")
        # Plus d'appel de finalisation : la version examinée est promue (1.3).
        self.assertEqual(self.a.calls, 2)
        self.assertEqual(self.b.calls, 2)

    def test_exchange_artifacts_are_named_and_ordered(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        self.run_engine(collab)
        names = sorted(p.name for p in (collab / "echanges").iterdir())
        self.assertEqual(names, [
            "0001-proposition-A.md",
            "0002-critique-B.json",
            "0003-reponses-A.json",
            "0003-revision-1-A.md",
            "0004-critique-B.json",
        ])

    def test_final_document_opens_on_the_program_written_line(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
            corpus_captured_at="2026-09-03",
        )
        self.run_engine(collab)
        final = (collab / "livrables" / "version_finale.md").read_text(encoding="utf-8")
        self.assertIn("n'est pas approuvé", final)
        self.assertIn("Revue B : CONSULT", final)
        self.assertIn("constats restés ouverts : 0 (dont 0 BLOCKING)", final)
        self.assertIn("corpus figé le 2026-09-03", final)
        examined = (collab / "echanges" / "0003-revision-1-A.md").read_text(encoding="utf-8")
        self.assertTrue(final.endswith(examined), "le livrable n'est pas la version examinee")

    def test_calling_is_published_before_popen(self) -> None:
        """Étape 4 : le processus **lancé** relit `etat.json` et y voit RUNNING.

        Le point d'observation est dans le processus fils, pas dans le
        programme : `command()` est désormais résolu avant la publication de
        `CALLING`, si bien qu'y relire l'état ne prouverait plus rien de
        l'ordre entre publication et `Popen`.
        """
        collab = self.build(a=(_QUESTION,), b=())
        marker = self.root / "statut-vu.txt"
        self.a.status_marker = str(marker)
        self.run_engine(collab)
        self.assertEqual(marker.read_text(encoding="utf-8"), "RUNNING")
        self.assertEqual(fakes.read_json(collab / "etat.json")["status"], "WAITING_HUMAN")

    def test_the_command_is_resolved_before_calling_is_published(self) -> None:
        """Un exécutable disparu entre le prévol et l'appel doit être un refus
        sans mutation, pas un faux « possiblement payé » (lot 2)."""
        collab = self.build(a=(_QUESTION,), b=())
        self.run_engine(collab)
        self.assertEqual(self.a.observed_status, ["READY"])

    def test_intention_records_the_observed_version_not_a_provider_name(self) -> None:
        collab = self.build(a=(_QUESTION,), b=())
        self.run_engine(collab)
        call_dir = next((collab / "appels").iterdir())
        intention = fakes.read_json(call_dir / "intention.json")
        self.assertEqual(intention["observed_version"], "fake 0.1.0")
        self.assertEqual(intention["adapter_id"], "fake-a")
        self.assertIsNone(intention["retries"])
        self.assertNotIn("fake", call_dir.name.split("-")[-1])

    def test_intention_traces_the_requested_argv_without_argv_zero(self) -> None:
        """D-6b : trace de l'argv **demandé**, jamais preuve des capacités
        effectives. `argv[0]` en est retiré — c'est le seul chemin absolu de la
        liste, et la règle « aucun chemin absolu persisté » n'a pas à être
        rouverte pour cela."""
        collab = self.build(a=(_QUESTION,), b=())
        self.run_engine(collab)
        call_dir = next((collab / "appels").iterdir())
        intention = fakes.read_json(call_dir / "intention.json")
        argv = intention["invocation_args"]
        self.assertIsInstance(argv, list)
        self.assertNotIn(sys.executable, argv, "argv[0] ne doit pas etre persiste")
        self.assertIn("-c", argv)


class TestTransitions(WorkflowCase):
    def test_question_stops_before_b(self) -> None:
        collab = self.build(a=(_QUESTION,), b=(fakes.review(),))
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.WAITING_HUMAN)  # type: ignore[attr-defined]
        self.assertEqual(self.b.calls, 0)
        self.assertTrue((collab / "echanges" / "0001-question-A.md").exists())

    def test_bloque_hands_back_to_the_human(self) -> None:
        collab = self.build(a=(_DOC,), b=(fakes.review("BLOQUE"),))
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.WAITING_HUMAN)  # type: ignore[attr-defined]
        self.assertEqual(self.etat(collab)["open_finding_ids"], ["B-001"])

    def test_revision_limit_goes_straight_to_promotion(self) -> None:
        collab = self.build(
            a=(_DOC,),
            b=(fakes.review("REVISER"),),
            max_revisions=0,
        )
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)  # type: ignore[attr-defined]
        self.assertEqual(self.a.calls, 1, "un appel de finalisation a ete paye")

    def test_accepter_with_open_blocking_keeps_the_decision_and_hands_back(self) -> None:
        blocking = ({
            "id": "B-009", "severity": "BLOCKING", "disposition": "OPEN",
            "statement": "La reprise ne couvre pas le cas X.",
        },)
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER", findings=blocking),))
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.WAITING_HUMAN)  # type: ignore[attr-defined]
        etat = self.etat(collab)
        self.assertEqual(etat["open_finding_ids"], ["B-009"])
        # La revue est persistée telle quelle : la décision de B n'est pas réécrite.
        review = fakes.read_json(collab / "echanges" / "0002-critique-B.json")
        self.assertEqual(review["decision"], "ACCEPTER")
        incident = fakes.read_json(collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "ACCEPTER_WITH_OPEN_BLOCKING")

    def test_prior_findings_reach_the_next_review(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        self.run_engine(collab)
        self.assertIn("Manque X.", self.b.prompts[1])
        self.assertIn("B-001", self.b.prompts[1])


class TestContractFailure(WorkflowCase):
    def test_unknown_tag_is_an_error_with_the_raw_response_preserved(self) -> None:
        collab = self.build(a=("Bonjour, voici mon document.",), b=())
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.ERROR)  # type: ignore[attr-defined]
        call_dir = next((collab / "appels").iterdir())
        self.assertEqual(
            (call_dir / "reponse_brute.txt").read_text(encoding="utf-8"),
            "Bonjour, voici mon document.",
        )
        incident = fakes.read_json(call_dir / "incident.json")
        self.assertEqual(incident["kind"], "CONTRACT_ERROR")

    def test_lost_prior_finding_is_a_contract_error(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fakes.review("REVISER"), fakes.review("REVISER", findings=())),
        )
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.ERROR)  # type: ignore[attr-defined]


class TestCanonicalReview(WorkflowCase):
    """C-09 / D-8 : `echanges/NNNN-critique-B.json` porte la forme canonique.

    Le programme relit ce fichier comme **registre des constats**. Y écrire le
    texte de B tel quel le rendait illisible par `json.loads` dès que B le
    rendait dans un bloc clôturé — pourtant accepté par le contrat. La preuve
    exacte reste `appels/…/reponse_brute.txt` : aucun troisième artefact.
    """

    def review_path(self, collab: Path) -> Path:
        return collab / "echanges" / "0002-critique-B.json"

    def test_a_fenced_review_is_stored_as_readable_json(self) -> None:
        fenced = "```json\n" + fakes.review("BLOQUE") + "\n```"
        collab = self.build(a=(_DOC,), b=(fenced,))
        self.run_engine(collab)
        stored = fakes.read_json(self.review_path(collab))  # json.loads, sans détour
        self.assertEqual(stored["decision"], "BLOQUE")
        self.assertEqual(stored["findings"][0]["id"], "B-001")
        # Sélection par le champ de rôle, jamais par un glob : `Path.glob` est
        # **insensible à la casse** sous Windows, et `*B*` désignait le dossier
        # de A dès que son UUID contenait un `b`.
        raw = next(p for p in (collab / "appels").iterdir() if p.name.split("-")[1] == "B")
        self.assertTrue(
            (raw / "reponse_brute.txt").read_text(encoding="utf-8").startswith("```json"),
            "la preuve brute doit rester exactement ce que B a rendu",
        )

    def test_an_omitted_severity_is_emitted_as_unknown(self) -> None:
        """B a le droit d'omettre `severity` ; le registre, lui, l'émet toujours."""
        sans_severite = ({"id": "B-007", "disposition": "OPEN", "statement": "Manque Y."},)
        collab = self.build(a=(_DOC,), b=(fakes.review("BLOQUE", findings=sans_severite),))
        self.run_engine(collab)
        stored = fakes.read_json(self.review_path(collab))
        self.assertEqual(stored["findings"][0]["severity"], "UNKNOWN")

    def test_the_open_findings_survive_a_reread_of_the_canonical(self) -> None:
        """Le registre doit se relire sans peine : c'est lui qui alimente le
        prompt de la revue suivante."""
        fenced = "```json\n" + fakes.review("REVISER") + "\n```"
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fenced, fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        self.run_engine(collab)
        self.assertIn("B-001", self.b.prompts[1])
        self.assertIn("Manque X.", self.b.prompts[1])

    def test_no_third_artifact_is_created(self) -> None:
        collab = self.build(a=(_DOC,), b=(fakes.review("BLOQUE"),))
        self.run_engine(collab)
        self.assertEqual(list(collab.rglob("revue_normalisee.json")), [])


class TestPreflight(WorkflowCase):
    def test_unknown_adapter_refused_before_any_mutation(self) -> None:
        collab = self.build(a=(_DOC,), b=(), adapter_a="absent")
        before = (collab / "etat.json").read_text(encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)
        self.assertEqual((collab / "etat.json").read_text(encoding="utf-8"), before)
        self.assertFalse((collab / "appels").exists())

    def test_absent_cli_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.present = False
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_context_only_refused_when_unsupported(self) -> None:
        collab = self.build(a=(_DOC,), b=(), reviewer_access="CONTEXT_ONLY")
        self.b.capabilities = Capabilities(False, True)
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)
        self.assertEqual(self.a.calls, 0)

    def test_model_override_refused_when_unsupported(self) -> None:
        collab = self.build(a=(_DOC,), b=(), model_a="autre-modele")
        self.a.capabilities = Capabilities(True, False)
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_edited_demande_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        (collab / "demande.md").write_text("Autre demande.", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_sources_are_not_rechecked_when_running(self) -> None:
        """`TYPES_DE_MISSION.md` D3 : les sources se contrôlent à la création. Une
        collaboration existante sans corpus reste reprenable, quel que soit son type."""
        collab = self.build(a=(_DOC,), b=(), mission_kind="RECHERCHE")
        self.run_engine(collab)
        self.assertEqual(self.a.calls, 1)

    def test_altered_corpus_manifest_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=(), corpus_captured_at="2026-09-01")
        (collab / "corpus" / "manifeste.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)


class TestCorpusUnderLock(WorkflowCase):
    """C-04 : le contenu du corpus est confronté au manifeste avant chaque appel.

    Comparer la seule empreinte du **texte** du manifeste ne disait rien des
    fichiers qu'il décrit. Dans tous les cas ci-dessous, le refus tombe **avant**
    l'appel — `calls == 0` — parce qu'un corpus qui a bougé fait lire à A et B
    deux références différentes.
    """

    def corpus_collab(self) -> Path:
        return self.build(
            a=(_DOC,), b=(), mission_kind="RECHERCHE", corpus_captured_at="2026-09-01",
            corpus_files={"note.md": "Contenu de reference.", "sous/autre.md": "Second."},
        )

    def refused(self, collab: Path) -> str:
        """Compteur vérifié **hors** du `assertRaises` : sinon un contrôle
        absent ferait échouer sur « exception non levée » et masquerait l'appel
        parti sur un corpus qui a bougé (`RULES.md`)."""
        message = ""
        try:
            self.run_engine(collab)
        except WorkflowError as exc:
            message = str(exc)
        self.assertEqual(self.a.calls, 0, "un appel est parti sur un corpus qui a bouge")
        self.assertNotEqual(message, "", "aucun refus : le corpus n'a pas ete verifie")
        return message

    def test_a_nominal_corpus_passes(self) -> None:
        """Contrôle de sens : sans lui, tous les refus ci-dessous pourraient
        venir d'une fabrique cassée plutôt que du correctif."""
        collab = self.corpus_collab()
        self.run_engine(collab)
        self.assertEqual(self.a.calls, 1)

    def test_an_altered_file_is_refused(self) -> None:
        collab = self.corpus_collab()
        (collab / "corpus" / "fichiers" / "note.md").write_text(
            "Contenu substitue...", encoding="utf-8"
        )
        self.assertIn("note.md", self.refused(collab))

    def test_a_missing_file_is_refused(self) -> None:
        collab = self.corpus_collab()
        (collab / "corpus" / "fichiers" / "sous" / "autre.md").unlink()
        self.assertIn("autre.md", self.refused(collab))

    def test_a_supernumerary_file_is_refused(self) -> None:
        collab = self.corpus_collab()
        (collab / "corpus" / "fichiers" / "glisse.md").write_text("Ajoute.", encoding="utf-8")
        self.assertIn("surnuméraire", self.refused(collab))

    def test_a_symlink_is_refused(self) -> None:
        """Symétrie avec la copie, qui refuse déjà les fichiers non réguliers."""
        collab = self.corpus_collab()
        target = collab / "cible.md"
        target.write_text("Contenu de reference.", encoding="utf-8")
        link = collab / "corpus" / "fichiers" / "note.md"
        link.unlink()
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:  # privilège absent sous Windows
            self.skipTest(f"lien symbolique impossible sur cette machine : {exc}")
        self.assertIn("lien symbolique", self.refused(collab))

    def test_a_manifest_inconsistent_with_the_configuration_is_refused(self) -> None:
        collab = self.corpus_collab()
        manifest = fakes.read_json(collab / "corpus" / "manifeste.json")
        manifest["origin_label"] = "AutreProjet"
        fakes.write_json(collab / "corpus" / "manifeste.json", manifest)
        self.assertIn("ne correspond plus à la configuration", self.refused(collab))

    def test_a_manifest_with_a_broken_schema_is_refused(self) -> None:
        """Le manifeste est la référence : à moitié lu, il ne prouve rien."""
        collab = self.build(
            a=(_DOC,), b=(), corpus_captured_at="2026-09-01",
            corpus_files={"note.md": "Contenu."},
        )
        path = collab / "corpus" / "manifeste.json"
        manifest = fakes.read_json(path)
        manifest["files"][0].pop("taille")
        payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        path.write_text(payload, encoding="utf-8")
        # La configuration est réalignée sur le nouveau texte : sans cela, c'est
        # l'empreinte qui refuserait, et le schéma ne serait jamais atteint.
        config = fakes.read_json(collab / "configuration.json")
        config["corpus_manifest_sha256"] = contracts.normalize(payload).sha256
        fakes.write_json(collab / "configuration.json", config)
        self.assertIn("schéma inattendu", self.refused(collab))


class TestCliFailed(WorkflowCase):
    def test_non_zero_return_code_is_an_incident_not_a_contract_attempt(self) -> None:
        """D-2 : un code de retour non nul est traite avant meme d'essayer le
        contrat - sinon un message de quota sur stdout finirait en CONTRACT_ERROR
        (CONCEPTION_FINALE.md Sec5)."""
        collab = self.build(a=("Vous n'avez plus de credits.",), b=())
        self.a.exit_codes = [1]
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.INTERRUPTED)  # type: ignore[attr-defined]
        etat = self.etat(collab)
        incident = fakes.read_json(collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "CLI_FAILED")
        self.assertEqual(self.a.calls, 1)


class TestPermutations(WorkflowCase):
    def test_the_four_couples_run_the_same_cycle(self) -> None:
        """A et B sont chacun l'un ou l'autre outil : même workflow, même contrat."""
        for id_a in ("outil-1", "outil-2"):
            for id_b in ("outil-1", "outil-2"):
                with self.subTest(a=id_a, b=id_b):
                    tmp = TemporaryDirectory()
                    self.addCleanup(tmp.cleanup)
                    a = fakes.FakeAdapter(id_a, (_DOC,))
                    b = fakes.FakeAdapter(id_b, (fakes.review("ACCEPTER", findings=()),))
                    adapters = {id_a: a, id_b: b} if id_a != id_b else {id_a: a}
                    if id_a == id_b:
                        a.responses = [_DOC, fakes.review("ACCEPTER", findings=())]
                    collab = fakes.collaboration(
                        Path(tmp.name), adapter_a=id_a, adapter_b=id_b,
                        model_a=f"{id_a}-modele-a", model_b=f"{id_b}-modele-b",
                    )
                    state = workflow.run(collab, adapters=adapters, timeout_seconds=30.0)
                    self.assertIs(state.status, Status.AWAITING_APPROVAL)


class TestEffectBoundary(WorkflowCase):
    def test_a_diff_or_shell_block_stays_text(self) -> None:
        """Aucun symbole de production n'applique ni n'exécute : l'absence de
        chemin fonctionnel vaut mieux qu'une détection lexicale (§10)."""
        payload = (
            "IABINOME:DOCUMENT\n"
            "```sh\nrm -rf /\ntouch temoin.txt\n```\n"
            "```diff\n--- a\n+++ b\n```\nhttps://exemple.test/x"
        )
        collab = self.build(a=(payload,), b=(fakes.review("BLOQUE"),))
        self.run_engine(collab)
        document = (collab / "echanges" / "0001-proposition-A.md").read_text(encoding="utf-8")
        self.assertIn("rm -rf /", document)
        self.assertIn("https://exemple.test/x", document)
        self.assertFalse((collab / "temoin.txt").exists())


if __name__ == "__main__":
    unittest.main()
