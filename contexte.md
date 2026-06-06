# CanTelcoX - Vision Architecture Microservices

## Contexte

CanTelcoX est une plateforme BSS (Business Support System) pour un opérateur mobile canadien.

L'application doit permettre :

* Gestion des clients
* Vérification d'identité (KYC)
* Authentification et MFA
* Gestion des lignes mobiles
* Gestion des SIM/eSIM
* Gestion des forfaits et catalogues
* Création de commandes
* Activation de services
* Consultation d'usage
* Facturation
* Paiements
* Détection de fraude
* Audit et conformité

L'architecture doit être orientée microservices avec une évolution possible vers un modèle Event-Driven.

---

# Architecture cible

```text
                    ┌──────────────────┐
                    │    API Gateway   │
                    └────────┬─────────┘
                             │

 ┌─────────────────────────────────────────────────────┐
 │                     Core Domain                     │
 └─────────────────────────────────────────────────────┘

 ┌─────────────────┐
 │ Identity Service│
 └─────────────────┘

 ┌─────────────────┐
 │ Customer Service│
 └─────────────────┘

 ┌─────────────────┐
 │ Catalog Service │
 └─────────────────┘

 ┌─────────────────┐
 │ Order Service   │
 └─────────────────┘

 ┌─────────────────┐
 │ Line Service    │
 └─────────────────┘

 ┌─────────────────────┐
 │ Activation Service  │
 └─────────────────────┘

 ┌─────────────────┐
 │ Usage Service   │
 └─────────────────┘

 ┌─────────────────┐
 │ Billing Service │
 └─────────────────┘

 ┌─────────────────┐
 │ Payment Service │
 └─────────────────┘

 ┌─────────────────┐
 │ Fraud Service   │
 └─────────────────┘

 ┌─────────────────┐
 │ Audit Service   │
 └─────────────────┘
```

---

# Technologies

Backend:

* FastAPI
* SQLAlchemy
* PostgreSQL

Communication:

* REST API
* Async Events (Kafka futur)

Auth:

* JWT
* Refresh Tokens
* MFA

Infrastructure:

* Docker
* Docker Compose
* Future: Kubernetes

Monitoring:

* Prometheus
* Grafana
* OpenTelemetry

---

# API Gateway

Responsabilités :

* Point d'entrée unique
* Validation JWT
* Rate Limiting
* Correlation IDs
* Routing vers services
* Logs centralisés
* CORS

Ne contient aucune logique métier.

---

# Identity Service

Responsabilités :

## Authentification

* Register
* Login
* Logout
* Refresh Token

## MFA

* OTP
* TOTP
* WebAuthn (future)

## Gestion des rôles

Roles :

* USER
* TEAM_MANAGER
* ADMIN

## Tables

User
Role
RefreshToken
MfaConfiguration

## Endpoints

POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh

GET /auth/me

POST /auth/mfa/enable
POST /auth/mfa/verify

---

# Customer Service

Responsabilités :

Gestion du client métier.

À ne pas mélanger avec Identity Service.

## Données

* Nom
* Prénom
* Courriel
* Adresse
* Téléphone
* Consentements
* Statut KYC

## Tables

Customer
Address
Consent
KycRecord

## Endpoints

POST /customers

GET /customers/{id}

PUT /customers/{id}

DELETE /customers/{id}

---

# Catalog Service

Responsabilités :

Gestion des forfaits et offres.

Le catalogue doit être IMMUTABLE et VERSIONNÉ.

## Exemples

Forfait :

* 20 Go
* Appels illimités
* SMS illimités

## Tables

Product
ProductVersion
Offer
Promotion

## Endpoints

GET /catalog/products

POST /catalog/products

GET /catalog/offers

POST /catalog/offers

---

# Order Service

Responsabilités :

Gestion des commandes.

## États

PENDING

VALIDATED

ACTIVATING

COMPLETED

FAILED

CANCELLED

## Tables

Order
OrderItem
OrderStatusHistory

## Endpoints

POST /orders

GET /orders/{id}

GET /orders

DELETE /orders/{id}

## Important

Implémenter :

* Idempotency Key
* Saga Pattern
* Retry Logic

---

# Line Service

Responsabilités :

Gestion des lignes mobiles.

## Concepts

MSISDN
IMSI
ICCID
IMEI

## États

Pending

Active

Suspended

OnHold

PortedOut

Deactivated

## Tables

MobileLine
SimCard
EsimProfile

## Endpoints

POST /lines

GET /lines/{id}

PUT /lines/{id}

POST /lines/{id}/suspend

POST /lines/{id}/activate

---

# Activation Service

Responsabilités :

Provisioning.

Transforme une commande en activation technique.

## Exemple

Order Created

↓

Assign SIM

↓

Assign MSISDN

↓

Activate Line

↓

Notify Success

## Tables

ActivationJob
ActivationStep

## Endpoints

POST /activations

GET /activations/{id}

---

# Usage Service

Responsabilités :

Gestion de la consommation.

## Types

Voice

SMS

Data

## Tables

UsageRecord
CdrRecord

## Endpoints

GET /usage/{customerId}

POST /usage/import

---

# Billing Service

Responsabilités :

Facturation.

## Tables

Invoice
InvoiceItem
BillingCycle

## Endpoints

GET /invoices

GET /invoices/{id}

POST /billing/run

## Flux

CDR

↓

Rating

↓

Billing

↓

Invoice

---

# Payment Service

Responsabilités :

Paiements.

## Tables

Payment
PaymentMethod
Transaction

## Endpoints

POST /payments

GET /payments

GET /payments/{id}

---

# Fraud Service

Responsabilités :

Détection de fraude.

## Cas à gérer

SIM Swap

Port-Out Fraud

Account Takeover

Usage anormal

## Tables

FraudCase
FraudRule
FraudAlert

## Endpoints

GET /fraud/cases

POST /fraud/cases

POST /fraud/check

---

# Audit Service

Responsabilités :

Journalisation append-only.

Aucun événement ne doit être supprimé.

## Événements

UserCreated

LoginSucceeded

CustomerCreated

OrderCreated

LineActivated

InvoiceGenerated

PaymentReceived

FraudDetected

## Tables

AuditLog

## Endpoints

GET /audit

GET /audit/{id}

---

# Event Architecture (Future Kafka)

Events :

CustomerCreated

CustomerUpdated

OrderCreated

OrderValidated

LineActivated

UsageRecorded

InvoiceGenerated

PaymentReceived

FraudDetected

AuditCreated

---

# Priorité de développement

Phase 1 :

* API Gateway
* Identity Service
* Customer Service
* Catalog Service

Phase 2 :

* Order Service
* Line Service
* Activation Service

Phase 3 :

* Usage Service
* Billing Service
* Payment Service

Phase 4 :

* Fraud Service
* Audit Service

Phase 5 :

* Kafka
* Saga
* CQRS
* Event Driven

---

# Règles importantes

* Chaque service possède sa propre base de données.
* Aucun accès direct à la base d'un autre service.
* Communication REST entre services.
* Événements pour les processus asynchrones.
* JWT pour authentification.
* Correlation ID sur toutes les requêtes.
* Logs structurés JSON.
* OpenAPI obligatoire.
* Tests unitaires obligatoires.
* Tests d'intégration obligatoires.
* Docker obligatoire.
* Architecture DDD légère.
* Clean Architecture recommandée.
