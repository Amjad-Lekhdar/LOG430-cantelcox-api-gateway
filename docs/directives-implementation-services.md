# Directives d'implémentation des services CanTelcoX

## 1. Objectif

Ce document guide l'implémentation des services métier nécessaires pour compléter le système CanTelcoX conformément à l'architecture décrite dans `docs/`.

Les services principalement à réaliser sont :

- `audit-service`, port `8070`;
- `customers-service`, port hôte `8050` redirigé vers le port conteneur `8000`;
- `billing-service`, port `8060`.
- `line-service`, port `8080`.

Les services existants suivants doivent également être complétés :

- `identity-service`, port `8020`;
- `order-service`, port `8030`;
- `catalog-service`, port `8040`.

Le gateway reste un composant technique de routage. Aucune règle métier et aucune persistance métier ne doivent être ajoutées dans l'API Gateway.

## 2. Décision fonctionnelle à appliquer

Le compte d'identité et le profil client métier doivent rester séparés.

| Concept | Service propriétaire | Contenu |
| --- | --- | --- |
| Identité numérique | `identity-service` | Identifiants, mot de passe, authentification, MFA et jetons |
| Client métier | `customers-service` | Segment, coordonnées, adresse, consentements et statut commercial |

Les routes doivent donc respecter la convention suivante :

```text
/v1/users/*      -> identity-service
/v1/auth/*       -> identity-service
/v1/customers/*  -> customers-service
/v1/lines/*      -> line-service
```

Le scénario d'inscription complet doit créer l'identité numérique, puis le profil client associé au moyen de `identityId`.

## 3. Conventions communes

### 3.1 Technologies recommandées

- Python 3.12;
- FastAPI et Pydantic;
- PostgreSQL, avec une base distincte par service;
- SQLAlchemy pour la persistance;
- Alembic pour les migrations;
- pytest pour les tests;
- Docker et Docker Compose;
- Prometheus pour les métriques.

### 3.2 Architecture interne

Chaque service doit suivre une architecture hexagonale :

```text
app/
├── api/
│   └── routes/
├── application/
│   └── use_cases/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   └── exceptions.py
├── ports/
│   ├── repositories.py
│   └── services.py
├── adapters/
│   ├── persistence/
│   └── http/
├── core/
│   ├── config.py
│   ├── logging.py
│   └── security.py
└── main.py

tests/
├── unit/
└── integration/

alembic/
Dockerfile
docker-compose.yml
requirements.txt
```

Les dépendances doivent pointer vers le domaine :

```text
API REST -> cas d'utilisation -> domaine <- ports <- adaptateurs
```

### 3.3 Endpoints techniques obligatoires

Chaque service doit exposer :

```http
GET /health
GET /metrics
GET /docs
```

Réponse minimale de santé :

```json
{
  "status": "ok",
  "service": "billing-service"
}
```

### 3.4 Format commun des erreurs

Tous les services doivent retourner des erreurs JSON homogènes :

```json
{
  "code": "CUSTOMER_NOT_FOUND",
  "message": "Customer not found",
  "details": {},
  "traceId": "c94db638-6c93-4fb7-9ea8-66e3265bd22c",
  "timestamp": "2026-06-25T12:00:00Z"
}
```

Les erreurs attendues sont notamment :

| Situation | Statut |
| --- | --- |
| Requête invalide | `400` ou `422` |
| Authentification absente ou invalide | `401` |
| Accès interdit | `403` |
| Ressource inexistante | `404` |
| Conflit métier ou doublon | `409` |
| Dépendance métier indisponible | `502` ou `503` |

### 3.5 Headers communs

Les services doivent accepter et propager :

- `Authorization`;
- `X-Correlation-ID` ou `X-Trace-ID`;
- `Idempotency-Key` pour les opérations sensibles.

Si aucun identifiant de corrélation n'est fourni, le premier service appelé doit en générer un.

### 3.6 Persistance

Chaque service possède exclusivement sa base PostgreSQL. Il est interdit :

- d'utiliser une base partagée;
- de lire directement les tables d'un autre service;
- de créer des clés étrangères entre les bases de services.

Les références externes, par exemple `customerId` ou `identityId`, sont conservées comme UUID sans contrainte interbase.

## 4. `audit-service`

### 4.1 Priorité

Implémenter ce service en premier, car les autres services doivent y consigner leurs opérations sensibles.

### 4.2 Modèle minimal

