# 03. Contexte

## Contexte métier

CanTelcoX est une plateforme télécom découpée en services spécialisés.
Le gateway sert d'entrée commune pour les clients et délègue les traitements aux services responsables de chaque domaine.

## Systèmes externes et voisins

| Système | Rôle | Interface |
| --- | --- | --- |
| Frontend Expo | Client utilisateur principal | HTTP REST vers le gateway |
| Clients externes | Consommateurs API potentiels | HTTP REST vers le gateway |
| `identity-service` | Gestion des utilisateurs et de l'authentification | HTTP REST, port `8020` |
| `order-service` | Gestion des commandes | HTTP REST, port `8030` |
| Services catalogue, clients, facturation et audit | Domaines métier prévus | HTTP REST, URLs à configurer |
| Observability | Supervision des endpoints de santé | Prometheus, Grafana, Blackbox Exporter |

## Contexte technique

Le gateway expose les routes publiques sous `/v1`.
Il construit une URL amont à partir du service demandé, du chemin restant et des paramètres de requête.
Les headers HTTP hop-by-hop sont filtrés pour éviter de transmettre des informations propres à une connexion intermédiaire.

Les services amont sont configurés par variables d'environnement:

| Variable | Usage |
| --- | --- |
| `IDENTITY_SERVICE_URL` | Cible des routes `/v1/users/*` et `/v1/auth/*` |
| `ORDER_SERVICE_URL` | Cible des routes `/v1/orders/*` |
| `CATALOG_SERVICE_URL` | Cible des routes `/v1/catalog/*` |
| `CUSTOMERS_SERVICE_URL` | Cible des routes `/v1/customers/*` |
| `BILLING_SERVICE_URL` | Cible des routes `/v1/billing/*` |
| `AUDIT_SERVICE_URL` | Cible des routes `/v1/audit/*` |

## Frontières

Le gateway est responsable du routage et des erreurs de disponibilité amont.
Il n'est pas responsable de la persistance métier, de l'authentification interne détaillée ni des règles métier des services routés.
