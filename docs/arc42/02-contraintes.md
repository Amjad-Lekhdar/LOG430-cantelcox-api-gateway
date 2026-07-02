# 02. Contraintes d'architecture

## 2.1 Contraintes techniques

- Le gateway est implémenté en Python avec FastAPI.
- Le conteneur Docker du gateway est construit depuis le `Dockerfile` à la racine du dépôt.
- Les services amont peuvent tourner sur des VM/LXC distinctes et ne sont pas nécessairement présents dans ce dépôt.
- Les URLs des services amont sont injectées par variables d'environnement.
- Le déploiement Docker Compose actuel lance le gateway avec `network_mode: host`.
- Les services observés doivent exposer un endpoint `/health`.
- Les services métier exposent des APIs HTTP REST/JSON consommées par le gateway.
- Chaque service métier doit pouvoir être configuré par une URL amont dédiée et déployé indépendamment.
- Les services qui possèdent de la persistance utilisent PostgreSQL comme base de données relationnelle.
- Le frontend est une application Expo développée en TypeScript.
- Le frontend doit consommer l'API via le gateway comme point d'entrée unique, sans appeler directement les services internes.
- Le gateway doit autoriser les origines de développement nécessaires au frontend local grâce à sa configuration CORS.
- Le coeur free5GC est joint comme système technique de laboratoire; il n'est pas exposé comme route publique du gateway.

## 2.2 Contraintes organisationnelles

- Le projet documente les décisions structurantes avec des ADR.
- L'architecture cible suit une approche microservices.
- Les services métier doivent être déployables indépendamment lorsque leur maturité le permet.
- La documentation est maintenue en français sous `docs/arc42`, `docs/adr` et `docs/diagrams`.

## 2.3 Contraintes réglementaires et juridiques

CanTelcoX représente le BSS d'un opérateur mobile canadien. Le système cible couvre le cycle de vie des lignes mobiles: souscription, activation, consultation d'usage, prise de commande de forfaits et d'options, paiement de facture et conformité réglementaire.

Le secteur impose notamment:

- CRTC et Loi sur les télécommunications pour les obligations propres aux opérateurs télécoms.
- Loi 25 et LPRPDE pour la protection des renseignements personnels.
- Transparence tarifaire, étiquetage clair des offres et portabilité obligatoire des numéros.
- Contrôles de sécurité liés aux activations, notamment contre la fraude SIM swap et l'usurpation d'identité.
- Exigence élevée de disponibilité, car les communications mobiles sont critiques.

Dans le MVP, le gateway ne porte pas directement les règles réglementaires détaillées. Ces règles sont principalement implémentées dans les services métier. Le gateway fournit toutefois une base fiable: routage vers les bons services, observabilité minimale, propagation de `X-Trace-Id` et possibilité d'ajouter plus tard l'authentification, l'autorisation et l'audit.

## 2.4 Contraintes de réseau

Les VM/LXC du laboratoire sont reliées avec Tailscale.
Le Tailnet fournit des adresses stables utilisées par le gateway pour joindre les services internes sans les exposer directement sur Internet.
La justification complète de ce choix est documentée dans [ADR 0006](../adr/0006-utilisation-tailscale.md).

| Service | Adresse Tailnet connue |
| --- | --- |
| `identity-service` | `100.83.57.43:8020` |
| `order-service` | `100.108.225.1:8030` |
| `line-service` | `100.86.218.1:8080` |
| `catalog-service` | `100.95.65.46:8040` |
| `customers-service` | `100.99.167.126:8050` |
| `billing-service` | `100.114.185.38:8060` |
| `audit-service` | `100.94.161.70:8070` |
| free5GC core | Adresse Tailnet/LXC à renseigner |
| `observability` | `100.87.177.66` |

Le gateway doit pouvoir joindre les machines Tailnet depuis son environnement d'exécution. Les paramètres d'accès free5GC restent dans la configuration de `line-service`.