```text
AuditEvent
- id: UUID
- actorId: UUID
- actorType: CUSTOMER | AGENT | SERVICE
- action: string
- resourceType: string
- resourceId: UUID
- occurredAt: datetime
- traceId: UUID
- metadata: JSON
- previousHash: string, optionnel
- eventHash: string, optionnel

RiskSignal
- id: UUID
- auditEventId: UUID
- type: string
- severity: LOW | MEDIUM | HIGH | CRITICAL
- detectedAt: datetime
```

### 4.3 Endpoints minimaux

```http
POST /v1/audit/events
GET  /v1/audit/events
GET  /v1/audit/events/{id}
GET  /v1/audit/alerts
```

La recherche doit accepter des filtres tels que :

```text
actorId
resourceId
action
traceId
dateFrom
dateTo
```

### 4.4 Invariants

- Le journal est en insertion seule.
- Aucun endpoint `PUT`, `PATCH` ou `DELETE` ne doit être exposé.
- L'acteur, l'action, la date et le `traceId` sont obligatoires.
- Le rôle PostgreSQL de l'application ne doit pas avoir les permissions `UPDATE` et `DELETE`.
- Les recherches d'audit doivent être protégées par un rôle administratif.
- Des index doivent couvrir `actor_id`, `resource_id`, `occurred_at` et `trace_id`.

Une chaîne de hash entre les événements est recommandée pour faciliter la détection d'altérations.

### 4.5 Règles anti-fraude initiales

Le moteur de règles peut commencer avec :

- plusieurs échecs MFA dans une courte période;
- plusieurs demandes d'activation pour une même ligne;
- changement récent des coordonnées suivi d'une activation;
- paiements refusés ou répétés;
- activité roaming anormale;
- événements sensibles provenant d'un acteur inconnu.

Une règle déclenchée doit créer un `RiskSignal` et rendre l'alerte consultable.

## 5. `customers-service`

### 5.1 Responsabilité

Ce service gère le client métier, ses coordonnées et ses consentements. Il ne gère ni les mots de passe ni les jetons d'authentification.

### 5.2 Modèle minimal

```text
Customer
- id: UUID
- identityId: UUID, unique
- segment: INDIVIDUAL | SME
- status: ACTIVE | SUSPENDED | CLOSED
- createdAt: datetime
- updatedAt: datetime

ContactInfo
- email
- phone

Address
- line1
- city
- province
- postalCode
- country

Consent
- id: UUID
- customerId: UUID
- type: string
- granted: boolean
- recordedAt: datetime
```

### 5.3 Endpoints minimaux

```http
POST  /v1/customers
GET   /v1/customers/{id}
GET   /v1/customers/by-identity/{identityId}
PATCH /v1/customers/{id}
POST  /v1/customers/{id}/consents
GET   /v1/customers/{id}/consents
```

### 5.4 Création d'un client

Le cas d'utilisation doit :

1. valider la requête;
2. vérifier l'existence de `identityId` auprès d'`identity-service`;
3. vérifier qu'aucun client ne possède déjà cet `identityId`;
4. créer le client et ses consentements dans une transaction locale;
5. consigner `CUSTOMER_CREATED` auprès d'`audit-service`;
6. retourner `201 Created`.

### 5.5 Invariants

- Un `identityId` ne peut être associé qu'à un seul client.
- Un client ne peut consulter ou modifier que son propre profil, sauf rôle administratif.
- Toute modification de coordonnées ou de consentement doit être auditée.
- La fermeture d'un client ne doit pas supprimer physiquement son historique.
- Les données personnelles ne doivent jamais apparaître dans les logs techniques.

## 6. `billing-service`

### 6.1 Responsabilité

Ce service couvre :

- la consultation de l'usage;
- la gestion des factures;
- le paiement;
- la clôture du cycle mensuel;
- la prévention des doubles écritures financières.

### 6.2 Modèle minimal

```text
BillingAccount
- id: UUID
- customerId: UUID
- status: ACTIVE | SUSPENDED | CLOSED
- balance: decimal

UsageRecord
- id: UUID
- externalUsageId: string, unique
- customerId: UUID
- lineId: UUID
- quantity: decimal
- unit: DATA_MB | VOICE_MINUTE | SMS
- recordedAt: datetime
- ratedAmount: decimal

Invoice
- id: UUID
- customerId: UUID
- periodStart: date
- periodEnd: date
- status: DRAFT | OPEN | PAID | OVERDUE
- total: decimal

Payment
- id: UUID
- invoiceId: UUID
- providerTransactionId: string, unique
- idempotencyKey: string, unique
- amount: decimal
- status: PENDING | ACCEPTED | REFUSED
- paidAt: datetime
```

