# 06. Vue d'exécution

Cette section correspond à la vue processus de Kruchten 4+1.

## 6.1 Scénario: parcours E2E nominal

![Scénario E2E CanTelcoX](../diagrams/plantuml/runtime-e2e-6-1.svg)

Le parcours nominal couvre l'inscription, la validation MFA, la consultation du catalogue, la création de commande avec `Idempotency-Key`, la demande d'activation à `line-service`, l'activation réseau via free5GC et la consultation d'usage.
Le gateway relaie les appels; les règles métier restent dans les services amont.

## 6.2 Scénario: vérification de santé

```text
Client -> API Gateway: GET /health
API Gateway -> Client: 200 {"status": "ok", "service": "api-gateway"}
```

Ce scénario ne dépend pas des services amont.
Il permet à Docker, Prometheus Blackbox Exporter ou un opérateur de vérifier que le gateway répond.

## 6.3 Scénario: consultation de la table de routage

```text
Client -> API Gateway: GET /routes
API Gateway -> Client: 200 avec les routes et URLs configurées
```

La réponse reflète les variables d'environnement chargées au démarrage.
Elle permet de détecter rapidement une URL manquante ou incorrecte.

## 6.4 Scénario: proxy vers un service configuré

Exemple avec `/v1/orders/{id}`:

```text
Client -> API Gateway: GET /v1/orders/123?include=items
API Gateway -> order-service: GET {ORDER_SERVICE_URL}/v1/orders/123?include=items
order-service -> API Gateway: réponse HTTP
API Gateway -> Client: même statut et contenu applicatif
```

Le gateway conserve la méthode HTTP, le chemin, les paramètres de requête et le corps lorsque présent.

## 6.5 Scénario: activation avec free5GC

```text
Client -> API Gateway: POST /v1/orders avec Idempotency-Key
API Gateway -> order-service: POST /v1/orders avec Idempotency-Key
order-service -> catalog-service: vérifier offre et prix
order-service -> billing-service: déclarer commande facturable
order-service -> line-service: demander activation de ligne
line-service -> free5GC core: provisionner SUPI/SIM, DNN et slice
free5GC core -> line-service: activation acceptée ou erreur réseau
line-service -> audit-service: tracer activation
line-service -> order-service: ligne active ou erreur normalisée
order-service -> API Gateway: 201 commande confirmée ou erreur normalisée
API Gateway -> Client: même statut et contenu applicatif
```

Le gateway ne connaît pas les détails AMF/SMF/UDM/UDR/UPF. L'intégration free5GC est encapsulée par le port d'activation de `line-service`.

## 6.6 Scénario: service prévu mais URL absente

Exemple avec `/v1/billing/invoices` lorsque `BILLING_SERVICE_URL` est vide:

```text
Client -> API Gateway: GET /v1/billing/invoices
API Gateway -> Client: 503 {"detail": "No upstream service configured for /v1/billing"}
```

Ce comportement permet de déployer le gateway avant la disponibilité de tous les services métier.

## 6.7 Scénario: service amont indisponible

Lorsque l'URL est configurée mais que le service ne répond pas, le gateway retourne une erreur `502` avec l'URL amont et la raison réseau fournie par Python.

## 6.8 Aspects de concurrence

| Aspect | Décision actuelle |
| --- | --- |
| Modèle d'exécution | FastAPI servi par Uvicorn. |
| Appels amont | Proxy HTTP synchrone via `urllib.request.urlopen`. |
| Timeout | Timeout réseau de 15 secondes sur les appels amont. |
| Verrouillage | Aucun état métier partagé dans le gateway. |
| Backpressure | Non implémenté dans le MVP. |
