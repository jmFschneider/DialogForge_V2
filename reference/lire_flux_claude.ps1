# Lit le flux `--output-format stream-json --verbose` d'un appel `claude -p` et n'en garde que ce
# qui prouve ce que l'agent a pu et voulu faire (protocole 3.1, étapes 3 et 4) :
#   - les outils DISPONIBLES annoncés à l'ouverture de la session ;
#   - chaque APPEL d'outil (nom, identifiant) ;
#   - chaque RÉSULTAT d'outil, avec son drapeau d'erreur (un appel refusé par les permissions apparaît
#     ici comme un résultat en erreur, pas comme une absence d'appel).
#
# Usage : .\lire_flux_claude.ps1 .\3-claude-ferme.jsonl
# Aucun appel réseau, aucun quota : lecture d'un fichier.
param([Parameter(Mandatory = $true)][string]$Path)

Get-Content -LiteralPath $Path -Encoding utf8 | ForEach-Object {
    try { $e = $_ | ConvertFrom-Json -ErrorAction Stop } catch { return }
    switch ($e.type) {
        'system' {
            if ($e.subtype -eq 'init' -and $e.tools) {
                [pscustomobject]@{ Evenement = 'outils-disponibles'; Detail = ($e.tools -join ',') }
            }
        }
        'assistant' {
            foreach ($c in @($e.message.content)) {
                if ($c.type -eq 'tool_use') {
                    [pscustomobject]@{ Evenement = 'appel'; Detail = "$($c.name) $($c.id)" }
                }
            }
        }
        'user' {
            foreach ($c in @($e.message.content)) {
                if ($c.type -eq 'tool_result') {
                    [pscustomobject]@{ Evenement = 'resultat'; Detail = "$($c.tool_use_id) erreur=$($c.is_error)" }
                }
            }
        }
    }
}
