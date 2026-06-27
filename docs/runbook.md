# Runbook

## Correctif de connexion des VM/LXC

Ce guide sert à rétablir rapidement la connectivité entre le gateway, les VM/LXC applicatives et l'environnement d'observabilité.

Le choix principal du projet est d'utiliser Tailscale/Tailnet pour joindre les services. Le réseau `lxdbr0` reste utile pour l'accès local LXC, mais il ne doit pas être la dépendance principale du gateway ni de Prometheus.

## Adresses de référence

| Service | Adresse Tailnet | Port |
| --- | --- | --- |
| `identity-service` | `100.83.57.43` | `8020` |
| `order-service` | `100.108.225.1` | `8030` |
| `catalog-service` | `100.95.65.46` | `8040` |
| `customers-service` | `100.99.167.126` | `8050` |
| `billing-service` | `100.114.185.38` | `8060` |
| `audit-service` | `100.94.161.70` | `8070` |
| `observability` | `100.87.177.66` | `3000`, `9090`, `9115` |

Les variables du gateway doivent pointer vers les adresses Tailnet:

```bash
IDENTITY_SERVICE_URL=http://100.83.57.43:8020
ORDER_SERVICE_URL=http://100.108.225.1:8030
CATALOG_SERVICE_URL=http://100.95.65.46:8040
CUSTOMERS_SERVICE_URL=http://100.99.167.126:8050
BILLING_SERVICE_URL=http://100.114.185.38:8060
AUDIT_SERVICE_URL=http://100.94.161.70:8070
```

## Symptomes typiques

- Le gateway retourne `502 Upstream service unavailable`.
- Grafana affiche les services en `DOWN`.
- `docker build`, `docker pull`, `git pull` ou `curl https://github.com` echouent dans une VM/LXC.
- Les endpoints `/health` fonctionnent avec les IP `10.126.16.x`, mais pas avec les IP `100.x`, ou l'inverse.
- Les services sont `RUNNING` dans `lxc list`, mais Prometheus ne voit pas les bons endpoints.

## Diagnostic rapide

Verifier les IP des conteneurs:

```bash
lxc list
```

Verifier Tailscale sur l'hote:

```bash
tailscale status
tailscale ip -4
```

Tester les services depuis l'hote:

```bash
curl -i http://100.83.57.43:8020/health
curl -i http://100.108.225.1:8030/health
curl -i http://100.95.65.46:8040/health
curl -i http://100.99.167.126:8050/health
curl -i http://100.114.185.38:8060/health
curl -i http://100.94.161.70:8070/health
```

Tester l'acces Internet depuis une VM/LXC:

```bash
lxc exec identity-service -- curl -I -m 8 https://github.com
lxc exec order-service -- curl -I -m 8 https://github.com
lxc exec catalog-service -- curl -I -m 8 https://github.com
```

Verifier que les applications tournent dans les VM/LXC:

```bash
lxc exec identity-service -- docker ps
lxc exec order-service -- docker ps
lxc exec catalog-service -- docker ps
```

Si un service applicatif n'est pas demarre:

```bash
lxc exec identity-service -- sh -lc 'cd /root/LOG430-cantelcox-identity-service && docker compose up -d'
lxc exec order-service -- sh -lc 'cd /root/LOG430-cantelcox-order-service && docker compose up -d'
lxc exec catalog-service -- sh -lc 'cd /root/LOG430-cantelcox-catalog-service && docker compose up -d'
```

## Correctif principal: utiliser Tailscale

Sur chaque VM/LXC, verifier que Tailscale est actif:

```bash
lxc exec identity-service -- tailscale status
lxc exec order-service -- tailscale status
lxc exec catalog-service -- tailscale status
lxc exec observability -- tailscale status
```

Si Tailscale est arrete dans une VM/LXC:

```bash
lxc exec identity-service -- systemctl restart tailscaled
lxc exec order-service -- systemctl restart tailscaled
lxc exec catalog-service -- systemctl restart tailscaled
lxc exec observability -- systemctl restart tailscaled
```

Si une machine n'est plus connectee au Tailnet:

