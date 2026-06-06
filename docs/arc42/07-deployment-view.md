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

## Services amont connus

| Service | Adresse actuelle |
| --- | --- |
| `identity-service` | `http://100.83.57.43:8020` |
| `order-service` | `http://100.108.225.1:8030` |
| `catalog-service` | `http://100.95.65.46:8010` |
| `customers-service` | À configurer |
| `billing-service` | À configurer |
| `audit-service` | À configurer |

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
Les métriques applicatives Prometheus sont prévues comme une étape d'instrumentation ultérieure.

## Commandes utiles

```bash
sudo docker compose up --build
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/routes
```
