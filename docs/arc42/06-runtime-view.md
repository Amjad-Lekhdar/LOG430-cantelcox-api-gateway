# 06. Runtime view

## Scénario: vérification de santé

```text
Client -> API Gateway: GET /health
API Gateway -> Client: 200 {"status": "ok", "service": "api-gateway"}
```

Ce scénario ne dépend pas des services amont.
Il permet à Docker, Prometheus Blackbox Exporter ou un opérateur de vérifier que le gateway répond.

## Scénario: consultation de la table de routage

```text
Client -> API Gateway: GET /routes
API Gateway -> Client: 200 avec les routes et URLs configurées
```

La réponse reflète les variables d'environnement chargées au démarrage.
Elle permet de détecter rapidement une URL manquante ou incorrecte.

## Scénario: proxy vers un service configuré

Exemple avec `/v1/orders/{id}`:

```text
Client -> API Gateway: GET /v1/orders/123?include=items
API Gateway -> order-service: GET {ORDER_SERVICE_URL}/v1/orders/123?include=items
order-service -> API Gateway: réponse HTTP
API Gateway -> Client: même statut et contenu applicatif
```

Le gateway conserve la méthode HTTP, le chemin, les paramètres de requête et le corps lorsque présent.

## Scénario: service prévu mais URL absente

Exemple avec `/v1/billing/invoices` lorsque `BILLING_SERVICE_URL` est vide:

```text
Client -> API Gateway: GET /v1/billing/invoices
API Gateway -> Client: 503 {"detail": "No upstream service configured for /v1/billing"}
```

Ce comportement permet de déployer le gateway avant la disponibilité de tous les services métier.

## Scénario: service amont indisponible

Lorsque l'URL est configurée mais que le service ne répond pas, le gateway retourne une erreur `502` avec l'URL amont et la raison réseau fournie par Python.
