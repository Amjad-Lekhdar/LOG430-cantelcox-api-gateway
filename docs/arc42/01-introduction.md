# 01. Introduction

## Objectif du système

CanTelcoX API Gateway est la facade REST exposée au frontend Expo et aux clients externes.
Son rôle est de fournir une URL d'entrée unique et de router les appels vers les services internes de la plateforme CanTelcoX.

Le gateway ne porte pas la logique métier principale. Il agit comme point d'accès, applique les règles communes de proxy HTTP et masque la localisation réelle des microservices.

## Fonctionnalités principales

- Exposer un endpoint de santé `GET /health`.
- Exposer la table de routage effective avec `GET /routes`.
- Router les appels `/v1/users/*` et `/v1/auth/*` vers le service d'identité.
- Router les appels `/v1/orders/*` vers le service de commandes.
- Préparer les routes `/v1/catalog/*`, `/v1/customers/*`, `/v1/billing/*` et `/v1/audit/*` vers des services dédiés configurables.
- Retourner une erreur explicite lorsqu'un service amont n'est pas encore configuré.

## Parties prenantes

| Partie prenante | Besoin principal |
| --- | --- |
| Utilisateurs du frontend Expo | Accéder aux fonctionnalités CanTelcoX via une API stable. |
| Équipe backend | Déployer et faire évoluer les services indépendamment. |
| Équipe exploitation | Observer l'état des services et diagnostiquer les erreurs de routage. |
| Enseignants / évaluateurs LOG430 | Vérifier les choix d'architecture et leur justification documentaire. |

## Portée

Cette documentation couvre l'architecture du gateway et son intégration avec les services CanTelcoX existants ou prévus.
Les détails internes des services `identity-service`, `order-service`, `catalog`, `customers`, `billing` et `audit` sont hors portée, sauf lorsqu'ils influencent les contrats de routage.