Tous les montants doivent utiliser un type décimal. Les nombres flottants sont interdits pour les montants financiers.

### 6.3 Endpoints minimaux

```http
GET  /v1/billing/usage
POST /v1/billing/usage
GET  /v1/billing/invoices
GET  /v1/billing/invoices/{id}
POST /v1/billing/invoices/{id}/payments
POST /v1/billing/payment-webhooks
POST /v1/billing/cycles/{period}/close
```

Il ne faut pas exposer `POST /v1/billing/invoices` pour créer une facture à
l'unité. Le flux nominal est :

1. enregistrer un usage facturable avec `POST /v1/billing/usage`;
2. fermer le cycle avec `POST /v1/billing/cycles/{period}/close`;
3. consulter les factures avec `GET /v1/billing/invoices`.

### 6.4 Consultation

Les routes de lecture doivent vérifier que le client authentifié possède les comptes, lignes et factures demandés.

Une consultation ne doit jamais modifier l'état d'une facture.

### 6.5 Paiement idempotent

`POST /v1/billing/invoices/{id}/payments` doit exiger `Idempotency-Key`.

Le traitement doit :

1. démarrer une transaction PostgreSQL;
2. rechercher un paiement existant avec la même clé;
3. retourner le paiement existant en cas de rejeu;
4. vérifier la facture, son propriétaire et son solde;
5. créer le paiement avec une contrainte unique;
6. mettre à jour le solde et le statut de la facture;
7. valider la transaction;
8. auditer `PAYMENT_APPLIED`.

La garantie attendue est réalisée avec une transaction locale, des contraintes uniques et la déduplication. Un rejeu ne doit jamais appliquer deux fois le montant.

### 6.6 Clôture mensuelle

La base doit empêcher la création de deux factures pour la même période :

```text
UNIQUE(customer_id, period_start, period_end)
```

Le batch doit pouvoir être rejoué sans produire de facture ou d'écriture en double.

Si le service publie des événements après une transaction, utiliser une table outbox enregistrée dans la même transaction.

## 7. Compléments dans les services existants

### 7.1 `identity-service`

Endpoints attendus :

```http
POST /v1/users
GET  /v1/users/{id}
POST /v1/auth/login
POST /v1/auth/mfa/challenge
POST /v1/auth/mfa/verify
GET  /v1/users/{id}/verification
```

Directives :

- hacher les mots de passe avec Argon2id ou bcrypt;
- ne jamais retourner le hash;
- donner une durée de vie courte aux OTP;
- limiter les tentatives MFA;
- invalider un challenge après utilisation;
- auditer les connexions, refus et validations MFA;
- inclure l'identité, les rôles et l'état MFA dans le jeton.

### 7.2 `catalog-service`

Endpoints attendus :

```http
GET  /v1/catalog/plans
GET  /v1/catalog/plans/{id}
POST /v1/catalog/eligibility/check
```

Directives :

- seules les offres actives peuvent être vendues;
- chaque offre doit posséder une version;
- le prix et les règles doivent être cohérents avec cette version;
- les commandes doivent conserver l'identifiant, la version et le prix validé;
- le cache doit avoir un TTL et être invalidé lors d'une modification du catalogue.

### 7.3 `order-service`

Endpoints attendus :

```http
POST /v1/orders
GET  /v1/orders/{id}
GET  /v1/orders
POST /v1/orders/{id}/activation-requests
```

Pour créer une commande :

1. exiger `Idempotency-Key`;
2. valider le client auprès du service approprié;
3. vérifier l'offre, sa version, son admissibilité et son prix;
4. enregistrer la commande et la clé dans la même transaction;
5. retourner la commande existante en cas de rejeu;
6. auditer la création.

La portée d'une clé doit au minimum inclure :

```text
customerId + route + Idempotency-Key
```

Pour demander une activation :

- vérifier que la commande est admissible;
- exiger une preuve MFA récente;
- appeler `line-service` via HTTP REST, jamais free5GC directement;
- transmettre `orderId`, `customerId`, `offerId`, `offerVersion`, `msisdn` si déjà attribué, et la preuve MFA ou son résultat;
- rendre la demande d'activation idempotente;
- contrôler explicitement les transitions de statut;
- auditer le succès et l'échec.

Ce que `order-service` ne doit plus faire :

- posséder les tables `MobileLine`, `SimProfile` ou `NetworkSession`;
- attribuer ou réserver directement un MSISDN;
- stocker les secrets, paramètres ou credentials free5GC;
- appeler AMF/SMF/UDM/UDR/UPF ou des scripts free5GC;
- décider seul qu'une ligne est active sans confirmation de `line-service`;
- mélanger l'état de commande (`PENDING`, `CONFIRMED`, `ACTIVATION_REQUESTED`) avec l'état réseau de la ligne.

