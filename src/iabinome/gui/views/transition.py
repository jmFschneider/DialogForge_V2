"""Le formulaire de création quand il poursuit une recherche acceptée
(`conception/PARCOURS_MISSION_CONCEPTION.md` §4.2, §4.3) : ce que l'instantané préparé y
met, et comment la demande éditée parvient à F. Aucune règle ici : la façade juge."""

from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from ... import facade, model_catalog

if TYPE_CHECKING:
    from .creation import CreationView


def fill(view: CreationView, follow_up: facade.FollowUp) -> None:
    """Dossier, mandat, réglages hérités de la recherche, et le corpus remplacé par sa
    mention. Un modèle absent du catalogue reste proposé, étiqueté « hérité de la
    recherche » : il n'est jamais remplacé sans avertissement."""
    from .creation import _ACCESS, _DESIGN, _NON_SPECIFIE

    config = follow_up.config
    view.bind("<Destroy>", lambda _event: follow_up.discard())  # le dossier jetable
    view._dossier.set(str(follow_up.default_dest))
    view._kind.set(_DESIGN)
    view._demande_text.insert("1.0", follow_up.mandate)
    sync_idea(view)
    for spec, agent, model, effort in (
        (config.agent_a, view._agent_a, view._model_a, view._effort_a),
        (config.agent_b, view._agent_b, view._model_b, view._effort_b),
    ):
        view._model_catalog, shown = model_catalog.inherit(
            view._model_catalog, spec.adapter_id, spec.model,
        )
        agent.set(spec.adapter_id)
        model.set(shown)
        effort.set(spec.effort or _NON_SPECIFIE)
    view._revisions.set(str(config.max_revisions))
    view._reviewer.set(next(k for k, v in _ACCESS.items() if v is config.reviewer_access))
    view._web_access.set(config.web_access)
    view._sync_model("A")
    view._sync_model("B")
    for child in view._corpus_frame.winfo_children():
        child.destroy()
    label = facade.follow_up_label(follow_up)
    ttk.Label(view._corpus_frame, text=label, wraplength=560).pack(anchor="w")


def sync_idea(view: CreationView) -> None:
    """F lit la demande **telle qu'elle est à l'écran** : une correction du mandat avant le
    cadrage lui parvient. Sans transition, l'idée de départ reste libre."""
    if view._follow_up is not None:
        idea = view._framing_panel.idea
        idea.delete("1.0", "end")
        idea.insert("1.0", view._current_text())
