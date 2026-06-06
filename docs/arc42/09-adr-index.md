# 09. Index ADR

| ADR | Sujet | Statut connu |
| --- | --- | --- |
| [ADR 0001](../adr/0001-architecture-microservices.md) | Architecture microservices | À compléter |
| [ADR 0002](../adr/0002-architecture-hexagonale.md) | Architecture hexagonale | À compléter |
| [ADR 0003](../adr/0003-api-gateway.md) | API Gateway | À compléter |
| [ADR 0004](../adr/0004-database-per-service.md) | Database per service | À compléter |
| [ADR 0005](../adr/0005-idempotence-audit-billing.md) | Idempotence, audit et billing | À compléter |
| [ADR 0006](../adr/0006-observability-lxc.md) | Environnement observabilité dédié | Accepté |

## Décisions reflétées dans l'architecture actuelle

- Le gateway est le point d'entrée HTTP unique pour les clients.
- Les services métier sont adressés par URLs configurables.
- L'observabilité est séparée des services applicatifs.
- Les services futurs peuvent être préparés dans la table de routage avant leur disponibilité effective.