### 7.4 `line-service`

Responsabilité :

`line-service` est propriétaire du bounded context Lignes & Services. Il gère les lignes mobiles, MSISDN, profils SIM/SUPI, demandes d'activation, état réseau et intégration free5GC.

Endpoints attendus :

```http
POST /v1/lines/activations
GET  /v1/lines/{id}
GET  /v1/lines/by-customer/{customerId}
GET  /v1/lines/{id}/network-status
PATCH /v1/lines/{id}/suspend
PATCH /v1/lines/{id}/resume
```

Modèle minimal :

```text
MobileLine
- id: UUID
- customerId: UUID
- orderId: UUID
- msisdn: MSISDN, unique
- status: PENDING_ACTIVATION | ACTIVE | SUSPENDED | FAILED | CLOSED
- offerId: UUID
- offerVersion: integer
- activatedAt: datetime?

SimProfile
- id: UUID
- lineId: UUID
- iccid: string, unique
- supi: string, unique
- dnn: string
- slice: string

ActivationRequest
- id: UUID
- orderId: UUID
- customerId: UUID
- idempotencyKey: string
- status: RECEIVED | PROVISIONING | ACTIVATED | FAILED
- failureReason: string?
- createdAt: datetime
- completedAt: datetime?

NetworkSession
- id: UUID
- lineId: UUID
- pduSessionId: string?
- accessType: string
- state: REGISTERED | CONNECTED | DISCONNECTED | UNKNOWN
- observedAt: datetime
```

Invariants :

- Une ligne appartient à un seul `customerId`.
- Un `MSISDN`, un `ICCID` et un `SUPI` sont uniques.
- Une activation est idempotente par `customerId + orderId + Idempotency-Key`.
- Une ligne ne peut passer à `ACTIVE` qu'après confirmation free5GC ou simulation explicitement documentée.
- Un échec free5GC ne doit pas créer une ligne active.
- Toute activation, suspension, reprise ou échec doit être auditée.

Flux d'activation :

1. recevoir `POST /v1/lines/activations` depuis `order-service` ou le gateway;
2. exiger `Idempotency-Key`;
3. vérifier la preuve MFA récente ou le résultat de validation fourni;
4. créer ou retrouver `ActivationRequest` dans une transaction locale;
5. réserver ou créer `MobileLine` et `SimProfile`;
6. appeler l'adapter free5GC avec SUPI, DNN, slice et paramètres requis;
7. marquer la ligne `ACTIVE` seulement après confirmation;
8. auditer `LINE_ACTIVATED` ou `LINE_ACTIVATION_FAILED`;
9. retourner l'état de ligne à `order-service`.

Ports et adapters :

- `LineRepository` vers PostgreSQL;
- `Free5gcPort` vers l'adapter free5GC;
- `AuditPort` vers `audit-service`;
- `IdentityPort` ou validation JWT pour vérifier client/MFA;
- adapter optionnel de portabilité MSISDN.

Variables suggérées :

```text
LINE_SERVICE_URL=http://100.x.x.x:8080
FREE5GC_API_URL=
FREE5GC_NRF_URL=
FREE5GC_DNN=
FREE5GC_SLICE=
FREE5GC_DEFAULT_PLMN=
```

## 8. Sécurité

### 8.1 Authentification et autorisation

- Le frontend s'authentifie auprès d'`identity-service`.
- Les services valident le JWT ou délèguent cette validation à un composant commun clairement documenté.
- L'identifiant de ressource demandé doit être comparé à l'identité du jeton.
- Les opérations administratives doivent exiger un rôle explicite.
- Une preuve MFA récente est requise pour l'activation et les opérations sensibles.

### 8.2 Secrets et données sensibles

- Tous les secrets passent par des variables d'environnement.
- Le fichier `.env` ne doit pas être commité.
- Un `.env.example` sans secret doit documenter les variables.
- Les mots de passe, OTP, jetons, données bancaires et informations personnelles ne doivent pas être journalisés.
- Les requêtes SQL doivent être paramétrées par l'ORM.

## 9. Observabilité

Chaque requête doit produire un log JSON contenant au minimum :

```text
timestamp
level
service
method
path
status
durationMs
traceId
```

Chaque service doit exposer des métriques permettant de suivre :

