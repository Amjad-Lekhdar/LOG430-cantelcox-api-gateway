# Cahier de charge du projet CanTelcoX

## 1. Contexte

Dans le cadre de ce projet d'architecture logicielle avancée, vous assumez le rôle d'architecte logiciel mandaté par CanTelcoX, un opérateur mobile canadien fictif. CanTelcoX souhaite concevoir et déployer un système de support commercial (BSS) moderne destiné aux abonnés particuliers et PME, permettant la gestion complète du cycle de vie des lignes mobiles :

- souscription;
- activation;
- consultation d'usage;
- prise de commande de forfaits et d'options;
- paiement de facture;
- conformité réglementaire.

Le secteur des télécommunications canadien est caractérisé par un cadre réglementaire strict, notamment :

- CRTC;
- Loi sur les télécommunications;
- Loi 25;
- LPRPDE.

Il impose aussi une exigence élevée de disponibilité du service et des contrôles stricts contre la fraude :

- SIM swap;
- usurpation d'identité;
- fraude roaming.

La plateforme doit s'intégrer à des infrastructures simulées :

- réseau mobile HLR/HSS;
- hub de portabilité;
- passerelle de paiement.

Elle doit satisfaire les objectifs de disponibilité, sécurité, performance et auditabilité fixés au cahier de charge.

## 2. Mandat

Votre mandat consiste à poser les fondations architecturales du système et à les déployer sous la forme d'une architecture distribuée.

Pour cette phase, vous devez :

- Concevoir une architecture basée par services claire, cohérente et évolutive, en vous inspirant des bonnes pratiques de conception étudiées en cours : DDD, hexagonal, ports/adapters.
- Définir et implémenter les cas d'utilisation prioritaires Must-Have du cahier de charge CanTelcoX, parmi UC-01 à UC-08, couvrant les domaines Clients & Identité, Lignes & Services, Commandes & Activations, Catalogue & Offres, Usage/Rating/Facturation, Conformité & Audit.
- Exposer le système via une API RESTful sécurisée, documentée avec OpenAPI/Swagger et orchestrée par une API Gateway.
- Utiliser les standards TMF Open APIs à titre de référence industrielle, notamment TMF620 Product Catalog, TMF622 Product Ordering, TMF629 Customer Management et TMF666 Account Management.
- Documenter l'architecture selon une approche 4+1 views et compléter au moins trois Architectural Decision Records (ADR) justifiant vos choix structurants, incluant les décisions de conformité : idempotence, exactly-once, journal append-only.
- Mettre en oeuvre une stratégie d'observabilité : logs structurés, métriques Prometheus, dashboards Grafana et 4 Golden Signals.
- Démontrer le respect des paliers NFR cibles : latence P95 <= 500 ms, débit >= 600 opérations/s, disponibilité 95 %.
- Optimiser la performance par load balancing et caching, et démontrer la tolérance aux pannes.
- Démontrer la faisabilité technique par une implémentation conteneurisée multi-service et un pipeline CI/CD complet.

En tant qu'architecte logiciel, vous êtes responsable de :

- Analyser le cahier de charge CanTelcoX et traduire les besoins métiers en exigences architecturales : frontières de service, NFR, contraintes réglementaires CRTC / Loi 25.
- Prendre des décisions structurantes : style architectural, découpage en services, persistance/transactions, idempotence des commandes/activations, exactly-once des écritures de facturation, journal d'audit append-only, stratégie d'erreurs/versionnage.
- Justifier ces décisions.
- Communiquer clairement l'architecture au reste de l'équipe par des modèles, des vues 4+1 et des ADR de référence.
- Démontrer les gains de l'architecture distribuée par des comparaisons mesurées : direct vs Gateway, N instances, cache on/off.
- Démontrer le respect des paliers NFR phase microservices.

## 3. Objectifs d'apprentissage

À l'issue de ce projet, l'étudiant ou l'étudiante devra être capable de :

