"""Gabarits de prompts — critères intellectuels, pas pseudo-confinement.

Les capacités sont fixées avant la construction du prompt : la ligne d'accès
**informe**, elle n'interdit pas. Le prévol fait déjà le travail, et le prompt
ne confine rien (CONCEPTION_FINALE.md §9). Alléger, ne pas durcir.
"""

from __future__ import annotations

from .models import MissionKind, ReviewerAccess

_A_PROPOSAL = """\
Tu es A, auteur principal. La demande ci-dessous est l'unique autorité.

Commence par IABINOME:QUESTION si une information absente changerait substantiellement
le périmètre, la méthode ou la conclusion ; pose alors seulement ces questions.
Sinon commence par IABINOME:DOCUMENT et produis un document Markdown autonome.

Distingue faits, inférences, recommandations et incertitudes. Nomme tes limites de
preuve. Chaque recommandation dit jusqu'à quand elle est réversible et quel acte
la referme.

Tu ne produis aucun effet hors de ta réponse : tu ne modifies ni ne crées aucun
fichier. **Lire** ceux du dossier courant t'est en revanche ouvert, et le corpus est
là pour ça. Proposer des modifications DANS le document est ce qu'on attend de toi,
pas les appliquer."""

_RESEARCH = """\
Cite les sources localisables et leur niveau d'accès réellement vérifié. La source
primaire prime ; qualifie résumé et reprise secondaire. Deux reprises d'une même
origine ne font pas deux preuves. Distingue absent, nul, négatif, inconnu et non
prouvé. Un résultat négatif documenté est un résultat. Conserve contre-preuves,
biais et contextes non couverts. Borne chaque conclusion au contexte étudié.
Une source web se cite par son adresse et sa date de consultation.
Si le critère de fin manque, rends QUESTION."""

_CONCEPTION = """\
Pars du dossier fourni : ses faits établis ne se rouvrent pas sans contre-preuve.
Compare les options sérieuses et motive le choix retenu. Nomme risques, hypothèses
et points ouverts. Termine par des étapes de réalisation vérifiables, assez précises
pour être confiées au développement."""

_KIND_BLOCK = {MissionKind.RECHERCHE: _RESEARCH, MissionKind.CONCEPTION: _CONCEPTION}

_B_REVIEW = """\
Tu es B, contradicteur. Cherche omissions, contradictions, faits non établis,
contre-preuves et alternatives sérieuses."""

_B_RULES = """\
Retourne seulement le JSON de revue v2. BLOQUE est réservé à une information humaine
indispensable. Reprends chaque constat antérieur exactement une fois, avec son énoncé
inchangé : pourquoi il reste ouvert, se résout ou se retire va dans "justification",
jamais dans "statement". Une fermeture sans justification reste ouverte. Ne déduis pas la
décision des sévérités.

Le JSON de revue v2 a exactement cette forme, sans clé en plus :

{"schema_version": 2,
 "decision": "ACCEPTER" | "REVISER" | "BLOQUE",
 "analysis": "critique synthetique en Markdown",
 "findings": [{"id": "B-sujet-001",
               "severity": "BLOCKING" | "MAJOR" | "MINOR" | "NOTE",
               "disposition": "OPEN" | "RESOLVED" | "WITHDRAWN",
               "statement": "le constat, en une phrase, énoncé initial",
               "justification": "pourquoi cette disposition"}]}"""

_A_REVISION = """\
Tu es A. Commence par IABINOME:QUESTION si un constat révèle une information humaine
indispensable. Sinon commence par IABINOME:DOCUMENT, puis donne une version complète
qui traite la critique sans masquer les désaccords ni les limites restantes. Le
document n'est pas une réponse point par point : celle-ci est à part.

Après le document, s'il y a des constats OPEN dans la critique, écris une ligne
IABINOME:REPONSES puis un objet JSON qui répond à chacun, une fois, avec son id :

{"schema_version": 1,
 "responses": [{"id": "B-sujet-001",
                "response": "CORRIGE" | "CONTESTE" | "REPORTE" | "ARBITRAGE",
                "justification": "pourquoi"}]}

CORRIGE : la version corrige le point. CONTESTE : tu maintiens ta position, motivée.
REPORTE : hors périmètre ou sous condition, dis laquelle. ARBITRAGE : seul l'humain peut
trancher, pose la question. Sauf CORRIGE, la justification est obligatoire."""

