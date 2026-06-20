# Backlog de finition - CanTelcoX

Ce backlog resume le travail restant pour rapprocher le projet des criteres du cahier de charge LOG430. Il distingue les elements deja amorces dans le depot API Gateway des livrables encore a produire ou a demontrer.

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
| B-01 | ADR et decisions d'architecture | P0 | En cours | ADR complets, traçables au cahier de charge |
| B-02 | Documentation Arc42 et 4+1 | P0 | En cours | Documentation finale coherente avec l'etat reel du systeme |
| B-03 | Cas d'utilisation Must | P0 | A faire | Au moins 5 UC Must decrits et relies aux services |
| B-04 | Tests automatises du gateway | P0 | A faire | Tests unitaires/integration pour les routes critiques |
| B-05 | Observabilite | P0 | En cours | Health, logs structures, metriques Prometheus, dashboard Grafana |
| B-06 | Docker Compose complet | P0 | En cours | Gateway, services, DB, observabilite et healthchecks lancables |
| B-07 | Performance et charge | P1 | A faire | Mesures k6/JMeter/Artillery et comparaison des variantes |
| B-08 | Securite applicative | P1 | En cours | CORS, erreurs uniformes, auth/MFA documentee ou implementee |
| B-09 | Runbook et guide de demo | P1 | A faire | Procedure de lancement, diagnostic et demonstration |
| B-10 | Rapport final et preuves | P1 | A faire | Captures, tableaux de resultats, ecarts argumentes |

## B-01 - Completer les ADR

Priorite: P0  
Statut: En cours

### Taches

- [ ] Completer `docs/adr/0001-architecture-microservices.md`.
- [ ] Completer `docs/adr/0002-api-gateway.md`.
- [ ] Completer `docs/adr/0003-database-per-service.md`.
- [ ] Completer `docs/adr/0004-idempotence-audit-billing.md`.
- [ ] Harmoniser les statuts, dates, decideurs et consequences.
- [ ] Verifier que chaque ADR reference une exigence du cahier de charge.

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
- [ ] Completer la vue logique avec les bounded contexts metier.
- [ ] Completer la vue processus avec les scenarios UC Must.
- [ ] Completer la vue de deploiement avec les VM/LXC, Tailnet, gateway, observabilite et services.
- [ ] Completer la vue developpement avec structure des depots/services.
- [ ] Ajouter les limites connues et les ecarts par rapport au cahier.

### Criteres d'acceptation

- Les sections coeur Arc42 sont lisibles sans dependance a l'oral.
- Chaque vue 4+1 contient un diagramme texte ou UML et un rationnel.
- Les risques et dettes techniques sont explicites.

## B-03 - Documenter au moins 5 UC Must

Priorite: P0  
Statut: A faire

### Taches

- [ ] Decrire UC-01 Inscription et verification d'identite.
- [ ] Decrire UC-02 Authentification et MFA.
- [ ] Decrire UC-03 Activation d'une ligne.
- [ ] Decrire UC-04 Consultation usage/factures.
- [ ] Decrire UC-05 Prise de commande.
- [ ] Optionnel: decrire UC-06 Paiement de facture.
- [ ] Optionnel: decrire UC-07 Detection de fraude.
- [ ] Optionnel: decrire UC-08 Cycle de facturation mensuel.
- [ ] Relier chaque UC au service responsable et a la route gateway.

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
Statut: A faire

### Taches

- [ ] Ajouter une configuration de test Python.
- [ ] Tester `GET /health`.
- [ ] Tester `GET /routes`.
- [ ] Tester une route inconnue avec reponse `404`.
- [ ] Tester une route connue mais non configuree avec reponse `503`.
- [ ] Tester un upstream indisponible avec reponse `502`.
- [ ] Tester le proxy vers un service mock.
- [ ] Ajouter la commande de test dans le README.

### Criteres d'acceptation