1. Concevoir une architecture basée par services évolutive : déployer un BSS télécom composé d'au moins deux microservices fonctionnels dans la machine virtuelle fournie, orchestrés par une API Gateway.
2. Appliquer les principes du Domain-Driven Design (DDD) : identifier les bounded contexts du domaine télécom et tirer les frontières de service à partir du modèle.
3. Mettre en oeuvre des patrons de conception adaptés : intégrer et justifier l'usage de patrons tels que MVC, Architecture hexagonale ou GoF par service.
4. Concevoir une solution de persistance robuste et fiable : implémenter une couche de persistance cohérente par service, garantissant l'intégrité des données, l'idempotence des prises de commande / activations, l'exactly-once des écritures de facturation et un journal d'audit append-only pour la conformité CRTC.
5. Exposer une API RESTful sécurisée : concevoir des endpoints versionnés, documentés avec OpenAPI/Swagger, avec gestion d'erreurs normalisée, CORS, authentification Basic/JWT et MFA pour les opérations sensibles.
6. Instrumenter et mesurer le système : mettre en place les 4 Golden Signals via Prometheus + Grafana et conduire des campagnes de charge réalistes avec k6, JMeter ou Artillery.
7. Optimiser la performance : évaluer et mesurer l'impact du load balancing N = 1..4 instances, du caching mémoire/Redis et de l'API Gateway sur la latence, le débit et la tolérance aux pannes.
8. Documenter et justifier les choix architecturaux : produire des diagrammes UML 4+1 views, compléter au moins trois ADR et structurer la documentation selon le modèle Arc42.
9. Assurer la qualité par les tests automatisés : établir une suite de tests unitaires, d'intégration et end-to-end avec une couverture >= 80 % sur le domaine critique.
10. Mettre en place des pratiques DevOps complètes : maintenir un pipeline CI/CD complet et conteneuriser l'ensemble des services, dépendances et observabilité via Docker Compose.

## 4. Tâches à réaliser

### 4.1 Analyse métier & DDD

#### 1.1 Clarifier le périmètre & cas d'utilisation Must

**Livrables :**

- UC textuels : scénarios principal et alternatifs.
- Priorisation MoSCoW.
- Alignement avec les domaines du cahier.

**Critères d'acceptation :**

- Au moins 5 UC Must du cahier entièrement décrits et validés, parmi :
  - UC-01 Inscription & vérification d'identité;
  - UC-02 Authentification & MFA;
  - UC-03 Activation d'une ligne;
  - UC-04 Consultation usage/factures;
  - UC-05 Prise de commande;
  - UC-06 Paiement de facture;
  - UC-07 Détection de fraude;
  - UC-08 Cycle de facturation mensuel.

#### 1.2 Cartographier le domaine (DDD)

**Livrables :**

- Bounded contexts :
  - Clients & Identité;
  - Lignes & Services;
  - Commandes & Activations;
  - Catalogue & Offres;
  - Usage/Rating/Facturation;
  - Conformité & Audit.
- Ubiquitous language.
- Diagramme de contexte.
- Modèle de domaine : entités, agrégats, value objects.

**Critères d'acceptation :**

- Glossaire validé.
- Agrégats clés identifiés :
  - profils abonnés;
  - lignes/MSISDN;
  - commandes;
  - forfaits;
  - factures.
- Frontières de service tracées à partir des bounded contexts.

### 4.2 Architecture & décisions

#### 2.1 Concevoir l'architecture microservices évolutive

**Livrables :**

- Choix de découpage en services, avec au moins 2 services.
- Style par service : Hexagonal ou MVC.
- Couches & dépendances.
- Stratégie de communication inter-services : REST synchrone en phase 1.

**Critères d'acceptation :**

- Dépendances dirigées sans cycles.
- Couplage contrôlé aux frameworks.
- Bounded contexts mappés sur services.

#### 2.2 Concevoir la couche API RESTful

