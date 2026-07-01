# 08. Concepts transversaux

Cette section correspond à la vue développement de Kruchten 4+1.

## 8.1 Configuration

Les adresses des services amont sont configurées par variables d'environnement.
Le fichier `.env` sert de configuration locale/laboratoire et est chargé par Docker Compose.

Variables principales:

- `IDENTITY_SERVICE_URL`
- `ORDER_SERVICE_URL`
- `CATALOG_SERVICE_URL`
- `CUSTOMERS_SERVICE_URL`
- `BILLING_SERVICE_URL`
- `AUDIT_SERVICE_URL`

Les paramètres free5GC ne sont pas des variables du gateway public; ils appartiennent à `line-service`, qui implémente le port d'activation réseau.

## 8.2 Routage HTTP

Le gateway route les requêtes en fonction du premier segment après `/v1`.
Le chemin complet restant et les paramètres de requête sont conservés.
Les appels vers free5GC ne passent pas par une route publique du gateway: ils sont déclenchés par `line-service` via un adapter de sortie.

## 8.3 Gestion des headers

Les headers hop-by-hop sont supprimés lors du proxying.
Cela évite de propager des headers propres à une connexion HTTP intermédiaire, par exemple `connection`, `transfer-encoding` ou `host`.
Le header `X-Trace-Id` est généré ou propagé pour relier les logs gateway et services.

## 8.4 Gestion des erreurs

| Cas | Réponse |
| --- | --- |
| Route inconnue | `404` |
| Route connue mais URL absente | `503` |
| Service amont inaccessible | `502` |
| Erreur HTTP retournée par le service amont | Statut et contenu de l'amont |

Les erreurs métier, dont les erreurs d'activation free5GC, doivent être normalisées par le service amont responsable, notamment `line-service` pour `/v1/lines/*`, avant d'être relayées.

## 8.5 Observabilité

Le gateway expose `/health`, `/routes` et `/metrics`.
La supervision initiale repose sur des sondes HTTP via Blackbox Exporter et des métriques Prometheus.
Les métriques applicatives des autres services restent à instrumenter ou raccorder progressivement.

## 8.6 Sécurité

Le gateway configure CORS pour des origines locales utilisées en développement.
Les mécanismes avancés comme l'authentification centralisée, la validation des jetons, le rate limiting et les politiques de sécurité d'API restent à préciser.

Les opérations sensibles du domaine télécom, comme le SIM swap, le port-out, le changement de mot de passe ou le changement d'adresse, doivent être traitées comme des actions à risque. Le gateway reste compatible avec ces contrôles en préservant les headers applicatifs et en permettant la propagation de traces.

## 8.7 Idempotence, exactly-once et audit

Le gateway préserve les headers applicatifs et peut transporter `Idempotency-Key`.
La déduplication effective doit être implémentée côté `order-service` pour les commandes, côté `line-service` pour les activations et côté `billing-service` pour les écritures de facturation.
Les opérations sensibles doivent être journalisées par `audit-service` dans un registre append-only.

## 8.8 Intégration free5GC

free5GC est traité comme système technique externe au BSS.
`line-service` expose un port d'activation qui masque les détails réseau 5G: provisionnement SIM/SUPI, DNN, slice et vérification d'état.
Cette séparation évite de coupler le gateway et les contrats REST publics aux composants AMF, SMF, UDM, UDR, NRF ou UPF.

## 8.9 Persistance et migrations

Non applicable au gateway MVP: il ne possède pas de base de données.
La persistance appartient aux services métier, idéalement avec une base PostgreSQL ou un schéma isolé par service.

## 8.10 Build, déploiement, CI/CD

Le build est défini par le `Dockerfile`.
Le lancement local/laboratoire est défini par `docker-compose.yml`.
Les URLs amont sont chargées depuis `.env`.

## 8.11 Tests

Le dépôt contient des tests automatisés du gateway dans `tests/test_gateway.py`.
Ils couvrent notamment `/health`, `/routes`, les routes inconnues, les services connus non configurés, les erreurs amont et le proxy vers un service mock.

## 8.12 Conventions de code et structure des dépôts

| Élément | Convention actuelle |
| --- | --- |
| Application | `app/main.py` |
| Configuration | `app/core/config.py` |
| Documentation arc42 | `docs/arc42/` et `docs/arc42.md` |
| ADR | `docs/adr/NNNN-titre.md` |
