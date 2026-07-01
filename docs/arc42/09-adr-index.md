# 09. Décisions d'architecture - index ADR

Chaque ADR vit dans son propre fichier sous `docs/adr/NNNN-titre.md`.

| # | Titre | Statut | Date |
| --- | --- | --- | --- |
| [0001](../adr/0001-architecture-microservices.md) | Architecture microservices alignée sur les bounded contexts | Accepted | 2026-06-23 |
| [0002](../adr/0002-api-gateway.md) | API Gateway comme point d'entrée HTTP unique | Accepted | 2026-06-23 |
| [0003](../adr/0003-database-per-service.md) | Persistance database-per-service | Accepted | 2026-06-23 |
| [0004](../adr/0004-idempotence-audit-billing.md) | Idempotence, facturation exactly-once et audit append-only | Accepted | 2026-06-23 |
| [0005](../adr/0005-observability-lxc.md) | Environnement observabilité dédié | Accepted | 2026-06-08 |
| [0006](../adr/0006-utilisation-tailscale.md) | Utilisation de Tailscale pour le réseau privé | Accepted | 2026-06-08 |
| [0007](../adr/0007-choix-frontend.md) | Choix du frontend Expo React Native Web | Accepted | 2026-06-28 |

Statuts possibles: Proposed, Accepted, Deprecated, Superseded by NNNN.

## Décisions reflétées dans l'architecture actuelle

- Le gateway est le point d'entrée HTTP unique pour les clients.
- Les services métier sont adressés par URLs configurables.
- L'observabilité est séparée des services applicatifs.
- Les services futurs peuvent être préparés dans la table de routage avant leur disponibilité effective.
- Le frontend client utilise l'API Gateway comme unique point d'accès au BSS.
- free5GC est intégré derrière un adapter d'activation, hors API publique du gateway.