_B_TARGETED = """\
C'est une relecture ciblée : A a corrigé la version que tu as examinée. Ne reprends pas
la critique depuis le début. Examine seulement (1) chaque objection antérieure et ce que
A y a répondu, (2) les régressions que la correction a pu introduire. Une observation
nouvelle hors de ce périmètre se note en NOTE : elle sera présentée à l'humain, elle
n'ouvre pas de tour de plus. Si rien ne reste à corriger dans ce périmètre, rends
ACCEPTER : la version examinée sera livrée telle quelle, sans réécriture."""

_CORPUS = (
    "Le corpus local est un instantané du {date}, à lire sous corpus/fichiers/ : c'est"
    " ta matière, et la seule."
)
_CONTEXT_ONLY = (
    "Tu ne disposes que des éléments ci-dessous ; qualifie ce que tu ne peux pas vérifier."
)


def build_proposal(demande: str, kind: MissionKind, corpus_date: str | None) -> str:
    blocks = [_A_PROPOSAL, _KIND_BLOCK[kind]]
    return _assemble(blocks, corpus_date, {"DEMANDE": demande})


def build_review(
    demande: str,
    document: str,
    prior_findings: str,
    access: ReviewerAccess,
    corpus_date: str | None,
    targeted: bool = False,
) -> str:
    """`targeted` : la revue suit une correction de A (1.3), et se limite aux
    objections traitées et aux régressions."""
    blocks = [_B_REVIEW]
    if access is ReviewerAccess.CONTEXT_ONLY:
        blocks.append(_CONTEXT_ONLY)
        corpus_date = None
    if targeted:
        blocks.append(_B_TARGETED)
    blocks.append(_B_RULES)
    return _assemble(
        blocks,
        corpus_date,
        {"DEMANDE": demande, "DOCUMENT COURANT": document, "CONSTATS ANTÉRIEURS": prior_findings},
    )


def build_revision(
    demande: str, document: str, review: str, kind: MissionKind, corpus_date: str | None
) -> str:
    return _a_on_document(_A_REVISION, demande, document, review, kind, corpus_date)


def _a_on_document(
    head: str,
    demande: str,
    document: str,
    review: str,
    kind: MissionKind,
    corpus_date: str | None,
) -> str:
    """§9 ne donne que le bloc de consignes pour la révision. Les trois sections
    de charge sont les mêmes que pour B : sans elles, A n'aurait ni l'autorité,
    ni la version courante, ni la critique à traiter. Il n'y a plus de
    finalisation par A : la version examinée est promue telle quelle (1.3)."""
    blocks = [head, _KIND_BLOCK[kind]]
    return _assemble(
        blocks,
        corpus_date,
        {"DEMANDE": demande, "DOCUMENT COURANT": document, "CRITIQUE": review},
    )


def _assemble(blocks: list[str], corpus_date: str | None, sections: dict[str, str]) -> str:
    parts = list(blocks)
    if corpus_date is not None:
        parts.append(_CORPUS.format(date=corpus_date))
    parts.extend(f"{title}\n{body}" for title, body in sections.items())
    return "\n\n".join(parts) + "\n"


# -- Cadrage avec agent F (`conception/CADRAGE_AGENT.md` §7) --------------------------------

_F_START = """\
Tu es l'agent F de cadrage de DialogForge.

Cette conversation utilise une session persistante. Conserve pendant toute la
session les informations utiles lues et les réponses humaines. Elles ne seront
pas retransmises intégralement à chaque tour.

Transforme progressivement l'idée en demande autonome. Si corpus/fichiers/
contient des fichiers, lis maintenant ceux qui sont utiles. Il s'agit d'une
copie isolée : n'écris et n'exécute rien.

N'invente aucune décision. Une observation du corpus n'est pas un choix humain.
Pose un seul arbitrage principal, éventuellement avec deux ou trois
alternatives réelles.

Le premier groupe admet au plus trois réponses humaines. Lorsque sa limite est
atteinte, rends IABINOME:CADRAGE_PRET. Si l'idée suffit déjà, propose-la
maintenant."""

