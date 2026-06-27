# 05. Building blocks

## Vue niveau 1 - Whitebox du système global

Cette vue décompose le système en blocs principaux et précise, pour chacun, sa responsabilité et son interface principale.

![Figure 5.1 - Diagramme de composants niveau 1 du système CanTelcoX](../diagrams/plantuml/building-blocks-5-1.svg)

La vue de niveau 1 décompose le système en une façade d'entrée unique, `CanTelcoX API Gateway`, et plusieurs services métier amont alignés sur les bounded contexts du domaine télécom. Le gateway est le seul bloc implémenté dans ce dépôt : il expose les routes publiques, résout le service cible à partir du segment `/v1/{service}`, puis relaie la requête HTTP vers l'URL amont configurée.

Les dépendances sont dirigées du client vers le gateway, puis du gateway vers les services responsables. Le gateway agit comme adaptateur d'entrée et point de routage; les règles métier, la persistance et les contrats internes restent dans les services amont.

| Bloc | Responsabilité | Interface principale |
| --- | --- | --- |
| `CanTelcoX API Gateway` | Routage `/v1/*`, diagnostic `/health` et `/routes`, filtrage des headers hop-by-hop, gestion des erreurs de disponibilité amont (`404`, `503`, `502`) | HTTP REST public, port `8000` |
| `identity-service` | Utilisateurs, authentification, MFA et identité numérique | HTTP REST interne via `/v1/users/*` et `/v1/auth/*`, port `8020` |
| `order-service` | Commandes, demandes d'activation et idempotence métier | HTTP REST interne via `/v1/orders/*`, port `8030` |
| `catalog-service` | Catalogue des offres, forfaits, options et règles d'éligibilité | HTTP REST interne via `/v1/catalog/*`, port `8040` |
| `customers-service` | Client métier distinct de l'identité numérique | HTTP REST interne via `/v1/customers/*`; service prévu, URL à configurer |
| `billing-service` | Usage, factures, paiements et écritures de facturation | HTTP REST interne via `/v1/billing/*`; service prévu, URL à configurer |
| `audit-service` | Journalisation append-only, traces des opérations sensibles et support anti-fraude | HTTP REST interne via `/v1/audit/*`; service prévu, URL à configurer |

## Vue niveau 2 - Whitebox des services

Le niveau 2 détaille les blocs critiques de la vue 5.1. Les services métier suivent une cible hexagonale : adapters d'entrée, couche application, domaine pur, adapters de sortie. Le gateway reste une façade technique de routage.

### API Gateway

![Whitebox API Gateway](../diagrams/plantuml/level2/api-gateway-5-2.svg)

| Élément | Description |
| --- | --- |
| Responsabilité | Exposer `/health`, `/routes` et `/v1/*`, résoudre la cible amont et relayer les requêtes. |
| Ports primaires | HTTP public FastAPI. |
| Ports secondaires | URLs `*_SERVICE_URL` vers les services métier. |
| Invariant | Aucune règle métier ni persistance métier dans le gateway. |

### `identity-service`

![Whitebox identity-service](../diagrams/plantuml/level2/identity-service-5-2.svg)

| Élément | Description |
| --- | --- |
| Domaine | `User`, `IdentityProfile`, `Credential`, `MfaChallenge`. |
| Ports primaires | `UserController`, `AuthController`. |
| Ports secondaires | `UserRepository`, fournisseur OTP/MFA, `AuditClient`. |
| Invariants | Identifiants uniques, MFA validé avant les opérations sensibles, authentification traçable. |

### `order-service`

![Whitebox order-service](../diagrams/plantuml/level2/order-service-5-2.svg)

| Élément | Description |
| --- | --- |
| Domaine | `Order`, `OrderItem`, `OrderStatus`, `IdempotencyKey`. |
| Ports primaires | `OrderController`, `ActivationController`. |
| Ports secondaires | `OrderRepository`, `CatalogClient`, `IdentityClient`, `BillingClient`, `AuditClient`, adapter HLR/HSS simulé. |
| Invariants | Une clé d'idempotence ne crée qu'une commande logique, statut contrôlé, offre vérifiée avant activation. |

### `catalog-service`

![Whitebox catalog-service](../diagrams/plantuml/level2/catalog-service-5-2.svg)

| Élément | Description |
| --- | --- |
| Domaine | `Offer`, `Plan`, `Price`, `EligibilityRule`, `CatalogVersion`. |
| Ports primaires | `CatalogController`. |
| Ports secondaires | `OfferRepository`, cache catalogue, `AuditClient`. |
| Invariants | Catalogue versionné, offre active pour être vendue, prix cohérents avec la version. |

### `customers-service`

![Whitebox customers-service](../diagrams/plantuml/level2/customers-service-5-2.svg)

| Élément | Description |
| --- | --- |
| Domaine | `Customer`, `ContactInfo`, `Address`, `Consent`. |
| Ports primaires | `CustomerController`. |
| Ports secondaires | `CustomerRepository`, `IdentityClient`, `AuditClient`. |
| Invariants | Client métier distinct de l'identité numérique, changements sensibles auditables. |

### `billing-service`

![Whitebox billing-service](../diagrams/plantuml/level2/billing-service-5-2.svg)

| Élément | Description |
| --- | --- |
| Domaine | `BillingAccount`, `UsageRecord`, `Invoice`, `Payment`. |
| Ports primaires | `BillingController`, `PaymentWebhook`. |
| Ports secondaires | `BillingRepository`, `UsageProvider`, passerelle de paiement, `AuditClient`. |
| Invariants | Paiement appliqué une seule fois, facture rattachée à une période, écriture exactly-once. |

### `audit-service`

![Whitebox audit-service](../diagrams/plantuml/level2/audit-service-5-2.svg)

| Élément | Description |
| --- | --- |
| Domaine | `AuditEvent`, `Actor`, `RiskSignal`, `AppendOnlyLog`. |
| Ports primaires | `AuditController`, consommateur d'événements de domaine. |
| Ports secondaires | Repository append-only, moteur de règles fraude, publication d'alertes. |
| Invariants | Journal en insertion seule, horodatage et acteur obligatoires, événements sensibles conservés. |

## Services amont

| Service | Routes gateway | État de configuration |
| --- | --- | --- |
| `identity-service` | `/v1/users/*`, `/v1/auth/*` | Configuré via `IDENTITY_SERVICE_URL` |
| `order-service` | `/v1/orders/*` | Configuré via `ORDER_SERVICE_URL` |
| `catalog-service` | `/v1/catalog/*` | Configuré via `CATALOG_SERVICE_URL` |
| `customers-service` | `/v1/customers/*` | Prévu, URL à fournir |
| `billing-service` | `/v1/billing/*` | Prévu, URL à fournir |
| `audit-service` | `/v1/audit/*` | Prévu, URL à fournir |

## API Gateway - responsabilités internes

- Déterminer le service cible à partir du segment `/v1/{service}`.
- Préserver le chemin et les paramètres de requête.
- Transmettre la méthode HTTP et le corps de la requête.
- Filtrer les headers hop-by-hop.
- Retourner la réponse amont telle que reçue, après filtrage des headers.
- Retourner `404` pour une famille de route inconnue.
- Retourner `503` pour une famille de route connue mais non configurée.
