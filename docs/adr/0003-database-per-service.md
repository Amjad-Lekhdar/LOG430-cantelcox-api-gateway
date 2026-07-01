# ADR 0003 - Persistance database-per-service

## Statut

Accepté

## Contexte

Les domaines CanTelcoX manipulent des données avec des contraintes différentes: profils clients, identifiants, commandes, catalogue, usage, factures, paiements et événements d'audit.

Le cahier de charge demande une persistance robuste, des transactions, des contraintes d'intégrité, des migrations reproductibles, des données de démonstration, l'idempotence des commandes et activations, l'exactly-once des écritures de facturation et un journal d'audit append-only.

Dans une architecture microservices, partager une seule base relationnelle entre services simplifierait certaines jointures, mais créerait un couplage fort entre modèles, migrations et cycles de livraison. À l'inverse, une base par service renforce l'autonomie des bounded contexts, au prix d'une cohérence distribuée à gérer explicitement.

## Forces de décision

- Protéger l'autonomie des modèles de données par domaine.
- Éviter qu'un service dépende directement du schéma interne d'un autre.
- Garder les transactions locales à l'intérieur d'un service.
- Permettre des stratégies de données adaptées: catalogue versionné, billing transactionnel, audit append-only.
- Préparer le scaling et le déploiement indépendant des services.
- Rester compatible avec PostgreSQL et les contraintes du laboratoire.

## Options considérées

| Option | Exemple | Avantages | Inconvénients |
| --- | --- | --- | --- |
| Base unique partagée | Une seule base `cantelcox` avec les tables `users`, `customers`, `orders`, `invoices` et `audit_events` accessibles par tous les services | Requêtes croisées simples, administration initiale plus facile | Couplage fort, migrations risquées, frontières DDD affaiblies |
| Schémas séparés dans une même instance PostgreSQL | Une instance PostgreSQL commune avec les schémas `identity`, `customers`, `orders`, `billing` et `audit` | Isolation logique, coût infra réduit | Risque de dépendances SQL entre schémas, autonomie partielle |
| Base ou schéma dédié par service | `identity-service` possède sa base, `order-service` possède sa base et `billing-service` possède sa base, sans accès direct aux tables des autres | Autonomie forte, transactions locales, évolution indépendante | Pas de jointure directe entre domaines, besoin d'API ou événements pour synchroniser |

## Décision

Adopter le patron database-per-service.

Chaque service métier possède sa persistance logique et ne lit pas directement les tables d'un autre service. En contexte de laboratoire, cette persistance peut être déployée comme une base PostgreSQL dédiée ou comme un schéma isolé par service, à condition que les accès applicatifs restent séparés.

Les responsabilités de persistance sont:

| Service | Données principales | Contraintes attendues |
| --- | --- | --- |
| `identity-service` | utilisateurs, credentials, MFA | identifiants uniques, secrets protégés, traces d'authentification |
| `customers-service` | clients, coordonnées, consentements | unicité client, gestion des données personnelles, audit des changements sensibles |
| `catalog-service` | offres, forfaits, prix, versions | catalogue versionné, offres actives, cohérence prix/version |
| `order-service` | commandes, activations, clés d'idempotence | unicité des clés d'idempotence, statuts contrôlés, aucune double création logique |
| `billing-service` | usage, factures, paiements, écritures comptables | exactly-once sur écritures de facturation, unicité des références externes |
| `audit-service` | événements d'audit, signaux de risque | insertion seule, horodatage, acteur et corrélation obligatoires |

Les échanges inter-domaines passent par APIs REST en phase 1. Les duplications nécessaires sont traitées comme des copies applicatives contrôlées, pas comme des dépendances directes au schéma source.

## Conséquences

- Les migrations d'un service peuvent évoluer sans casser directement les autres services.
- Les transactions restent locales et plus simples à raisonner.
- Les lectures transversales doivent passer par composition API, vues matérialisées futures ou événements futurs.
- La cohérence forte globale n'est pas garantie par une transaction distribuée; les cas critiques utilisent des clés d'idempotence, contraintes uniques, statuts et audit.
- Les sauvegardes, migrations et seeds doivent être documentés par service.
- Les tests d'intégration doivent couvrir les invariants propres à chaque base ou schéma.

## Conformité

Cette décision répond aux exigences du cahier de charge sur:

- la couche de persistance robuste par service;
- les transactions et contraintes d'intégrité;
- l'idempotence des commandes et activations;
- l'exactly-once de la facturation;
- le journal d'audit append-only pour la conformité CRTC/Loi 25.

La conformité est vérifiée par:

- l'absence de base de données métier dans le gateway;
- les repositories et migrations des services;
- les contraintes uniques sur clés métier et clés d'idempotence;
- les tests d'intégration DB des services;
- l'ADR 0004 pour les garanties idempotence, billing et audit.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-23.
- Cette décision complète l'ADR 0001 et prépare l'ADR 0004 sur les garanties d'intégrité.