```bash
lxc exec identity-service -- tailscale up
```

Adapter la commande selon la VM/LXC concernee. Si Tailscale demande une authentification, ouvrir l'URL fournie dans le terminal.

## Correctif gateway

Verifier `.env` dans le depot du gateway:

```bash
cat .env
```

Les trois services principaux doivent utiliser les IP Tailnet:

```text
IDENTITY_SERVICE_URL=http://100.83.57.43:8020
ORDER_SERVICE_URL=http://100.108.225.1:8030
CATALOG_SERVICE_URL=http://100.95.65.46:8040
CUSTOMERS_SERVICE_URL=http://100.99.167.126:8050
BILLING_SERVICE_URL=http://100.114.185.38:8060
AUDIT_SERVICE_URL=http://100.94.161.70:8070
```

Redemarrer le gateway:

```bash
sudo docker compose up -d --build
```

Verifier le gateway:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/routes
curl -i http://127.0.0.1:8000/metrics
```

Verifier les metriques applicatives du gateway:

```bash
curl -s http://127.0.0.1:8000/metrics | grep api_gateway_http
```

Les logs du gateway sont emis en JSON et incluent `trace_id`, methode, chemin,
route, statut, duree et client. Le header `X-Trace-Id` est retourne au client et
propage vers le service amont.

## Load balancing catalogue

Le load balancing initial cible `catalog-service` avec HAProxy. Il est lance
par le profil Compose `load-balancing`:

`catalog-service` est le service pilote retenu pour la demonstration N = 1..4
instances. Il n'est pas necessaire de placer immediatement un load balancer
devant tous les services; le meme patron HAProxy peut etre replique ensuite
service par service en remplacant l'URL amont du gateway.

```bash
sudo docker compose --profile load-balancing up -d --build
```

HAProxy ecoute sur `127.0.0.1:18040` et verifie les instances catalogue avec
`GET /health`.

Pour faire passer les appels catalogue par le load balancer, configurer:

```text
CATALOG_SERVICE_URL=http://127.0.0.1:18040
```

Un exemple complet est fourni dans `.env.load-balancing.example`.

Puis redemarrer le gateway:

```bash
sudo docker compose --profile load-balancing up -d --build
```

Verifier le load balancer directement:

```bash
curl -i http://127.0.0.1:18040/health
```

Verifier le trajet complet client -> gateway -> HAProxy -> catalogue:

```bash
curl -i http://127.0.0.1:8000/v1/catalog/plans
```

Pour tester N = 1, 2, 3, 4 instances, demarrer les instances additionnelles du
catalogue sur des ports distincts, activer les lignes `catalog-2` a `catalog-4`
dans `infra/load-balancer/haproxy/catalog.cfg`, puis relancer HAProxy.

Test de charge initial:

```bash
k6 run tests/load/catalog-through-gateway.js
```

Dernier résultat de référence pour N = 1 instance catalogue:

```text
Charge: 20 VUs pendant 1 minute
Requêtes: 1200
RPS: 19,85 req/s
P90: 8,16 ms
P95: 9,91 ms
Max: 56,89 ms
Erreurs HTTP: 0,00 %
Checks réussis: 100 %
```

Pendant le test, tuer une instance catalogue et relever RPS, P95, erreurs et
saturation pour completer la section 10.6 du dossier d'architecture.

## Correctif observability

Dans la VM/LXC `observability`, Prometheus doit sonder les adresses Tailnet, pas les adresses `10.126.16.x`.

Verifier les cibles:

```bash
lxc exec observability -- cat /root/LOG430-cantelcox-observability/prometheus/targets/microservices.yml
```

Les targets attendues sont:

```yaml
- targets:
    - http://100.83.57.43:8020/health
  labels:
    service: identity-service
    environment: lab

- targets:
    - http://100.108.225.1:8030/health
  labels:
    service: order-service
    environment: lab

- targets:
    - http://100.95.65.46:8040/health
  labels:
    service: catalog-service
    environment: lab
