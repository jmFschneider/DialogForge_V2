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

Tu ne modifies aucun fichier et n'exécutes rien. Proposer des modifications DANS le
document est au contraire ce qu'on attend de toi."""

_RESEARCH = """\
Cite les sources localisables et leur niveau d'accès réellement vérifié. La source
primaire prime ; qualifie résumé et reprise secondaire. Deux reprises d'une même
origine ne font pas deux preuves. Distingue absent, nul, négatif, inconnu et non
prouvé. Un résultat négatif documenté est un résultat. Conserve contre-preuves,
biais et contextes non couverts. Borne chaque conclusion au contexte étudié.
Si le critère de fin manque, rends QUESTION."""

_B_REVIEW = """\
Tu es B, contradicteur. Cherche omissions, contradictions, faits non établis,
contre-preuves et alternatives sérieuses."""

_B_RULES = """\
Retourne seulement le JSON de revue v1. BLOQUE est réservé à une information humaine
indispensable. Reprends chaque constat antérieur exactement une fois et motive toute
fermeture. Ne déduis pas la décision des sévérités.

Le JSON de revue v1 a exactement cette forme, sans clé en plus :

{"schema_version": 1,
 "decision": "ACCEPTER" | "REVISER" | "BLOQUE",
 "analysis": "critique synthetique en Markdown",
 "findings": [{"id": "B-sujet-001",
               "severity": "BLOCKING" | "MAJOR" | "MINOR" | "NOTE",
               "disposition": "OPEN" | "RESOLVED" | "WITHDRAWN",
               "statement": "le constat, en une phrase"}]}"""

_A_REVISION = """\
Tu es A. Commence par IABINOME:QUESTION si un constat révèle une information humaine
indispensable. Sinon commence par IABINOME:DOCUMENT, puis donne une version complète
qui traite la critique sans masquer les désaccords ni les limites restantes. Ne
réponds pas point par point à la place du livrable."""

_A_FINAL = """\
Tu es A. Commence par IABINOME:QUESTION s'il manque encore une information humaine
indispensable. Sinon commence par IABINOME:DOCUMENT, puis donne le document final
autonome à partir de la version courante. Intègre les apports utiles sans raconter le
dialogue. Garde visibles les incertitudes, les non-décisions et les constats encore
ouverts."""

_CORPUS = "Le corpus local est un instantané du {date}, sous corpus/fichiers/."
_CONTEXT_ONLY = (
    "Tu ne disposes que des éléments ci-dessous ; qualifie ce que tu ne peux pas vérifier."
)


def build_proposal(demande: str, kind: MissionKind, corpus_date: str | None) -> str:
    blocks = [_A_PROPOSAL]
    if kind is MissionKind.RECHERCHE:
        blocks.append(_RESEARCH)
    return _assemble(blocks, corpus_date, {"DEMANDE": demande})


def build_review(
    demande: str,
    document: str,
    prior_findings: str,
    access: ReviewerAccess,
    corpus_date: str | None,
) -> str:
    blocks = [_B_REVIEW]
    if access is ReviewerAccess.CONTEXT_ONLY:
        blocks.append(_CONTEXT_ONLY)
        corpus_date = None
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


def build_final(
    demande: str, document: str, review: str, kind: MissionKind, corpus_date: str | None
) -> str:
    return _a_on_document(_A_FINAL, demande, document, review, kind, corpus_date)


def _a_on_document(
    head: str,
    demande: str,
    document: str,
    review: str,
    kind: MissionKind,
    corpus_date: str | None,
) -> str:
    """§9 ne donne que le bloc de consignes pour la révision et la finalisation.
    Les trois sections de charge sont les mêmes que pour B : sans elles, A
    n'aurait ni l'autorité, ni la version courante, ni la critique à traiter."""
    blocks = [head]
    if kind is MissionKind.RECHERCHE:
        blocks.append(_RESEARCH)
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
