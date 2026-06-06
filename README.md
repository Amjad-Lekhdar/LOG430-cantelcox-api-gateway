# CanTelcoX API Gateway

Facade REST pour le frontend Expo et les clients externes.

Le gateway expose une seule URL publique et route les appels vers les services internes.

## Run local

```bash
cd services/api-gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Routing MVP

```text
GET    /health
GET    /routes

/v1/users/*      -> identity-service
/v1/auth/*       -> identity-service
/v1/orders/*     -> order-service

/v1/catalog/*    -> bss-core
/v1/customers/*  -> bss-core
/v1/billing/*    -> bss-core
/v1/audit/*      -> bss-core
```

## Health checks

Local services:

```bash
# api-gateway
curl -i http://127.0.0.1:8000/health

# identity-service
curl -i http://127.0.0.1:8020/health

# order-service
curl -i http://127.0.0.1:8030/health

# bss-core
curl -i http://127.0.0.1:8010/health
```

Tailnet/LXC services:

```bash
# identity-service
curl -i http://100.83.57.43:8020/health

# order-service
curl -i http://100.108.225.1:8030/health
```

Gateway route table:

```bash
# api-gateway
curl -i http://127.0.0.1:8000/routes
```

## Environment

By default, the gateway expects the services to run on the same machine:

```text
IDENTITY_SERVICE_URL=http://127.0.0.1:8020
ORDER_SERVICE_URL=http://127.0.0.1:8030
BSS_CORE_URL=http://127.0.0.1:8010
```

When services run in LXC/VM machines on the Tailnet, start the gateway with the
machine IPs:

```bash
IDENTITY_SERVICE_URL=http://100.83.57.43:8020 \
ORDER_SERVICE_URL=http://100.108.225.1:8030 \
BSS_CORE_URL=http://127.0.0.1:8010 \
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Current Tailnet machines:

```text
identity-service  100.83.57.43
observability     100.87.177.66
order-service     100.108.225.1
```

Docker service names can still be used when the gateway and upstream services run
inside the same Docker network:

```text
IDENTITY_SERVICE_URL=http://identity-service:8020
ORDER_SERVICE_URL=http://order-service:8030
BSS_CORE_URL=http://bss-core:8010
```

## Connectivity test

From the repository root:

```bash
GATEWAY_URL=http://127.0.0.1:8000 \
IDENTITY_URL=http://127.0.0.1:8020 \
python3 scripts/check_gateway_connectivity.py
```

If the identity service runs in a Tailnet LXC/VM, use its IP:

```bash
GATEWAY_URL=http://127.0.0.1:8000 \
IDENTITY_URL=http://100.83.57.43:8020 \
python3 scripts/check_gateway_connectivity.py
```

If the test returns a `502` with upstream `http://identity-service:8020`, the
gateway was started with the Docker service name. Restart it with
`IDENTITY_SERVICE_URL=http://100.83.57.43:8020`.

If the auth endpoints are not deployed yet:

```bash
python3 scripts/check_gateway_connectivity.py --skip-auth-flow
```
