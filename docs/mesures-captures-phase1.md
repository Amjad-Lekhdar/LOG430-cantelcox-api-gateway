# Mesures et captures - Phase 1 LOG430

Ce fichier sert de zone de collecte avant intégration dans
`docs/Gabarit_LOG430_Phase1_Architecture_v3_1.md`.

Déposer les captures dans `docs/captures/` avec des noms explicites, puis
remplir les tableaux ci-dessous. Les captures utiles doivent montrer la date ou
l'heure, la cible testée, la période observée et les valeurs visibles.

## 1. Préparation

Créer le dossier de captures:

```bash
mkdir -p docs/captures
```

Vérifier que le gateway répond:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/routes
curl -i http://127.0.0.1:8000/metrics
```

Vérifier l'observabilité:

```text
Grafana:    http://100.87.177.66:3000
Prometheus: http://100.87.177.66:9090
```

## 2. Captures prioritaires

| ID | Section gabarit | Preuve attendue | Capture à envoyer | Fichier cible | Statut |
| --- | --- | --- | --- | --- | --- |
| C01 | §8.8, §10.5 | Dashboard Grafana 4 Golden Signals gateway | Latence P95, trafic, erreurs, saturation sur la même période | `docs/captures/grafana/c01-latence-p95-p99-health.png` à `docs/captures/grafana/c06-rps-applicatif-gateway.png` | Intégré au gabarit |
| C02 | §8.8 | Prometheus scrape `/metrics` gateway UP | Page Targets ou requête `up{job=...}` | `docs/captures/prometheus/c02-prometheus-targets-gateway-up.png` | Intégré au gabarit |
| C03 | §10.5 | Résultat k6 campagne charge catalogue via gateway | Terminal complet avec checks, RPS, P95, erreurs | `docs/captures/k6/c03-k6-catalog-gateway.png` | Intégré au gabarit |
| C04 | §10.6 | Load balancing N=2 | HAProxy/Grafana/k6 montrant RPS, P95, erreurs | `docs/captures/k6-load-balancing/c04-lb-n2.png` | Intégré au gabarit |
| C05 | §10.6 | Load balancing N=3 | HAProxy/Grafana/k6 montrant RPS, P95, erreurs | `docs/captures/k6-load-balancing/c05-lb-n3.png` | Intégré au gabarit |
| C06 | §10.6 | Load balancing N=4 | HAProxy/Grafana/k6 montrant RPS, P95, erreurs | `docs/captures/k6-load-balancing/c06-lb-n4.png` | Intégré au gabarit |
| C07 | §10.6 | Kill d'instance en charge | Courbe erreurs/disponibilité pendant arrêt d'une instance | `docs/captures/c07-lb-kill-instance.png` | À faire |
| C08 | §10.7 | Cache OFF | k6 ou Grafana avec `CACHE_ENABLED=false` | `docs/captures/c08-cache-off.png` | À faire |
| C09 | §10.7 | Cache ON | k6 ou Grafana avec `CACHE_ENABLED=true`, headers `X-Cache` visibles si possible | `docs/captures/c09-cache-on.png` | À faire |
| C10 | §10.8 | Appel direct catalogue | k6 direct vers `catalog-service` | `docs/captures/c10-direct-catalog.png` | À faire |
| C11 | §10.8 | Appel via gateway | k6 via `api-gateway` sur le même endpoint | `docs/captures/c11-gateway-catalog.png` | À faire |

## 3. Requêtes Prometheus utiles

Latence P95 gateway:

```promql
histogram_quantile(0.95, sum(rate(api_gateway_http_request_duration_seconds_bucket[5m])) by (le))
```

Trafic gateway en requêtes par seconde:

```promql
sum(rate(api_gateway_http_requests_total[5m]))
```

Taux d'erreurs HTTP 4xx/5xx:

```promql
sum(rate(api_gateway_http_requests_total{status=~"4..|5.."}[5m]))
/
sum(rate(api_gateway_http_requests_total[5m]))
```

Requêtes en cours:

```promql
api_gateway_http_requests_in_progress
```

Sonde Blackbox santé:

```promql
probe_success
probe_duration_seconds
```

## 4. Campagnes k6

### 4.1 Catalogue via gateway

```bash
k6 run tests/load/catalog-through-gateway.js
```

Valeurs à relever:

| Date/heure | Endpoint | VUs | Durée | RPS | P90 | P95 | Max | Erreurs | Capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-30 | `/v1/catalog/plans` via gateway | 20 | 1 min | 19,46 req/s | 45,36 ms | 50,26 ms | 54,42 ms | 0,00 % | C03 |

### 4.2 Direct vs gateway

Direct catalogue:

```bash
GATEWAY_URL=http://100.95.65.46:8040 CATALOG_PATH=/plans k6 run tests/load/catalog-through-gateway.js
```

Via gateway:

```bash
GATEWAY_URL=http://127.0.0.1:8000 CATALOG_PATH=/v1/catalog/plans k6 run tests/load/catalog-through-gateway.js
```

| Trajet | URL | P95 | Erreurs | Traçabilité observée | Capture |
| --- | --- | --- | --- | --- | --- |
| Direct | `http://100.95.65.46:8040/plans` | À compléter | À compléter | Logs service amont | C10 |
| Via gateway | `http://127.0.0.1:8000/v1/catalog/plans` | À compléter | À compléter | `/routes`, logs JSON gateway, `X-Trace-Id` | C11 |

