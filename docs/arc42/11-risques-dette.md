# 11. Risques et dette technique

## Risques actuels

| Risque | Impact | Mitigation actuelle | Action recommandée |
| --- | --- | --- | --- |
| URLs amont incorrectes | Routes en `502` ou `503` | `/routes` expose la configuration active | Ajouter des tests de connectivité automatisés |
| Services futurs non disponibles | Certaines routes restent inutilisables | Variables vides et réponse `503` | Créer les services et renseigner les URLs |
| Pas de découverte de services | Configuration manuelle fragile | `.env` centralisé pour le gateway | Évaluer DNS interne, service registry ou convention Tailnet |
| Métriques applicatives partielles | Diagnostic limité hors gateway | `/health`, Blackbox Exporter et `/metrics` gateway | Raccorder `/metrics` gateway dans Prometheus et ajouter `/metrics` par service |
| Sécurité API incomplète | Accès potentiellement trop ouvert | CORS limité au développement local | Définir authentification, autorisation et rate limiting |
| Proxy HTTP synchrone | Performance limitée sous forte charge | MVP simple | Évaluer `httpx` async et timeouts par service |

## Dette technique

- Les ADR 0001 à 0005 sont encore peu documentés.
- Les routes clients, facturation et audit sont prêtes mais leurs services ne sont pas encore branchés.
- Les tests automatisés du gateway ne sont pas présents dans ce dépôt.

## Points à clarifier

- Noms définitifs des services amont pour clients, facturation et audit.
- Ports et adresses Tailnet de ces services.
- Politique d'authentification au niveau gateway.
- Format cible des logs et corrélation des requêtes entre services.
