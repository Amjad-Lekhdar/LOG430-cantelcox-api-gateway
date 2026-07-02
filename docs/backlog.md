# Backlog de finition - CanTelcoX

Ce backlog resume le travail restant pour rapprocher le projet des criteres du cahier de charge LOG430. Il distingue les elements deja amorces dans le depot API Gateway des livrables encore a produire ou a demontrer.

Derniere mise a jour: 23 juin 2026.

## Legende

| Priorite | Sens |
| --- | --- |
| P0 | Necessaire pour un rendu credible et directement lie a la definition de fini |
| P1 | Important pour maximiser la note et couvrir les criteres d'acceptation |
| P2 | Amelioration utile si le temps le permet |

| Statut | Sens |
| --- | --- |
| A faire | Non realise ou non visible dans ce depot |
| En cours | Base presente, mais incomplete |
| Fait | Livrable present et exploitable |

## Vue d'ensemble

| ID | Epic | Priorite | Statut | Resultat attendu |
| --- | --- | --- | --- | --- |
| B-01 | ADR et decisions d'architecture | P0 | Fait | ADR complets, traçables au cahier de charge |
| B-02 | Documentation Arc42 et 4+1 | P0 | En cours | Documentation finale coherente avec l'etat reel du systeme |
| B-03 | Cas d'utilisation Must | P0 | Fait | 5 UC Must decrits et relies aux services |
| B-04 | Tests automatises du gateway | P0 | Fait | Tests unitaires pour les routes critiques du gateway |
| B-05 | Observabilite | P0 | En cours | Gateway instrumente; Prometheus/Grafana raccordes pour la demo; preuves a garder synchronisees |
| B-06 | Docker Compose complet | P0 | En cours | Gateway, Redis et load balancer lancables; services metier maintenus dans des depots separes |
| B-07 | Performance et charge | P1 | En cours | Mesures k6 catalogue, cache, direct/gateway et load balancing integrees; saturation haute cadence a approfondir |
| B-08 | Securite applicative | P1 | En cours | CORS, erreurs uniformes, auth/MFA documentee ou implementee |
| B-09 | Runbook et guide de demo | P1 | En cours | Procedure de lancement, diagnostic et demonstration |
| B-10 | Rapport final et preuves | P1 | En cours | Captures et tableaux principaux integres; PDF final et coherence finale a produire |

## Progres documentaire recent

- [x] Vue niveau 1 du systeme et interactions entre services: `docs/diagrams/plantuml/building-blocks-5-1.svg`.
- [x] Vues niveau 2 de l'API Gateway et des six services selon l'architecture hexagonale: `docs/diagrams/plantuml/level2/`.
- [x] Modele de domaine logique: `docs/diagrams/plantuml/domain-model-5-3.svg`.
- [x] Scenario d'execution E2E nominal: `docs/diagrams/plantuml/runtime-e2e-6-1.svg`.
- [x] Sections 5.1, 5.2, 5.3 et 6.1 integrees dans `docs/Gabarit_LOG430_Phase1_Architecture_v3_1.md`.
- [x] Choix PostgreSQL par service documente dans la vue d'architecture.

## B-01 - Completer les ADR

Priorite: P0  
Statut: Fait

### Taches

- [x] Completer `docs/adr/0001-architecture-microservices.md`.
- [x] Completer `docs/adr/0002-api-gateway.md`.
- [x] Completer `docs/adr/0003-database-per-service.md`.
- [x] Completer `docs/adr/0004-idempotence-audit-billing.md`.
- [x] Harmoniser les statuts, dates, decideurs et consequences.
- [x] Verifier que chaque ADR reference une exigence du cahier de charge.

### Criteres d'acceptation

- Chaque ADR contient: statut, contexte, forces de decision, options, decision, consequences.
- Les decisions couvrent au minimum:
  - style microservices et decoupage par domaines;
  - API Gateway;
  - database per service;
  - idempotence, exactly-once billing et audit append-only.
- Les ADR sont references depuis `docs/arc42.md`.

## B-02 - Finaliser Arc42 et les vues 4+1

Priorite: P0  
Statut: En cours

### Taches

- [ ] Ajouter une section "Etat d'implementation" dans `docs/arc42.md`.
- [ ] Distinguer clairement ce qui est implemente, simule, configure hors depot et prevu.
- [x] Completer la vue logique avec les bounded contexts metier.
- [x] Completer la vue processus avec un scenario E2E couvrant les UC Must.
- [x] Completer la vue de deploiement avec les VM/LXC, reseau prive, gateway, observabilite et services.
- [x] Completer la vue developpement avec la structure du gateway et la cible hexagonale des services.
- [x] Ajouter les limites connues et les ecarts par rapport au cahier.

