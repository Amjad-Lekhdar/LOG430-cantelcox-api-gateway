# CanTelcoX API Gateway

Façade REST FastAPI du système CanTelcoX. Le gateway expose une URL d'entrée
unique et relaie les requêtes vers les microservices accessibles sur le
Tailnet.

Le gateway ne contient ni logique métier ni base de données. Les règles métier
et la persistance PostgreSQL appartiennent aux services responsables.

## État actuel

| Service | Route du gateway | Cible Tailnet | État |
| --- | --- | --- | --- |
| `identity-service` | `/v1/users/*`, `/v1/auth/*` | `100.83.57.43:8020` | Configuré |
| `order-service` | `/v1/orders/*` | `100.108.225.1:8030` | Configuré |
| `catalog-service` | `/v1/catalog/*` | `100.95.65.46:8040` | Configuré |
| `customers-service` | `/v1/customers/*` | `100.99.167.126:8050` | Déployé |
| `billing-service` | `/v1/billing/*` | `100.114.185.38:8060` | Déployé |
| `audit-service` | `/v1/audit/*` | `100.94.161.70:8070` | LXC créé, application à déployer |

L'environnement d'observabilité est accessible sur `100.87.177.66`.

## Prérequis

- Python 3.12;
- Docker et Docker Compose pour le lancement conteneurisé;
- accès au Tailnet pour joindre les services LXC.

## Lancement local

Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interfaces utiles :

```text
Swagger: http://127.0.0.1:8000/docs
Santé:   http://127.0.0.1:8000/health
Routes:  http://127.0.0.1:8000/routes
Metrics: http://127.0.0.1:8000/metrics
```

## Lancement avec Docker

Le fichier `docker-compose.yml` utilise le réseau de l'hôte afin que le
conteneur puisse atteindre les adresses Tailscale :

```bash
docker compose up -d --build
docker compose ps
curl -i http://127.0.0.1:8000/health
```

Arrêt :

```bash
docker compose down
```

## Load balancing catalogue

Une première tranche de load balancing est disponible pour `catalog-service`
avec HAProxy. Le gateway reste inchangé: il pointe vers une seule URL, et
HAProxy distribue ensuite les requêtes vers les instances catalogue.

`catalog-service` sert de service pilote pour démontrer l'exigence N = 1..4
instances, les mesures de performance et le kill d'instance en charge. Le même
patron peut ensuite être répliqué aux autres services avec un backend HAProxy
dédié et une variable d'URL amont différente.

Lancer le gateway et le load balancer catalogue:

```bash
docker compose --profile load-balancing up -d --build
```

Pointer le gateway vers le load balancer local:

```dotenv
CATALOG_SERVICE_URL=http://127.0.0.1:18040
```

Un exemple complet est disponible dans `.env.load-balancing.example`.

Le fichier HAProxy est dans
`infra/load-balancer/haproxy/catalog.cfg`. Par défaut, il utilise l'instance
actuelle:

```text
catalog-1 -> 100.95.65.46:8040
```

Pour comparer N = 1, 2, 3, 4 instances, démarrer des instances additionnelles
du catalogue sur des ports distincts, puis activer les lignes `catalog-2` à
`catalog-4` dans `catalog.cfg`.

Vérifications utiles:

```bash
curl -i http://127.0.0.1:18040/health
curl -i http://127.0.0.1:8000/v1/catalog/plans
```

Test de charge k6:

```bash
k6 run tests/load/catalog-through-gateway.js
```

## Configuration

Le gateway charge automatiquement le fichier `.env` :

```dotenv
IDENTITY_SERVICE_URL=http://100.83.57.43:8020
ORDER_SERVICE_URL=http://100.108.225.1:8030
CATALOG_SERVICE_URL=http://100.95.65.46:8040
CUSTOMERS_SERVICE_URL=http://100.99.167.126:8050
BILLING_SERVICE_URL=http://100.114.185.38:8060
AUDIT_SERVICE_URL=http://100.94.161.70:8070
```

Après une modification de `.env`, redémarrer le gateway :

```bash
docker compose up -d --build
```

## Routage

```text
GET /health
GET /metrics
GET /routes

/v1/users/*      -> identity-service
/v1/auth/*       -> identity-service
/v1/orders/*     -> order-service
/v1/catalog/*    -> catalog-service
/v1/customers/*  -> customers-service
/v1/billing/*    -> billing-service
/v1/audit/*      -> audit-service
```

Le gateway conserve la méthode HTTP, le chemin, le corps, les paramètres de
requête et les headers applicatifs. Les headers HTTP hop-by-hop sont retirés.

## Vérification

Vérifier la configuration chargée :

```bash
curl -s http://127.0.0.1:8000/routes
```

Vérifier les métriques Prometheus du gateway :

```bash
curl -s http://127.0.0.1:8000/metrics | grep api_gateway_http
```

Les métriques applicatives exposées sont :

```text
api_gateway_http_requests_total
api_gateway_http_request_duration_seconds
api_gateway_http_requests_in_progress
```

## Tests automatisés

Installer les dépendances puis lancer la suite gateway :

```bash
pip install -r requirements.txt
pytest
```

Les tests couvrent `/health`, `/routes`, les erreurs `404`, `503`, `502` et le
proxy vers un service amont simulé.

Tester directement les services déployés :

```bash
curl -i http://100.83.57.43:8020/health
curl -i http://100.108.225.1:8030/health
curl -i http://100.95.65.46:8040/health
```

Tester les services récemment ajoutés :

```bash
curl -i http://100.99.167.126:8050/health
curl -i http://100.114.185.38:8060/health
```

Le service d'audit ne répondra qu'après son déploiement :

```bash
curl -i http://100.94.161.70:8070/health
```

Vérifier Tailscale depuis l'hôte LXD :

```bash
lxc exec customers-service -- tailscale status
lxc exec billing-service -- tailscale status
lxc exec audit-service -- tailscale status
```

## Gestion des erreurs

| Situation | Réponse |
| --- | --- |
| Famille de route inconnue | `404` |
| Service connu sans URL configurée | `503` |
| URL configurée, mais service inaccessible | `502` |
| Erreur HTTP du service amont | Statut et contenu du service conservés |

`customers-service` écoute sur le port hôte `8050`, redirigé par Docker vers
son port interne `8000`. `billing-service` écoute sur `8060`. Le gateway
retournera `502` pour `/v1/audit/*` tant que `audit-service` ne sera pas
déployé sur `8070`.

## Services à compléter

L'ordre de réalisation recommandé est :

1. `audit-service`;
2. `customers-service`;
3. `billing-service`;
4. compléments MFA, catalogue versionné, idempotence et activation dans les
   services existants.

Chaque service métier doit posséder sa propre base PostgreSQL et suivre
l'architecture hexagonale décrite dans les directives d'implémentation.

## Documentation

- [Directives d'implémentation des services](docs/directives-implementation-services.md)
- [Dossier d'architecture](docs/Gabarit_LOG430_Phase1_Architecture_v3_1.md)
- [Documentation Arc42](docs/arc42.md)
- [Runbook](docs/runbook.md)
- [Backlog](docs/backlog.md)
- [ADR Tailscale](docs/adr/0006-utilisation-tailscale.md)