_F_CONTINUE = """\
Continue le même cadrage en utilisant le contexte déjà conservé dans cette
session.

La réponse humaine peut être partielle, hésitante, hors sujet ou corriger une
décision antérieure. Mets ton état à jour sans inventer.

Si REPONSES_DANS_LE_GROUPE atteint LIMITE_DU_GROUPE, rends obligatoirement
IABINOME:CADRAGE_PRET. Sinon, pose le seul arbitrage le plus utile ou propose
la clôture immédiatement."""

_F_REOPEN = """\
L'utilisateur refuse pour l'instant la clôture et {what}. Cet apport est la
première réponse d'un nouveau groupe de limite deux : tu peux poser au plus une
nouvelle question avant de rendre une nouvelle proposition IABINOME:CADRAGE_PRET.
Mets à jour le cadrage sans inventer."""

_F_DRAFT = """\
Rédige maintenant la demande autonome à partir de l'ensemble de cette session.

N'invente aucune décision. Conserve explicitement les inconnues, limites et
désaccords encore ouverts. Ne mentionne ni la conversation ni les agents.

Commence par IABINOME:DEMANDE et ne rends ensuite que le Markdown.

FORMAT
# Demande
## Objectif
## Livrable
## Sources
## Contraintes
## Non-objectifs
## Critères de fin"""

_F_CONTRACTS = """\
Chaque réponse conversationnelle commence par l'une de ces deux lignes.

IABINOME:CADRAGE_QUESTION
QUESTION
Un seul arbitrage principal, éventuellement accompagné de choix.
POURQUOI
Effet de la réponse sur la future demande.
ETAT_CADRAGE
DECISIONS, HESITATIONS, CONTRADICTIONS, FICHIERS_CONSULTES, QUESTIONS_OUVERTES
(une liste chacune, chemins logiques pour les fichiers ; une liste vide s'écrit - AUCUNE)

IABINOME:CADRAGE_PRET
RESUME
Le mandat compris.
SANS_REPONSE
- Question : ... / Effet possible : ... (chaque inconnue restante)
APERCU
Objectif, Livrable, Sources, Contraintes, Non-objectifs, Critères de fin : une ligne chacun.
ETAT_CADRAGE
(comme ci-dessus)"""

_F_RETRY = """\
Ta dernière réponse n'a pas pu être retenue : {motif}. Rends-la de nouveau selon
le contrat, sans changer de sujet."""


def _counters(group: int, answers: int, limit: int) -> dict[str, str]:
    return {
        "GROUPE": str(group), "REPONSES_DANS_LE_GROUPE": str(answers),
        "LIMITE_DU_GROUPE": str(limit),
    }


def build_framing_start(idea: str, *, draft: bool = False) -> str:
    """Le seul envoi qui porte l'idée et la consultation du corpus (§6.2). `draft` :
    `/clore` avant tout échange — la rédaction suit dans le même envoi (A2)."""
    text = _assemble(
        [_F_START], None, {"IDEE": idea, **_counters(1, 0, 3), "CONTRATS": _F_CONTRACTS},
    )
    return text + "\n" + _F_DRAFT + "\n" if draft else text


def build_framing_continue(answer: str, group: int, answers: int, limit: int) -> str:
    return _assemble([_F_CONTINUE], None, {
        "DERNIERE_REPONSE_OU_INSTRUCTION_HUMAINE": answer, **_counters(group, answers, limit),
    })


def build_framing_reopen(text: str, group: int, *, correction: bool) -> str:
    """« Continuer » et « Corriger un point » : même groupe, même compteur (A1)."""
    what = "corrige le point suivant" if correction else "poursuit le cadrage"
    title = "CORRECTION_HUMAINE" if correction else "REPONSE_HUMAINE"
    return _assemble(
        [_F_REOPEN.format(what=what)], None, {title: text, **_counters(group, 1, 2)}
    )


def build_framing_draft() -> str:
    """Ni l'idée ni la transcription : elles sont dans la session (§6.6, §7.4)."""
    return _F_DRAFT + "\n"


def build_framing_retry(motif: str) -> str:
    return _F_RETRY.format(motif=motif) + "\n"