### Criteres d'acceptation

- Les sections coeur Arc42 sont lisibles sans dependance a l'oral.
- Chaque vue 4+1 contient un diagramme texte ou UML et un rationnel.
- Les risques et dettes techniques sont explicites.

## B-03 - Documenter au moins 5 UC Must

Priorite: P0  
Statut: Fait

### Taches

- [x] Decrire UC-01 Inscription et verification d'identite.
- [x] Decrire UC-02 Authentification et MFA.
- [x] Decrire UC-03 Activation d'une ligne.
- [x] Decrire UC-04 Consultation usage/factures.
- [x] Decrire UC-05 Prise de commande.
- [ ] Optionnel: decrire UC-06 Paiement de facture.
- [ ] Optionnel: decrire UC-07 Detection de fraude.
- [ ] Optionnel: decrire UC-08 Cycle de facturation mensuel.
- [x] Relier chaque UC au service responsable et a la route gateway.

Preuve: section 1.2 de `docs/Gabarit_LOG430_Phase1_Architecture_v3_1.md`.

### Criteres d'acceptation

- Au moins 5 UC Must ont:
  - acteur principal;
  - preconditions;
  - scenario nominal;
  - scenarios alternatifs;
  - erreurs principales;
  - endpoints concernes;
  - preuve ou statut d'implementation.

## B-04 - Ajouter les tests automatises du gateway

Priorite: P0  
Statut: Fait

### Taches

- [x] Ajouter une configuration de test Python.
- [x] Tester `GET /health`.
- [x] Tester `GET /routes`.
- [x] Tester une route inconnue avec reponse `404`.
- [x] Tester une route connue mais non configuree avec reponse `503`.
- [x] Tester un upstream indisponible avec reponse `502`.
- [x] Tester le proxy vers un service mock.
- [x] Ajouter la commande de test dans le README.

Preuve: `tests/test_gateway.py`; validation locale `6 passed in 0.24s`.

### Criteres d'acceptation

- Les tests se lancent avec une commande unique.
- Les routes critiques du gateway sont couvertes.
- Les erreurs JSON sont verifiees.

## B-05 - Completer l'observabilite

Priorite: P0  
Statut: En cours

### Taches

- [x] Ajouter des logs structures au gateway.
- [x] Ajouter un endpoint `/metrics` Prometheus.
- [x] Definir les metriques gateway: trafic, latence, erreurs, requetes en cours et saturation processus.
- [x] Propager un `X-Trace-Id` vers les services amont.
- [x] Documenter les metriques gateway dans le README, le runbook et Arc42.
- [ ] Raccorder `/metrics` du gateway dans Prometheus.
- [ ] Ajouter/mettre a jour les dashboards Grafana pour les metriques gateway.
- [ ] Documenter Prometheus, Grafana et Blackbox Exporter cote observability.
- [ ] Ajouter des captures Grafana au rapport final.
- [ ] Montrer les endpoints `/health` de chaque service accessible depuis les depots separes.

### Criteres d'acceptation

- Les 4 Golden Signals sont couverts:
  - latence P95/P99;
  - trafic RPS;
  - erreurs 4xx/5xx;
  - saturation CPU/RAM/threads.
- Les paliers NFR sont suivis explicitement: P95 <= 500 ms, debit >= 600 ops/s, disponibilite 95 %.

### Etat actuel

- Cote gateway: logs JSON, `X-Trace-Id`, `/metrics` et metriques Prometheus applicatives sont en place.
- Cote observability: Prometheus/Grafana/Blackbox existent dans le depot dedie. Les captures principales sont integrees au rapport; il reste a garder les dashboards et les preuves synchronises avec l'environnement de demo.

## B-06 - Rendre Docker Compose plus complet

Priorite: P0  
Statut: En cours

### Taches

- [ ] Ajouter les healthchecks au gateway.
- [ ] Documenter comment lancer ou joindre les services metier maintenus dans leurs depots GitHub separes.
- [ ] Ajouter PostgreSQL pour les services persistants si applicable.
- [ ] Ajouter Prometheus.
- [ ] Ajouter Grafana.
- [ ] Ajouter Blackbox Exporter.
- [ ] Ajouter Redis ou cache memoire documente si utilise.
- [ ] Ajouter les variables d'environnement dans `.env.example`.

