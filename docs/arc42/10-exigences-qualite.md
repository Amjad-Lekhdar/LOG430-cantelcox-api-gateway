# 10. Exigences qualite

## Arbre de qualité

| Qualité | Objectif | Mécanisme actuel |
| --- | --- | --- |
| Maintenabilité | Modifier les URLs et routes sans refactor majeur | Configuration par variables d'environnement et table de routage explicite |
| Déployabilité | Lancer le gateway indépendamment des services métier | Dockerfile et Docker Compose dédiés au gateway |
| Disponibilité | Identifier rapidement un service indisponible | `/health`, erreurs `502`/`503`, supervision Blackbox |
| Évolutivité fonctionnelle | Ajouter de nouveaux domaines métier | Variables et routes dédiées par domaine |
| Observabilité | Voir l'état des services | Endpoints `/health`, environnement observabilité séparé |
| Simplicité | Garder le MVP compréhensible | Proxy HTTP direct sans découverte de service complexe |

## Scénarios de qualité

| Scénario | Stimulus | Réponse attendue |
| --- | --- | --- |
| Déplacement d'un service | L'adresse du service d'identité change | Mettre à jour `IDENTITY_SERVICE_URL` sans changer le code |
| Service non encore créé | Un client appelle `/v1/billing/*` | Le gateway retourne `503` avec un message de configuration manquante |
| Service amont arrêté | `order-service` est inaccessible | Le gateway retourne `502` avec la cible amont |
| Vérification exploitation | Un opérateur appelle `/health` | Le gateway retourne `200` si l'application est active |
| Diagnostic routage | Un opérateur appelle `/routes` | Le gateway liste les URLs actuellement chargées |

## Priorités

1. Déployabilité en environnement laboratoire.
2. Maintenabilité de la configuration réseau.
3. Observabilité minimale fiable.
4. Ajout progressif de sécurité et de métriques applicatives.
