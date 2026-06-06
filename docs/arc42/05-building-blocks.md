# 05. Building blocks

## Vue niveau 1

```text
Clients
  |
  v
CanTelcoX API Gateway
  |
  +--> identity-service
  +--> order-service
  +--> catalog-service
  +--> customers-service    (à configurer)
  +--> billing-service      (à configurer)
  +--> audit-service        (à configurer)
```

## Vue niveau 2 - API Gateway

| Bloc | Responsabilité | Fichier |
| --- | --- | --- |
| Application FastAPI | Expose `/health`, `/routes` et le proxy `/v1/...` | `app/main.py` |
| Configuration | Charge les URLs des services amont depuis l'environnement | `app/core/config.py` |
| Conteneurisation | Construit l'image Python/FastAPI | `Dockerfile` |
| Orchestration locale | Lance le gateway avec Docker Compose | `docker-compose.yml` |

## Services amont

| Service | Routes gateway | État de configuration |
| --- | --- | --- |
| `identity-service` | `/v1/users/*`, `/v1/auth/*` | Configuré via `IDENTITY_SERVICE_URL` |
| `order-service` | `/v1/orders/*` | Configuré via `ORDER_SERVICE_URL` |
| `catalog-service` | `/v1/catalog/*` | Configuré via `CATALOG_SERVICE_URL` |
| `customers-service` | `/v1/customers/*` | Prévu, URL à fournir |
| `billing-service` | `/v1/billing/*` | Prévu, URL à fournir |
| `audit-service` | `/v1/audit/*` | Prévu, URL à fournir |

## API Gateway - responsabilités internes

- Déterminer le service cible à partir du segment `/v1/{service}`.
- Préserver le chemin et les paramètres de requête.
- Transmettre la méthode HTTP et le corps de la requête.
- Filtrer les headers hop-by-hop.
- Retourner la réponse amont telle que reçue, après filtrage des headers.
- Retourner `404` pour une famille de route inconnue.
- Retourner `503` pour une famille de route connue mais non configurée.