**Livrables :**

- Routes versionnées `/v1/...`.
- Codes HTTP normalisés.
- Format d'erreur JSON unifié.
- Contrats OpenAPI.

**Référence industrielle optionnelle :**

- TMF620 Product Catalog pour le catalogue.
- TMF622 Product Ordering pour les commandes.
- TMF629 Customer Management pour les clients.
- TMF666 Account Management pour la facturation.

**Critères d'acceptation :**

- Swagger publié.
- Collection Postman fonctionnelle.
- Séparation domain ↔ infra respectée.

#### 2.3 Documenter l'architecture (4+1 + Arc42)

**Livrables :**

- Vues 4+1 :
  - Logique;
  - Processus (C&C);
  - Déploiement;
  - Développement;
  - Scénarios.
- Arc42 sections 1 à 8 :
  - contexte;
  - contraintes;
  - concept solution;
  - décisions;
  - qualité;
  - risques.

**Critères d'acceptation :**

- Chaque vue contient :
  - diagramme;
  - texte;
  - contexte;
  - éléments;
  - relations;
  - rationnel.

#### 2.4 Consigner les décisions structurantes (ADR)

**Livrables :**

- Au moins 3 ADR couvrant :
  - style architectural & découpage en services;
  - persistance/transactions;
  - idempotence des commandes/activations;
  - exactly-once de la facturation;
  - journal append-only pour CRTC/Loi 25;
  - stratégie d'erreurs/versionnage.

**Critères d'acceptation :**

- Format ADR complet : statut, contexte, décision, conséquences.
- Chaque ADR explicitement traçable à une exigence du cahier.

### 4.3 Persistance & intégrité

#### 3.1 Concevoir le schéma de persistance

**Livrables :**

- Modèle logique ER/UML par service.
- Choix ORM ou DAO.
- Transactions.
- Contraintes d'intégrité : unicité MSISDN, FK profils ↔ lignes, index.

**Critères d'acceptation :**

- Migrations reproductibles.
- Données seed pour démo :
  - catalogue de forfaits;
  - abonnés;
  - lignes de test.

#### 3.2 Implémenter la couche de persistance

**Livrables :**

- Repositories/DAOs.
- Mapping.
- Tests d'intégration sur DB conteneurisée.
- Idempotency-key sur prises de commande et activations.
- Garantie exactly-once sur écritures de facturation.
- Journal d'audit append-only pour conformité CRTC.

**Critères d'acceptation :**

- CRUD robuste sur agrégats clés :
  - profils abonnés;
  - lignes/MSISDN;
  - commandes;
  - factures.
- Rollback sur erreurs.
- Double soumission d'une commande sans effet de bord.

### 4.4 Implémentation & API REST sécurisée

#### 4.1 Implémenter le domaine & services applicatifs

**Livrables :**

- Entités, value objects et services par bounded context.
- Validation des règles métier :
  - éligibilité forfait;
  - contrôles anti-fraude SIM swap;
  - vérification MFA.
- Gestion d'erreurs.

**Critères d'acceptation :**

- UC Must couverts au niveau domaine.
- Tests unitaires verts.

#### 4.2 Adapter l'interface (ports/adapters)

**Livrables :**

- Adapters web : controllers REST.
- Adapters persistance.
- Adapters externes simulés :
  - HLR/HSS;
  - hub de portabilité;
  - passerelle de paiement.
- Mapping DTO ↔ domain.

**Critères d'acceptation :**

- Séparation nette domain ↔ infra.
- Aucune logique métier dans les controllers.

#### 4.3 Exposer l'API REST publique

**Livrables :**

- Endpoints REST pour UC Must.
- Swagger/OpenAPI.
- Collection Postman couvrant les scénarios bout-en-bout.

**Critères d'acceptation :**

- Scénario bout-en-bout démontrable dans la VM, par exemple inscription → MFA → activation ligne → souscription forfait → consultation usage.
- Erreurs normalisées JSON.