## 5. Load balancing N = 1..4

Lancer le gateway avec HAProxy:

```bash
docker compose --profile load-balancing up -d --build
```

Pointer `CATALOG_SERVICE_URL` vers:

```dotenv
CATALOG_SERVICE_URL=http://127.0.0.1:18040
```

Puis relancer:

```bash
docker compose --profile load-balancing up -d --build
```

Activer progressivement `catalog-2`, `catalog-3`, `catalog-4` dans
`infra/load-balancer/haproxy/catalog.cfg`, selon les instances réellement
disponibles.

| N instances | RPS | P95 (ms) | Erreurs | Saturation CPU/RAM | Capture | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 19,39 req/s | 55,9 | 0,00 % | Non mesurée | `docs/captures/k6-load-balancing/c03-lb-n1-reference.png` | 20 VUs, 1 min, 1183 requêtes |
| 2 | 19,51 req/s | 38,8 | 0,00 % | Non mesurée | `docs/captures/k6-load-balancing/c04-lb-n2.png` | 20 VUs, 1 min, 1190 requêtes |
| 3 | 19,42 req/s | 74,84 | 0,00 % | Non mesurée | `docs/captures/k6-load-balancing/c05-lb-n3.png` | 20 VUs, 1 min, 1184 requêtes |
| 4 | 19,53 req/s | 41,72 | 0,00 % | Non mesurée | `docs/captures/k6-load-balancing/c06-lb-n4.png` | 20 VUs, 1 min, 1189 requêtes |
| Kill instance | À compléter | À compléter | À compléter | À compléter | C07 | Arrêter une instance pendant k6 |

## 6. Cache on/off

Cache OFF:

```dotenv
CACHE_ENABLED=false
```

Cache ON:

```dotenv
CACHE_ENABLED=true
CACHE_TTL_SECONDS=60
CACHE_SERVICES=catalog
```

Vérifier les headers:

```bash
curl -i http://127.0.0.1:8000/v1/catalog/plans
curl -i http://127.0.0.1:8000/v1/catalog/plans
```

La première réponse devrait indiquer `X-Cache: MISS`, puis la suivante
`X-Cache: HIT` si Redis est disponible et si la réponse est cachable.

| Endpoint | P95 sans cache | P95 avec cache | Charge service/DB | Gain | Captures |
| --- | --- | --- | --- | --- | --- |
| `/v1/catalog/plans` | À compléter | À compléter | À compléter | À compléter | C08, C09 |

## 7. Notes de capture reçues

Coller ici les observations quand les captures seront reçues.

