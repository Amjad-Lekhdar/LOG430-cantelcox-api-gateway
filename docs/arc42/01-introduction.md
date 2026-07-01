# 01. Introduction et objectifs

## 1.1 Aperçu des exigences

CanTelcoX API Gateway est la facade REST exposée au frontend Expo et aux clients externes.
Son rôle est de fournir une URL d'entrée unique et de router les appels vers les services internes de la plateforme CanTelcoX.

Le gateway ne porte pas la logique métier principale. Il agit comme point d'accès, applique les règles communes de proxy HTTP et masque la localisation réelle des microservices.
Le dossier de domaine positionne CanTelcoX comme une plateforme BSS couvrant le cycle de vie client d'une ligne mobile, depuis l'inscription et l'activation jusqu'à la consultation d'usage, la facturation, le paiement et la détection de fraude.

Fonctionnalités principales:

- Exposer un endpoint de santé `GET /health`.
- Exposer la table de routage effective avec `GET /routes`.
- Exposer des métriques Prometheus avec `GET /metrics`.
- Router les appels `/v1/users/*` et `/v1/auth/*` vers `identity-service`.
- Router les appels `/v1/orders/*` vers `order-service`.
- Router les appels `/v1/catalog/*` vers `catalog-service`.
- Préparer les routes `/v1/customers/*`, `/v1/billing/*` et `/v1/audit/*` vers des services dédiés configurables.
- Retourner une erreur explicite lorsqu'un service amont n'est pas configuré ou indisponible.

## 1.2 Objectifs de qualité

| # | Objectif de qualité | Cible attendue | Impact sur le gateway |
| --- | --- | --- | --- |
| 1 | Performance | Latence P95 opération -> ACK <= 500 ms en phase microservices | Le gateway doit rester un proxy léger et limiter la surcharge ajoutée aux appels HTTP. |
| 2 | Débit | >= 600 opérations/s en phase microservices | Le routage doit rester simple et les services doivent pouvoir évoluer indépendamment derrière le gateway. |
| 3 | Disponibilité | 95 % en phase microservices | Le gateway doit retourner des erreurs explicites (`502`, `503`) et permettre de détecter rapidement les services indisponibles. |
| 4 | Observabilité | Logs structurés et métriques dès la phase 1 | Le gateway expose `/health`, `/routes` et `/metrics`; les logs JSON incluent un `trace_id` propagé vers les services amont. |
| 5 | Conformité et auditabilité | Idempotence des commandes et activations, écritures de facturation fiables, journaux append-only | Le gateway doit transmettre les informations nécessaires aux services métier et rester compatible avec les futures politiques d'audit. |
| 6 | Intégration réseau 5G | Activation démontrable avec free5GC en laboratoire | Le gateway reste hors des détails AMF/SMF/UDM/UDR/UPF; l'intégration free5GC est portée par l'adapter d'activation de `line-service`. |

## 1.3 Parties prenantes

| Rôle | Nom / groupe | Attentes |
| --- | --- | --- |
| Utilisateur final | Utilisateurs du frontend Expo | Accéder aux fonctionnalités CanTelcoX via une API stable. |
| Équipe backend | Développeurs CanTelcoX | Déployer et faire évoluer les services indépendamment. |
| Équipe exploitation | Ops / laboratoire | Observer l'état des services et diagnostiquer les erreurs de routage. |
| Équipe réseau 5G | Responsables free5GC / UERANSIM | Raccorder le provisioning de ligne au coeur 5G sans exposer les fonctions réseau au client public. |
| Évaluateurs | Enseignants LOG430 | Vérifier les choix d'architecture et leur justification documentaire. |

## 1.4 Portée

Cette documentation couvre l'architecture du gateway, son intégration avec les services CanTelcoX existants ou prévus, et le raccordement de l'activation de ligne au coeur free5GC.

Les détails internes des services `identity-service`, `order-service`, `catalog-service`, `customers-service`, `billing-service` et `audit-service` restent hors portée, sauf lorsqu'ils influencent les contrats de routage, les responsabilités d'architecture ou les scénarios de démonstration.