#### 4.4 Sécurité applicative

**Livrables :**

- CORS.
- Authentification Basic/JWT.
- MFA OTP pour opérations sensibles.
- Validation et assainissement des entrées.
- Gestion d'erreurs uniformisée.
- Secrets gérés via variables d'environnement.
- Journalisation des erreurs.

**Critères d'acceptation :**

- Aucun secret en clair.
- MFA fonctionnel sur authentification UC-02 et activation UC-03.

### 4.5 Observabilité, tests de charge, optimisation

#### 5.1 Observabilité

**Livrables :**

- Logs structurés.
- Métriques applicatives Prometheus.
- Dashboards Grafana.
- 4 Golden Signals :
  - latence P95/P99;
  - trafic RPS;
  - erreurs 4xx/5xx;
  - saturation CPU/RAM/threads.

**Critères d'acceptation :**

- Dashboards opérationnels.
- Captures jointes au rapport.
- Suivi explicite des paliers NFR cibles :
  - P95 <= 500 ms;
  - >= 600 ops/s;
  - disponibilité 95 %.

#### 5.2 Tests de charge (k6/JMeter/Artillery)

**Livrables :**

- Scénarios réalistes :
  - consultation d'usage à cadence élevée UC-04;
  - prise de commande de forfait UC-05;
  - activation de ligne UC-03;
  - authentification MFA UC-02;
  - génération de factures UC-08.
- Stress test progressif jusqu'au seuil de saturation.

**Critères d'acceptation :**

- Rapport de charge avec courbes.
- Vérification des paliers NFR :
  - P95 <= 500 ms;
  - >= 600 ops/s.
- Seuil de saturation identifié.

#### 5.3 Load balancing

**Livrables :**

- NGINX/HAProxy/Traefik en amont des services.
- Tests pour N = 1, 2, 3, 4 instances.
- Tolérance aux pannes : kill d'instance en charge.

**Critères d'acceptation :**

- Graphiques comparatifs :
  - X = instances;
  - Y = latence/RPS/erreurs/saturation.
- Démonstration de la tenue des 95 % de disponibilité sous panne d'une instance.

#### 5.4 Caching

**Livrables :**

- Cache mémoire/Redis sur endpoints coûteux :
  - consultation catalogue de forfaits;
  - consultation usage.
- Règles d'expiration/invalidation.

**Critères d'acceptation :**

- Gains chiffrés :
  - latence;
  - charge DB.
- Discussion des risques de données stale.
- Stratégies d'invalidation lors des mises à jour catalogue.

### 4.6 API Gateway

#### 6.1 Mettre en place l'API Gateway

**Livrables :**

- Kong/KrakenD/Spring Cloud Gateway.
- Routage dynamique.
- Ajout d'en-têtes/clé API.
- CORS.
- Optionnels :
  - journaux d'accès;
  - throttling/quota.

**Critères d'acceptation :**

- Appels fonctionnels via Gateway.
- Configuration versionnée.

#### 6.2 Comparer appels directs vs via Gateway

**Livrables :**

- Campagnes de charge avant/après.
- Analyse :
  - latence;
  - taux d'erreurs;
  - traçabilité.

**Critères d'acceptation :**

- Gains/impacts mesurés et argumentés.
- Résultats intégrés au dashboard.

### 4.7 Qualité, tests & sécurité

#### 7.1 Stratégie de tests

**Livrables :**

- Pyramide de tests :
  - unitaires;
  - intégration;
  - E2E.
- Coverage ciblé.
- Scénarios E2E télécom :
  - inscription;
  - MFA;
  - activation;
  - souscription forfait;
  - paiement.

**Critères d'acceptation :**

- Couverture >= 80 % sur les domaines critiques.
- Scénario E2E qui orchestre 1 UC clé via la Gateway.

#### 7.2 Sécurité applicative & gestion d'erreurs

**Livrables :**

