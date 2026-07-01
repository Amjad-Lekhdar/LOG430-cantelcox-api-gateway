# 11. Risques et dette technique

## 11.1 Risques actuels

| ID | Description | Probabilité | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | URLs amont incorrectes | Moyenne | Élevé | `/routes` expose la configuration active; ajouter des tests de connectivité automatisés. |
| R2 | Services futurs non disponibles | Élevée | Moyen | Variables vides et réponse `503`; créer les services et renseigner les URLs. |
| R3 | Pas de découverte de services | Moyenne | Moyen | `.env` centralisé; évaluer DNS interne, service registry ou convention Tailnet. |
| R4 | Métriques applicatives partielles | Moyenne | Moyen | `/health`, Blackbox Exporter et `/metrics` gateway; ajouter `/metrics` par service. |
| R5 | Sécurité API incomplète | Moyenne | Élevé | Définir authentification, autorisation et rate limiting. |
| R6 | Proxy HTTP synchrone | Faible | Moyen | Évaluer `httpx` async et timeouts par service. |
| R7 | Indisponibilité ou mauvaise configuration free5GC | Moyenne | Élevé | Garder l'intégration derrière l'adapter d'activation; retourner une erreur métier explicite; ajouter un test de santé/provisioning côté service. |
| R8 | Couplage involontaire aux fonctions réseau 5G | Faible | Moyen | Ne pas exposer AMF/SMF/UDM/UDR/UPF au gateway ni à `order-service`; maintenir un port `Free5gcPort` dans `line-service`. |

## 11.2 Dette technique connue

- Les ADR doivent rester synchronisées avec l'état réel des services pendant la fin de phase.
- Les routes clients, facturation et audit sont prêtes et configurables; les preuves de démonstration doivent rester à jour.
- Les tests automatisés du gateway existent, mais les tests d'intégration inter-services restent à compléter.
- Les métriques applicatives Prometheus sont exposées par le gateway; les autres services doivent encore être raccordés progressivement.
- Le scénario free5GC doit être complété par des preuves de configuration et de test côté `line-service`.

## 11.3 Points à clarifier

- Adresse Tailnet définitive du coeur free5GC.
- Convention de configuration de l'adapter free5GC (`SUPI`, DNN, slice, credentials éventuels).
- Noms définitifs des services amont pour clients, facturation et audit.
- Politique d'authentification au niveau gateway.
- Format cible des logs et corrélation des requêtes entre services.