- Les tests se lancent avec une commande unique.
- Les routes critiques du gateway sont couvertes.
- Les erreurs JSON sont verifiees.

## B-05 - Completer l'observabilite

Priorite: P0  
Statut: En cours

### Taches

- [ ] Ajouter des logs structures au gateway.
- [ ] Ajouter un endpoint `/metrics` Prometheus.
- [ ] Definir les metriques: trafic, latence, erreurs, saturation.
- [ ] Documenter Prometheus, Grafana et Blackbox Exporter.
- [ ] Ajouter des captures Grafana au rapport final.
- [ ] Montrer les endpoints `/health` de chaque service.

### Criteres d'acceptation

- Les 4 Golden Signals sont couverts:
  - latence P95/P99;
  - trafic RPS;
  - erreurs 4xx/5xx;
  - saturation CPU/RAM/threads.
- Les paliers NFR sont suivis explicitement: P95 <= 500 ms, debit >= 600 ops/s, disponibilite 95 %.

## B-06 - Rendre Docker Compose plus complet

Priorite: P0  
Statut: En cours

### Taches

- [ ] Ajouter les healthchecks au gateway.
- [ ] Ajouter les services disponibles au compose si leurs images/depots sont accessibles.
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
Statut: A faire

### Taches

- [ ] Ajouter des scripts k6, JMeter ou Artillery.
- [ ] Tester consultation catalogue ou usage a haute cadence.
- [ ] Tester prise de commande.
- [ ] Tester activation de ligne si le service existe.
- [ ] Comparer appels directs vs via gateway.
- [ ] Comparer cache off vs cache on.
- [ ] Comparer N = 1, 2, 3, 4 instances.
- [ ] Documenter un test de panne en charge.

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
Statut: A faire

### Taches

- [ ] Completer `docs/runbook.md`.
- [ ] Ajouter les commandes de demarrage.
- [ ] Ajouter les commandes de verification sante.
- [ ] Ajouter les commandes de diagnostic `502`, `503`, CORS et Tailnet.
- [ ] Ajouter le scenario de demonstration.
- [ ] Ajouter les URLs Swagger, Prometheus et Grafana.
- [ ] Ajouter une procedure de rollback simple.

### Criteres d'acceptation

- Une personne externe peut cloner, lancer et tester en moins de 30 minutes.
- Le runbook explique quoi faire quand un service amont ne repond pas.

## B-10 - Preparrer le rapport final et les preuves

Priorite: P1  
Statut: A faire

### Taches

- [ ] Generer ou assembler le PDF final.
- [ ] Ajouter captures Swagger.
- [ ] Ajouter captures Grafana.
- [ ] Ajouter captures de tests ou logs CI.
- [ ] Ajouter resultats de charge.
- [ ] Ajouter tableau direct vs gateway vs optimise.
- [ ] Ajouter tableau des exigences et statut: fait, partiel, non fait, justification.

### Criteres d'acceptation

- Le rapport relie chaque exigence importante a une preuve.
- Les ecarts sont assumés et argumentes.
- Le depot remis contient README, Arc42, ADR, runbook et scripts utiles.

## Ordre recommande

1. Completer les ADR vides.
2. Completer le runbook.
3. Ajouter les tests du gateway.
4. Ajouter les metriques et logs structures.
5. Mettre a jour Docker Compose.
6. Documenter les 5 UC Must.
7. Produire les tests de charge.
8. Finaliser Arc42 et le rapport PDF.

## Definition de fini locale

- [ ] Au moins 5 UC Must sont documentes.
- [ ] Le gateway est testable automatiquement.
- [ ] Les ADR principaux sont complets.
- [ ] Arc42 decrit l'etat reel du systeme.
- [ ] Docker Compose lance une pile exploitable.
- [ ] L'observabilite montre au moins la disponibilite et les premiers signaux.
- [ ] Les resultats de charge ou les ecarts NFR sont documentes.
- [ ] Le runbook permet une demonstration reproductible.
