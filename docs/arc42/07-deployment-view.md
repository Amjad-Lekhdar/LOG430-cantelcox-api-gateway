# 07. Deployment view

## Déploiement local et laboratoire

Le dépôt actuel construit et lance le gateway avec Docker Compose.
Les services métier ne sont pas construits depuis ce dépôt lorsqu'ils tournent déjà sur des VM/LXC.

```text
docker-compose.yml
  api-gateway
    build: .
    network_mode: host
    env_file: .env
```

Le mode réseau `host` permet au conteneur gateway d'utiliser la connectivité réseau de la machine hôte, notamment vers Tailnet et vers les services locaux exposés sur `127.0.0.1`.

## Load balancing

Une première cible de load balancing est disponible pour `catalog-service`.
Le composant `catalog-load-balancer` utilise HAProxy et s'active avec le profil
Compose `load-balancing`.

`catalog-service` est le service pilote retenu pour démontrer N = 1..4
instances et le kill d'instance en charge. Le choix évite de dupliquer le même
composant devant tous les services avant stabilisation complète des endpoints
métier. Le patron reste réplicable en ajoutant un load balancer dédié par
service et en configurant la variable d'URL amont correspondante du gateway.

```text
docker-compose.yml
  catalog-load-balancer
    image: haproxy:3.0-alpine
    network_mode: host
    bind: 127.0.0.1:18040
    config: infra/load-balancer/haproxy/catalog.cfg
```

Le gateway reste stateless et continue de lire `CATALOG_SERVICE_URL`. En mode
load balancing, cette variable pointe vers `http://127.0.0.1:18040`; HAProxy
applique ensuite une stratégie `roundrobin` vers les instances catalogue
actives et vérifie leur santé avec `GET /health`.

## Services amont connus

| Service | Adresse actuelle |
| --- | --- |
| `identity-service` | `http://100.83.57.43:8020` |
| `order-service` | `http://100.108.225.1:8030` |
| `catalog-service` | `http://100.95.65.46:8040` |
| `customers-service` | `http://100.99.167.126:8050` |
| `billing-service` | `http://100.114.185.38:8060` |
| `audit-service` | `http://100.94.161.70:8070` |

Les trois derniers conteneurs sont joints au Tailnet. Tant que leurs applications ne sont pas démarrées sur les ports indiqués, le gateway retourne `502` pour ces routes.

## Observability

L'observabilité est déployée dans un environnement dédié nommé `cantelcox-observability`.

Cet environnement peut être un conteneur LXC, une VM ou un hôte Linux dédié.
Il contient la pile de monitoring et sa configuration, tandis que les microservices applicatifs peuvent tourner sur des VM séparées.

La cible Tailnet connue pour l'observabilité est `100.87.177.66`.

La pile cible contient:

- Prometheus on port `9090`
- Grafana on port `3000`
- Blackbox Exporter on port `9115`

Le modèle initial utilise Blackbox Exporter pour sonder les endpoints `/health` des services.
Le gateway expose des métriques applicatives Prometheus sur `/metrics`. Les métriques applicatives des autres services restent à instrumenter ou raccorder progressivement.

## Commandes utiles

```bash
sudo docker compose up --build
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/routes
```
