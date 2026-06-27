# 02. Contraintes

## Contraintes techniques

- Le gateway est implémenté en Python avec FastAPI.
- Le conteneur Docker du gateway est construit depuis le `Dockerfile` à la racine du dépôt.
- Les services amont peuvent tourner sur des VM/LXC distinctes et ne sont pas nécessairement présents dans ce dépôt.
- Les URLs des services amont sont injectées par variables d'environnement.
- Le déploiement Docker Compose actuel lance uniquement le gateway localement et s'appuie sur `network_mode: host`.
- Les services observés doivent exposer un endpoint `/health`.

## Contraintes de réseau

- Les services existants sont accessibles via Tailnet:
  - `identity-service`: `100.83.57.43:8020`
  - `order-service`: `100.108.225.1:8030`
  - `catalog-service`: `100.95.65.46:8040`
  - `customers-service`: `100.99.167.126:8050`
  - `billing-service`: `100.114.185.38:8060`
  - `audit-service`: `100.94.161.70:8070`
  - `observability`: `100.87.177.66`
- Le gateway doit pouvoir joindre les machines Tailnet depuis son environnement d'exécution.
- Les URLs des services non encore créés restent configurables dans `.env`.

## Contraintes organisationnelles

- Le projet documente les décisions structurantes avec des ADR.
- L'architecture cible suit une approche microservices.
- Les services métier doivent être déployables indépendamment lorsque leur maturité le permet.

## Contraintes connues

- Les métriques applicatives Prometheus sont exposées par le gateway sur `/metrics`; les autres services doivent encore être instrumentés ou raccordés progressivement.
- Certaines routes sont préparées mais dépendent encore de la création des services amont correspondants.
