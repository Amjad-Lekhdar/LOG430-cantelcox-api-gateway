# 08. Concepts transversaux

## Configuration

Les adresses des services amont sont configurées par variables d'environnement.
Le fichier `.env` sert de configuration locale/laboratoire et est chargé par Docker Compose.

Variables principales:

- `IDENTITY_SERVICE_URL`
- `ORDER_SERVICE_URL`
- `CATALOG_SERVICE_URL`
- `CUSTOMERS_SERVICE_URL`
- `BILLING_SERVICE_URL`
- `AUDIT_SERVICE_URL`

## Routage HTTP

Le gateway route les requêtes en fonction du premier segment après `/v1`.
Le chemin complet restant et les paramètres de requête sont conservés.

## Gestion des headers

Les headers hop-by-hop sont supprimés lors du proxying.
Cela évite de propager des headers propres à une connexion HTTP intermédiaire, par exemple `connection`, `transfer-encoding` ou `host`.

## Gestion des erreurs

| Cas | Réponse |
| --- | --- |
| Route inconnue | `404` |
| Route connue mais URL absente | `503` |
| Service amont inaccessible | `502` |
| Erreur HTTP retournée par le service amont | Statut et contenu de l'amont |

## Observabilité

Le gateway expose `/health`.
La supervision initiale repose sur des sondes HTTP via Blackbox Exporter.
Les métriques applicatives détaillées restent à ajouter.

## Sécurité

Le gateway configure CORS pour des origines locales utilisées en développement.
Les mécanismes avancés comme l'authentification centralisée, la validation des jetons, le rate limiting et les politiques de sécurité d'API restent à préciser.