```

Redemarrer la pile d'observabilite:

```bash
lxc exec observability -- sh -lc 'cd /root/LOG430-cantelcox-observability && docker compose up -d'
```

Verifier Prometheus:

```bash
lxc exec observability -- curl -s 'http://127.0.0.1:9090/api/v1/query?query=probe_success'
```

Les services doivent avoir `probe_success = 1`.

## Plan B: reparer la sortie Internet via lxdbr0

Ce plan est utile quand les VM/LXC doivent faire `git pull`, `docker pull` ou `docker build`, mais qu'elles n'ont plus d'acces Internet via le bridge LXD.

Sur l'hote, trouver l'interface Internet:

```bash
ip route | grep default
```

Exemple: si l'interface est `wlp2s0`, appliquer:

```bash
sudo sysctl -w net.ipv4.ip_forward=1

sudo iptables -C FORWARD -i lxdbr0 -o wlp2s0 -j ACCEPT 2>/dev/null || \
sudo iptables -I FORWARD 1 -i lxdbr0 -o wlp2s0 -j ACCEPT

sudo iptables -C FORWARD -i wlp2s0 -o lxdbr0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
sudo iptables -I FORWARD 1 -i wlp2s0 -o lxdbr0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

sudo iptables -t nat -C POSTROUTING -s 10.126.16.0/24 -o wlp2s0 -j MASQUERADE 2>/dev/null || \
sudo iptables -t nat -A POSTROUTING -s 10.126.16.0/24 -o wlp2s0 -j MASQUERADE
```

Retester:

```bash
lxc exec identity-service -- curl -I -m 8 https://github.com
```

## Rendre le plan B persistant

Creer le script:

```bash
sudo nano /usr/local/sbin/fix-lxd-nat.sh
```

Contenu:

```bash
#!/usr/bin/env bash
set -euo pipefail

LXD_BRIDGE="lxdbr0"
LXD_SUBNET="10.126.16.0/24"
WAN_IF="$(ip route show default | awk '{print $5; exit}')"

sysctl -w net.ipv4.ip_forward=1

iptables -C FORWARD -i "$LXD_BRIDGE" -o "$WAN_IF" -j ACCEPT 2>/dev/null || \
iptables -I FORWARD 1 -i "$LXD_BRIDGE" -o "$WAN_IF" -j ACCEPT

iptables -C FORWARD -i "$WAN_IF" -o "$LXD_BRIDGE" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
iptables -I FORWARD 1 -i "$WAN_IF" -o "$LXD_BRIDGE" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

iptables -t nat -C POSTROUTING -s "$LXD_SUBNET" -o "$WAN_IF" -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -s "$LXD_SUBNET" -o "$WAN_IF" -j MASQUERADE
```

Activer le script:

```bash
sudo chmod +x /usr/local/sbin/fix-lxd-nat.sh
```

Creer le service:

```bash
sudo nano /etc/systemd/system/fix-lxd-nat.service
```

Contenu:

```ini
[Unit]
Description=Restore LXD NAT forwarding rules
After=network-online.target lxd.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/fix-lxd-nat.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Activer au demarrage:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fix-lxd-nat.service
sudo systemctl start fix-lxd-nat.service
```

Rendre `ip_forward` permanent:

```bash
echo 'net.ipv4.ip_forward=1' | sudo tee /etc/sysctl.d/99-lxd-forward.conf
sudo sysctl --system
```

## Checklist de validation finale

```bash
lxc list
curl -i http://100.83.57.43:8020/health
curl -i http://100.108.225.1:8030/health
curl -i http://100.95.65.46:8040/health
curl -i http://100.99.167.126:8050/health
curl -i http://100.114.185.38:8060/health
curl -i http://100.94.161.70:8070/health
curl -i http://127.0.0.1:8000/routes
lxc exec observability -- curl -s 'http://127.0.0.1:9090/api/v1/query?query=probe_success'
```

Etat attendu:

- les VM/LXC sont `RUNNING`;
- les endpoints `/health` retournent `200 OK`;
- `/routes` expose les IP Tailnet `100.x`;
- `probe_success` vaut `1` dans Prometheus;
- Grafana affiche les services `UP`.
