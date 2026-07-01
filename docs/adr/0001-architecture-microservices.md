# ADR 0001 - Architecture microservices alignée sur les bounded contexts

## Statut

Accepté

## Contexte

CanTelcoX doit fournir un BSS télécom couvrant l'inscription, l'identité, les commandes, l'activation de lignes, le catalogue, la facturation, les paiements, l'audit et la conformité réglementaire.

Le cahier de charge demande une architecture basée par services, inspirée de DDD, avec des frontières tirées des bounded contexts, une API RESTful, de l'observabilité, des tests de charge et une démonstration de scalabilité. Les domaines n'ont pas tous les mêmes contraintes: le catalogue est surtout lu, les commandes exigent l'idempotence, la facturation demande des écritures exactly-once et l'audit doit rester append-only.

Une architecture unique et monolithique serait plus simple à démarrer, mais elle rendrait plus difficile la démonstration des exigences du cours: découpage métier, déploiement distribué, disponibilité partielle, scaling ciblé et tolérance aux pannes.

## Forces de décision

- Aligner les services avec les bounded contexts du cahier de charge.
- Isoler les règles métier et la persistance par domaine.
- Permettre le scaling ciblé des domaines à forte charge, notamment le catalogue.
- Préserver une architecture compréhensible et démontrable dans un contexte de laboratoire.
- Réduire les dépendances cycliques entre domaines.
- Accepter une complexité opérationnelle raisonnable pour satisfaire les exigences microservices.

## Options considérées

| Option | Exemple | Avantages | Inconvénients |
| --- | --- | --- | --- |
| Monolithe modulaire | Une seule application `cantelcox-bss` contenant authentification, catalogue, commandes, facturation et audit | Déploiement simple, transactions locales, moins d'infrastructure | Démontre moins bien la distribution, scaling global seulement, risque de couplage entre domaines |
| Microservices par bounded context | Des services séparés comme `identity-service`, `catalog-service`, `order-service`, `billing-service` et `audit-service` | Autonomie métier, scaling par domaine, déploiement et observabilité par service | Plus de configuration, gestion des erreurs réseau, cohérence distribuée à documenter |
| Services purement techniques | Un service `user-api`, un service `billing-api`, un service `data-api` ou des services découpés par couche CRUD | Découpage rapide par couches techniques | Couplage fort entre domaines, frontières métier peu lisibles, faible cohérence DDD |

## Décision

Adopter une architecture microservices découpée par bounded contexts métier.

Les services retenus sont:

| Service | Bounded context | Responsabilité principale |
| --- | --- | --- |
| `identity-service` | Clients & Identité | Utilisateurs, authentification, MFA et identité numérique |
| `customers-service` | Clients & Identité | Client métier, coordonnées, consentements et données personnelles |
| `catalog-service` | Catalogue & Offres | Forfaits, options, prix, règles d'éligibilité et versionnement du catalogue |
| `order-service` | Commandes & Activations | Commandes, demandes d'activation et orchestration métier associée |
| `billing-service` | Usage/Rating/Facturation | Usage, factures, paiements et écritures de facturation |
| `audit-service` | Conformité & Audit | Journal append-only, traces réglementaires et signaux anti-fraude |
| `api-gateway` | Façade technique | Point d'entrée HTTP unique, routage et diagnostics |

Chaque service métier vise une architecture hexagonale: adapters d'entrée HTTP, couche application, domaine, ports de sortie et adapters de persistance ou d'intégration. Le gateway reste volontairement technique: il ne contient ni règle métier ni base de données métier.

La communication inter-services retenue pour la phase 1 est REST synchrone. Les URLs amont sont configurées par variables d'environnement et les machines sont reliées par le réseau privé Tailscale documenté dans l'ADR 0006.

## Conséquences

- Les frontières de service sont traçables aux domaines du cahier de charge.
- Les équipes peuvent raisonner sur les invariants par service plutôt que sur un modèle global unique.
- Un service peut servir de pilote pour démontrer le load balancing N = 1..4 instances.
- Les erreurs réseau, les timeouts, les services indisponibles et les réponses partielles deviennent des cas normaux à gérer.
- Le système n'utilise pas de transaction globale entre microservices. Chaque service sécurise ses propres données localement, tandis que les opérations critiques sont protégées par l'idempotence, les contraintes de base de données, les traces d'audit et les mécanismes anti-doublon du service de facturation.
- Les tests et la documentation doivent préciser l'état réel des services: implémenté, configuré, simulé ou prévu.

## Conformité

Cette décision répond aux sections du cahier de charge portant sur:

- la conception d'une architecture basée par services;
- l'application de DDD et des bounded contexts;
- l'utilisation de REST synchrone en phase 1;
- l'observabilité et la mesure des services;
- la démonstration de scalabilité, disponibilité et tolérance aux pannes.

La conformité est vérifiée par:

- les vues Arc42 et 4+1 décrivant les services;
- les diagrammes de building blocks niveau 1 et niveau 2;
- la table de routage du gateway;
- les tests du gateway;
- les ADR complémentaires sur gateway, persistance, idempotence, observabilité et réseau privé.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-23.
- Cette décision est complétée par l'ADR 0002 sur l'API Gateway et l'ADR 0003 sur la persistance par service.
