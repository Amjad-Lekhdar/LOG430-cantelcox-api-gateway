# 10. Exigences de qualité

Cette section correspond aux scénarios +1 de Kruchten.

## 10.1 Arbre de qualité

```text
Qualité
├── Déployabilité
│   └── Lancer le gateway indépendamment des services métier
├── Maintenabilité
│   └── Modifier les URLs et routes sans refactor majeur
├── Disponibilité
│   └── Identifier rapidement un service indisponible
├── Observabilité
│   └── Voir l'état des services via /health, /metrics et Blackbox Exporter
├── Intégration réseau 5G
│   └── Activer une ligne via free5GC sans exposer le coeur réseau publiquement
├── Évolutivité fonctionnelle
│   └── Ajouter de nouveaux domaines métier
└── Simplicité
    └── Garder le MVP compréhensible
```

## 10.2 Scénarios de qualité

| ID | Catégorie | Source | Stimulus | Réponse | Mesure |
| --- | --- | --- | --- | --- | --- |
| Q1 | Maintenabilité | Équipe backend | L'adresse du service d'identité change | Mettre à jour `IDENTITY_SERVICE_URL` sans changer le code | Redémarrage avec nouvelle variable |
| Q2 | Disponibilité | Client API | Appel `/v1/billing/*` sans service configuré | Retourner `503` avec un message explicite | Réponse HTTP immédiate |
| Q3 | Disponibilité | Client API | `order-service` est inaccessible | Retourner `502` avec la cible amont | Timeout maximal 15 s |
| Q4 | Observabilité | Opérateur | Appel `GET /health` | Retourner `200` si l'application est active | Endpoint utilisable par Blackbox Exporter |
| Q5 | Diagnostic | Opérateur | Appel `GET /routes` | Lister les URLs chargées au démarrage | Table lisible en JSON |
| Q6 | Intégration free5GC | Abonné / agent | Activation d'une ligne après commande | `line-service` provisionne SUPI/SIM/DNN/slice via l'adapter free5GC | Ligne active ou erreur réseau explicite |
| Q7 | Traçabilité | Exploitation | Erreur amont ou activation sensible | Propager `X-Trace-Id` et journaliser le résultat | Logs corrélables gateway/service |

## 10.3 Cibles NFR

| Indicateur | Cible | Mécanisme actuel / cible |
| --- | --- | --- |
| Latence P95 | <= 500 ms | Gateway proxy léger, mesure via k6 et Prometheus |
| Débit | >= 600 opérations/s | Load balancing démontré sur `catalog-service` |
| Disponibilité | 95 % | `/health`, erreurs explicites, HAProxy sur service pilote |
| Observabilité | 4 Golden Signals | `/metrics` gateway, Blackbox Exporter, Grafana |
| Sécurité/auditabilité | Opérations sensibles traçables | `X-Trace-Id`, `audit-service`, idempotence côté services |

## 10.4 Priorités

1. Déployabilité en environnement laboratoire.
2. Maintenabilité de la configuration réseau.
3. Observabilité minimale fiable.
4. Démonstration d'activation free5GC encapsulée par adapter.
5. Ajout progressif de sécurité, rate limiting et métriques par service.