- Codes/messages d'erreur normalisés.
- Validation et assainissement des entrées.
- Contrôles anti-fraude :
  - détection SIM swap;
  - usage anormal.
- Logs d'accès.
- Secrets via variables d'environnement.

**Critères d'acceptation :**

- Aucun secret en clair.
- Journalisation des erreurs cohérente entre services.
- Contrôles anti-fraude testés.

### 4.8 CI/CD & conteneurisation

#### 8.1 Conteneuriser services & infrastructure

**Livrables :**

- Dockerfile multi-stage par service.
- `docker-compose.yml` incluant :
  - services;
  - DB;
  - Prometheus;
  - Grafana;
  - Gateway;
  - cache;
  - seed.
- Healthchecks `/health`.

**Critères d'acceptation :**

- `docker compose up` lance l'ensemble.
- Healthchecks OK.

#### 8.2 Mettre en place la CI

**Livrables :**

- Pipeline :
  - lint;
  - build;
  - tests unitaires;
  - tests d'intégration;
  - tests E2E;
  - artefacts.
- Badge CI.

**Critères d'acceptation :**

- Pipeline déterministe en moins de 10 minutes.
- Fail rapide sur tests KO.

#### 8.3 Préparer un job CD (en VM)

**Livrables :**

- Script de déploiement :
  - compose;
  - swarm;
  - systemd.
- Rollback simple.
- Documentation d'exploitation.

**Critères d'acceptation :**

- Déploiement en une commande.

### 4.9 Documentation finale & démonstration

#### 9.1 Finaliser la documentation

**Livrables :**

- Documentation PDF :
  - Arc42;
  - 4+1;
  - ADR consolidés.
- README :
  - setup;
  - jeu de tests;
  - endpoints.
- Runbook :
  - opérations;
  - observabilité;
  - gestion des pannes.

**Critères d'acceptation :**

- Toute nouvelle personne peut cloner, lancer et tester en moins de 30 minutes.

#### 9.2 Rapport comparatif

**Livrables :**

- Rapport positionnant les NFR cibles du cahier :
  - P95 <= 500 ms;
  - >= 600 ops/s;
  - disponibilité 95 %.
- Résultats atteints.
- Comparaison :
  - appels directs;
  - optimisé LB/cache;
  - via API Gateway.

**Critères d'acceptation :**

- Liens/captures Grafana/Prometheus.
- Tableaux comparatifs avant/après.
- Atteinte des paliers NFR ou écart argumenté.

## 5. Définition de fini (DoD)

- Au moins 5 UC Must du cahier, parmi UC-01 à UC-08, implémentés bout-en-bout via l'API REST : domain + persistence + entrée, erreurs normalisées.
- Au moins 2 microservices conteneurisés + DB + Prometheus + Grafana + API Gateway, déployables via `docker-compose`.
- Idempotence sur prises de commande / activations, exactly-once sur écritures de facturation, journal d'audit append-only opérationnels.
- Tests automatisés en CI : unitaires, intégration, E2E.
- Couverture >= 80 % sur le domaine critique.
- 4 Golden Signals observés via dashboards Grafana.
- Paliers NFR cibles atteints ou écarts argumentés :
  - P95 <= 500 ms;
  - >= 600 ops/s;
  - disponibilité 95 %.
- Campagnes de charge avec comparatifs avant/après, N = 1..4 instances.
- Tolérance aux pannes démontrée.
- LB et cache en production compose avec impacts chiffrés.
- API Gateway opérationnelle.
- Scénarios direct vs gateway comparés et argumentés.
- 4+1 cohérent.
- Arc42 avec sections coeur.
- Au moins 3 ADR approuvés, incluant les décisions de conformité.
- CI/CD fonctionnels.
- Logs structurés.
- Runbook & guide de démo à jour.
- Rapport PDF + dépôt projet zip remis sur Moodle.
- Reproductibilité en moins de 30 minutes sur VM.