### Criteres d'acceptation

- `docker compose up` lance une pile demonstrable.
- Les services exposes repondent a `/health`.
- Le README indique les ports et les URLs utiles.

## B-07 - Produire les tests de charge et comparatifs

Priorite: P1  
Statut: En cours

### Taches

- [x] Ajouter un script k6 initial pour le load balancing catalogue.
- [x] Tester consultation catalogue a haute cadence via gateway + HAProxy pour N = 1.
- [ ] Tester prise de commande via le service du depot separe.
- [ ] Tester activation de ligne via le service du depot separe.
- [x] Comparer appels directs vs via gateway.
- [x] Comparer cache off vs cache on.
- [x] Comparer N = 1, 2, 3, 4 instances sur `catalog-service` comme service pilote.
- [x] Documenter un test de panne en charge sur une instance `catalog-service`.
- [x] Décrire le patron HAProxy réplicable aux autres services sans l'implémenter partout.

### Criteres d'acceptation

- Le rapport contient des tableaux de latence, RPS et erreurs.
- Le seuil de saturation est identifie.
- Les ecarts aux paliers NFR sont expliques si les cibles ne sont pas atteintes.

## B-08 - Completer la securite applicative

Priorite: P1  
Statut: En cours

### Taches

- [ ] Documenter la strategie d'authentification: Basic, JWT ou delegation aux services.
- [ ] Documenter MFA pour les operations sensibles.
- [ ] Normaliser le format d'erreur JSON.
- [ ] Verifier que les secrets passent par variables d'environnement.
- [ ] Ajouter ou documenter les controles anti-fraude SIM swap.
- [ ] Ajouter une section sur la protection Loi 25/LPRPDE.

### Criteres d'acceptation

- Aucune cle ou secret en clair dans le depot.
- Les operations sensibles ont une strategie MFA.
- Les erreurs sont coherentes entre gateway et services.

## B-09 - Completer le runbook et le guide de demo

Priorite: P1  
Statut: En cours

### Taches

- [x] Documenter le reseau, les adresses et le diagnostic dans `docs/runbook.md`.
- [ ] Ajouter les commandes de demarrage.
- [x] Ajouter les commandes de verification sante.
- [x] Ajouter le diagnostic du reseau prive LXC/Tailscale et des services injoignables.
- [ ] Ajouter les commandes de diagnostic applicatif `502`, `503` et CORS.
- [ ] Ajouter le scenario de demonstration.
- [ ] Ajouter les URLs Swagger, Prometheus et Grafana.
- [ ] Ajouter une procedure de rollback simple.

### Criteres d'acceptation

- Une personne externe peut cloner, lancer et tester en moins de 30 minutes.
- Le runbook explique quoi faire quand un service amont ne repond pas.

## B-10 - Preparrer le rapport final et les preuves

Priorite: P1  
Statut: En cours

### Taches

- [ ] Generer ou assembler le PDF final.
- [ ] Ajouter captures Swagger.
- [x] Ajouter captures Grafana.
- [ ] Ajouter captures de tests ou logs CI.
- [x] Ajouter resultats de charge.
- [x] Ajouter tableau direct vs gateway vs optimise.
- [ ] Ajouter tableau des exigences et statut: fait, partiel, non fait, justification.

### Criteres d'acceptation

- Le rapport relie chaque exigence importante a une preuve.
- Les ecarts sont assumés et argumentes.
- Le depot remis contient README, Arc42, ADR, runbook et scripts utiles.

## Ordre recommande

1. Completer les ADR vides.
2. Ajouter les tests du gateway.
3. Ajouter les metriques et logs structures.
4. Mettre a jour Docker Compose.
5. Completer le runbook et le scenario de demonstration.
6. Finaliser l'etat d'implementation dans Arc42.
7. Produire les tests de charge.
8. Finaliser le rapport PDF et les preuves.

## Definition de fini locale

- [x] Au moins 5 UC Must sont documentes.
- [ ] Le gateway est testable automatiquement.
- [ ] Les ADR principaux sont complets.
- [ ] Arc42 decrit l'etat reel du systeme.
- [ ] Docker Compose lance une pile exploitable.
- [ ] L'observabilite montre au moins la disponibilite et les premiers signaux.
- [ ] Les resultats de charge ou les ecarts NFR sont documentes.
- [ ] Le runbook permet une demonstration reproductible.
