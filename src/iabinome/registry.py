"""Le registre des adaptateurs disponibles — une seule instanciation, partagée
par la CLI et la GUI (`conception/GUI_V1.md` §6.1 : « Agent A/B | adaptateurs
disponibles | registre partagé »). Aucun nom de fournisseur hors de ce module
et de `adapters/` (`CLAUDE.md` §6) : le reste du programme ne lit que des
`adapter_id` opaques.
"""

from __future__ import annotations

from .adapters.base import AgentAdapter
from .adapters.claude import ClaudeAdapter
from .adapters.codex import CodexAdapter

ADAPTERS: dict[str, AgentAdapter] = {"claude": ClaudeAdapter(), "codex": CodexAdapter()}