## 6. Grille d'évaluation

| Critère | Pondération | Excellent (A) | Satisfaisant (B-C) | Insuffisant (D) | Non réalisé (F) |
| --- | ---: | --- | --- | --- | --- |
| 1. Analyse métier & DDD | 12 % | Au moins 5 UC Must du cahier bien décrits, 6 bounded contexts télécom identifiés, glossaire validé, frontières de service tracées à partir des BCs. | UC partiels, modèle de domaine esquissé mais lacunes de cohérence, frontières floues. | UC peu détaillés, modèle superficiel ou incohérent. | Aucun UC documenté, pas de modèle. |
| 2. Architecture, Décisions & API REST | 18 % | Architecture distribuée claire et rigoureusement justifiée, 4+1 complet, Arc42 sections 1 à 8, au moins 3 ADR solides, API REST versionnée + Swagger + Postman + erreurs normalisées. | Architecture définie mais justification limitée, 4+1/Arc42 partiels, 2 ADR seulement, API REST incomplète. | Architecture floue, vues manquantes, API limitée ou fragile. | Pas d'architecture documentée ni d'API. |
| 3. Persistance & intégrité | 12 % | Schéma robuste par service, migrations reproductibles, idempotency-key, exactly-once, audit append-only, intégrité validée. | Persistance fonctionnelle mais design incomplet, contraintes manquantes, seeds partiels, tests d'intégration minimes, conformité partielle. | Persistance fragile, CRUD incomplet, garanties faibles. | Pas de persistance. |
| 4. Microservices & API Gateway | 18 % | Au moins 2 microservices conteneurisés avec frontières alignées sur les bounded contexts télécom, communication inter-services maîtrisée, API Gateway opérationnelle, comparatifs direct vs Gateway argumentés. | Services/Gateway fonctionnels mais incomplets, frontières mal justifiées, comparatifs partiels. | Microservices/Gateway peu fonctionnels, découpage incohérent. | Aucun découpage / Gateway. |
| 5. Observabilité & Tests de charge | 10 % | 4 Golden Signals + dashboards Grafana, scénarios de charge réalistes, paliers NFR cibles atteints, seuils de saturation identifiés. | Observabilité/tests partiels, paliers NFR partiellement atteints. | Mesures peu fiables, paliers non vérifiés. | Aucune mesure. |
| 6. Load Balancing & Caching | 10 % | LB multi-instances N = 1..4 + cache efficaces, gains mesurés et discutés, tolérance aux pannes démontrée. | LB/cache partiels, gains peu chiffrés. | Gains non démontrés. | Aucun LB/cache. |
| 7. Qualité, tests & sécurité | 10 % | Suite complète unit/int/E2E, couverture > 80 %, sécurité minimale, validation, MFA, erreurs normalisées, secrets protégés, contrôles anti-fraude testés. | Tests présents mais E2E incomplet, couverture < 80 %, sécurité partielle. | Tests superficiels, absence de stratégie. | Pas de tests automatisés. |
| 8. CI/CD, Documentation & démo | 10 % | Pipeline CI < 10 min, compose multi-service avec healthchecks, déploiement scripté + rollback, rapport PDF clair, reproductibilité < 30 min. | CI/CD fonctionnel mais fragile, doc partielle, reproductibilité partielle. | CI/CD partiel ou non reproductible, doc superficielle. | Pas de CI/CD ni de doc. |

## 7. Barème indicatif

| Note | Pourcentage | Description |
| --- | ---: | --- |
| A | 85-100 % | Projet complet, robuste, paliers NFR atteints, documentation claire. |
| B | 70-84 % | Projet solide mais avec lacunes : documentation, tests, observabilité ou conformité. |
| C | 60-69 % | Fonctionnel mais partiel, preuves de performance limitées. |
| D | 50-59 % | Incomplet, architecture fragile ou mal documentée. |
| F | < 50 % | Non fonctionnel ou livrables incohérents. |