| Capture | Ce qu'on voit | Valeurs à reporter dans le gabarit | Section |
| --- | --- | --- | --- |
| `docs/captures/grafana/c01-latence-p95-p99-health.png` | Latence P95/P99 des sondes `/health` pour `api-gateway`, `identity-service`, `order-service` et `catalog-service` | Dernières valeurs visibles: P95 gateway 6,01 ms, P99 gateway 7,33 ms; P95 catalog 4,44 ms; P95 identity 5,40 ms; P95 order 5,84 ms | §8.8, §10.5 |
| `docs/captures/grafana/c02-disponibilite-health-up.png` | Disponibilité `/health` des services supervisés | `catalog-service`, `api-gateway`, `order-service` et `identity-service` sont `UP` | §8.8, §10.3 |
| `docs/captures/grafana/c03-saturation-cpu-ram.png` | Saturation CPU/RAM pour `identity-service` et `order-service` | Dernières valeurs visibles: CPU identity 6,20 %, CPU order 6,21 %, RAM identity 90,6 %, RAM order 90,6 % | §8.8, §10.5 |
| `docs/captures/grafana/c04-saturation-reseau.png` | Saturation réseau pour `identity-service` et `order-service` | Dernières valeurs visibles: In identity 4,06 kb/s, In order 3,61 kb/s, Out identity 28,3 kb/s, Out order 27,9 kb/s | §8.8, §10.5 |
| `docs/captures/grafana/c05-erreurs-4xx-5xx-gateway.png` | Erreurs applicatives gateway 4xx/5xx | Pic d'erreurs gateway autour de 0,9 req/s, puis retour à 0 req/s; preuve que le panneau est alimenté par `api_gateway_http_requests_total{status=~"4..|5.."}` | §8.8, §10.5 |
| `docs/captures/grafana/c06-rps-applicatif-gateway.png` | RPS applicatif gateway | Dernière valeur visible: 3,64 req/s; pic visible après génération de trafic | §8.8, §10.5 |
| `docs/captures/prometheus/c02-prometheus-targets-gateway-up.png` | Page Prometheus Targets filtrée sur `100.85.152.43:8000` | `api-gateway (1/1 up)` sur `http://100.85.152.43:8000/metrics`; sonde `blackbox-http-health (1/1 up)` sur `http://100.85.152.43:8000/health`; scrape `/metrics` en 10,437 ms et sonde `/health` en 5,830 ms | §8.8, §10.5 |
| `docs/captures/k6/c03-k6-catalog-gateway.png` | Résumé final k6 pour `/v1/catalog/plans` via gateway | 20 VUs pendant 1 min; 1187 requêtes; 19,46 req/s; checks 100 %; erreurs HTTP 0,00 %; P90 45,36 ms; P95 50,26 ms; max 54,42 ms | §10.5 |
| `docs/captures/k6-load-balancing/c03-lb-n1-reference.png` | Résumé k6 load balancing N=1 | 20 VUs pendant 1 min; 1183 requêtes; 19,39 req/s; checks 100 %; erreurs HTTP 0,00 %; P90 35,22 ms; P95 55,9 ms; max 155,58 ms | §10.6 |
| `docs/captures/k6-load-balancing/c04-lb-n2.png` | Résumé k6 load balancing N=2 | 20 VUs pendant 1 min; 1190 requêtes; 19,51 req/s; checks 100 %; erreurs HTTP 0,00 %; P90 31,15 ms; P95 38,8 ms; max 54,01 ms | §10.6 |
| `docs/captures/k6-load-balancing/c05-lb-n3.png` | Résumé k6 load balancing N=3 | 20 VUs pendant 1 min; 1184 requêtes; 19,42 req/s; checks 100 %; erreurs HTTP 0,00 %; P90 43,38 ms; P95 74,84 ms; max 124,89 ms | §10.6 |
| `docs/captures/k6-load-balancing/c06-lb-n4.png` | Résumé k6 load balancing N=4 | 20 VUs pendant 1 min; 1189 requêtes; 19,53 req/s; checks 100 %; erreurs HTTP 0,00 %; P90 31,97 ms; P95 41,72 ms; max 51,34 ms | §10.6 |