- le nombre de requêtes;
- la latence;
- les erreurs `4xx` et `5xx`;
- les connexions ou opérations en cours;
- les événements métier critiques, par exemple paiements refusés.

Les noms des métriques doivent rester stables et inclure le nom du service.

Objectifs du projet :

- latence P95 inférieure ou égale à `500 ms`;
- débit cible d'au moins `600 opérations/s`;
- disponibilité d'au moins `95 %`.

## 10. Tests obligatoires

### 10.1 Tests unitaires

Tester les règles métier sans base réelle :

- invariants des agrégats;
- transitions de statut;
- calcul des montants;
- admissibilité;
- règles anti-fraude;
- comportement idempotent.

### 10.2 Tests d'intégration

Tester chaque repository avec PostgreSQL :

- migrations depuis une base vide;
- contraintes uniques;
- commit et rollback;
- impossibilité de modifier ou supprimer l'audit;
- rejeu d'une commande, d'un paiement et d'un cycle de facturation.

### 10.3 Tests de contrat

Tester :

- les routes et méthodes HTTP;
- les DTO d'entrée et de sortie;
- les codes de statut;
- le format commun des erreurs;
- la propagation de `Authorization`, `X-Correlation-ID` et `Idempotency-Key`.

### 10.4 Scénario E2E minimal

Le scénario à démontrer via le gateway est :

1. création de l'identité;
2. création du profil client;
3. authentification et MFA;
4. consultation du catalogue;
5. création d'une commande avec `Idempotency-Key`;
6. rejeu identique sans nouvelle commande;
7. demande d'activation à `line-service`;
8. consultation de l'usage et de la facture;
9. paiement idempotent;
10. consultation de la trace d'audit.

## 11. Docker et configuration

Chaque service doit fournir :

- un `Dockerfile`;
- un `docker-compose.yml`;
- un conteneur PostgreSQL;
- un healthcheck;
- des migrations exécutables;
- des données seed de démonstration;
- un `.env.example`.

Variables communes suggérées :

```text
SERVICE_NAME=
SERVICE_PORT=
DATABASE_URL=
JWT_PUBLIC_KEY=
AUDIT_SERVICE_URL=
LOG_LEVEL=
```

Le gateway doit utiliser :

```text
IDENTITY_SERVICE_URL=http://100.83.57.43:8020
ORDER_SERVICE_URL=http://100.108.225.1:8030
CATALOG_SERVICE_URL=http://100.95.65.46:8040
CUSTOMERS_SERVICE_URL=http://100.99.167.126:8050
BILLING_SERVICE_URL=http://100.114.185.38:8060
AUDIT_SERVICE_URL=http://100.94.161.70:8070
LINE_SERVICE_URL=http://100.x.x.x:8080
```

## 12. Ordre de réalisation

1. Figer les responsabilités et les contrats OpenAPI.
2. Créer un squelette commun pour les services.
3. Implémenter `audit-service`.
4. Implémenter `customers-service`.
5. Implémenter `line-service` avec activation idempotente et adapter free5GC.
6. Implémenter la consultation d'usage et de factures.
7. Ajouter le paiement et la clôture mensuelle.
8. Compléter l'authentification et le MFA.
9. Compléter le catalogue versionné.
10. Compléter la commande idempotente dans `order-service`.
11. Brancher tous les services au gateway.
12. Ajouter les tests E2E.
13. Ajouter les tests de charge et les preuves Grafana.

## 13. Définition de fini

Un service est considéré comme terminé lorsque :

- son contrat OpenAPI est documenté;
- sa base démarre vide et les migrations passent;
- les données seed permettent une démonstration;
- `/health`, `/metrics` et `/docs` fonctionnent;
- les erreurs suivent le format commun;
- les tests unitaires et d'intégration passent;
- les actions sensibles sont auditées;
- les secrets sont hors du dépôt;
- le conteneur possède un healthcheck;
- le service fonctionne directement et à travers le gateway;
- les opérations sensibles résistent aux doubles soumissions;
- le README du service explique son démarrage et ses endpoints;
- les limites connues sont consignées dans la documentation d'architecture.

## 14. Références internes

- `docs/arc42/05-building-blocks.md`
- `docs/arc42/06-runtime-view.md`
- `docs/arc42/08-concepts-transversaux.md`
- `docs/arc42/10-exigences-qualite.md`
- `docs/Gabarit_LOG430_Phase1_Architecture_v3_1.md`
- `docs/backlog.md`
- `docs/runbook.md`
- `docs/adr/0003-database-per-service.md`
- `docs/adr/0004-idempotence-audit-billing.md`
