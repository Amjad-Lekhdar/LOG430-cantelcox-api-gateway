# 07. Vue de déploiement

Cette section correspond à la vue physique de Kruchten 4+1.
Tailscale est utilisé comme couche réseau privée entre les machines du laboratoire.
Le gateway s'appuie sur les adresses Tailnet configurées dans `.env` pour appeler les services amont.

## 7.1 Déploiement local et laboratoire

```text
Machine hôte / laboratoire
  |
  +--> Docker Compose: api-gateway
  |
  +--> Tailnet
        +--> identity-service
        +--> order-service
        +--> line-service
        +--> catalog-service
        +--> customers-service
        +--> billing-service
        +--> audit-service
        +--> free5GC core
        +--> observability
```

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

## 7.2 Noeuds de déploiement

| Noeud | Hébergeur | Quantité | Rôle |
| --- | --- | --- | --- |
| API Gateway | Docker Compose avec `network_mode: host` | 1 | Point d'entrée HTTP local/laboratoire |
| `identity-service` | VM/LXC Tailnet | 1 | Utilisateurs et authentification |
| `order-service` | VM/LXC Tailnet | 1 | Commandes |
| `line-service` | VM/LXC Tailnet | 1 | Lignes, SIM/SUPI et activations |
| `catalog-service` | VM/LXC Tailnet | 1..4 | Catalogue, service pilote pour load balancing |
| `customers-service` | VM/LXC Tailnet | 1 | Clients |
| `billing-service` | VM/LXC Tailnet | 1 | Facturation |
| `audit-service` | VM/LXC Tailnet | 1 | Audit append-only |
| free5GC core | VM/LXC Tailnet ou hôte laboratoire | 1 | Coeur réseau 5G et fonctions AMF/SMF/UDM/UDR/NRF/UPF |
| Observability | VM/LXC ou hôte dédié | 1 | Prometheus, Grafana, Blackbox Exporter |

## 7.3 Mapping blocs vers noeuds

| Bloc logique | Noeud de déploiement |
| --- | --- |
| API Gateway | Conteneur Docker construit depuis ce dépôt |
| `identity-service` | `http://100.83.57.43:8020` |
| `order-service` | `http://100.108.225.1:8030` |
| `line-service` | Adresse Tailnet/LXC à renseigner, port cible `8080` |
| `catalog-service` | `http://100.95.65.46:8040` ou HAProxy `http://127.0.0.1:18040` |
| `customers-service` | `http://100.99.167.126:8050` |
| `billing-service` | `http://100.114.185.38:8060` |
| `audit-service` | `http://100.94.161.70:8070` |
| free5GC core | Adresse Tailnet/LXC à renseigner côté adapter d'activation |
| Observability | `http://100.87.177.66` |

Les conteneurs `customers-service`, `billing-service` et `audit-service` sont joints au Tailnet. Tant que leurs applications ne sont pas démarrées sur les ports indiqués, le gateway retourne `502` pour ces routes.
Le coeur free5GC est un voisin réseau spécialisé et n'est pas routé publiquement par le gateway. Ses paramètres d'accès doivent rester dans la configuration de `line-service`.

## 7.4 Load balancing

Une première cible de load balancing est disponible pour `catalog-service`.
Le composant `catalog-load-balancer` utilise HAProxy et s'active avec le profil Compose `load-balancing`.

`catalog-service` est le service pilote retenu pour démontrer N = 1..4 instances et le kill d'instance en charge. Le choix évite de dupliquer le même composant devant tous les services avant stabilisation complète des endpoints métier. Le patron reste réplicable en ajoutant un load balancer dédié par service et en configurant la variable d'URL amont correspondante du gateway.

```text
docker-compose.yml
  catalog-load-balancer
    image: haproxy:3.0-alpine
    network_mode: host
    bind: 127.0.0.1:18040
    config: infra/load-balancer/haproxy/catalog.cfg
```

Le gateway reste stateless et continue de lire `CATALOG_SERVICE_URL`. En mode load balancing, cette variable pointe vers `http://127.0.0.1:18040`; HAProxy applique ensuite une stratégie `roundrobin` vers les instances catalogue actives et vérifie leur santé avec `GET /health`.

## 7.5 Observability

L'observabilité est déployée dans un environnement dédié nommé `cantelcox-observability`.
La cible Tailnet connue pour l'observabilité est `100.87.177.66`.

La pile cible contient:

- Prometheus sur le port `9090`.
- Grafana sur le port `3000`.
- Blackbox Exporter sur le port `9115`.

Le modèle initial utilise Blackbox Exporter pour sonder les endpoints `/health` des services.
Le gateway expose des métriques applicatives Prometheus sur `/metrics`. Les autres services peuvent être ajoutés progressivement selon le même patron.

## 7.6 Commandes utiles

```bash
sudo docker compose up --build
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/routes
curl -i http://127.0.0.1:8000/metrics
```
