# ADR 0004 - Idempotence, facturation exactly-once et audit append-only

## Statut

Accepté

## Contexte

Certaines opérations CanTelcoX sont sensibles parce qu'elles déclenchent des effets métier difficiles à corriger: prise de commande, activation de ligne, enregistrement d'usage, génération de facture, paiement et événements de conformité.

Le cahier de charge demande explicitement:

- l'idempotence des commandes et activations;
- l'exactly-once des écritures de facturation;
- un journal d'audit append-only pour la conformité CRTC, Loi 25 et LPRPDE;
- des contrôles contre la fraude comme le SIM swap et l'usurpation d'identité.

Dans un système distribué, un client ou un service peut répéter une requête après un timeout, une erreur réseau ou une réponse inconnue. Sans stratégie d'idempotence, une même intention peut créer plusieurs commandes, activer plusieurs fois une ligne, facturer deux fois un usage ou produire un audit incomplet.

## Forces de décision

- Éviter les doubles effets métier lors des retries.
- Conserver une trace réglementaire fiable et non destructive.
- Garantir que les écritures de billing ne sont pas appliquées deux fois.
- Rendre les échecs distribués diagnostiquables avec un identifiant de corrélation.
- Garder les garanties critiques au plus près des services responsables.
- Éviter une transaction distribuée globale en phase 1.

## Options considérées

| Option | Exemple | Avantages | Inconvénients |
| --- | --- | --- | --- |
| Retries simples sans idempotence | Le frontend relance `POST /v1/orders` après un timeout sans clé stable | Simple à implémenter | Risque de commandes, activations ou paiements dupliqués |
| Transaction distribuée globale | Une transaction unique coordonne `order-service`, `billing-service`, `audit-service` et leurs bases pour valider une commande | Cohérence forte théorique | Complexe, fragile, peu adaptée au laboratoire et aux services REST |
| Idempotence locale + contraintes uniques + audit append-only | `order-service` déduplique avec `Idempotency-Key`, `billing-service` impose une unicité sur `externalUsageId`, `audit-service` ajoute des événements append-only | Pragmatique, testable, aligné microservices | Demande une discipline par service et une bonne gestion des clés |

## Décision

Utiliser une combinaison de clés d'idempotence, contraintes uniques, statuts métier contrôlés, écritures append-only et corrélation de traces.

### Commandes et activations

Les opérations de création de commande et d'activation doivent accepter une clé d'idempotence fournie par le client ou générée par l'orchestrateur.

Le `order-service` stocke la clé avec:

- l'identité du demandeur;
- le type d'opération;
- une empreinte de la requête;
- le statut de traitement;
- la réponse métier stable à retourner en cas de retry.

Une réutilisation de la même clé avec le même contenu retourne le résultat déjà enregistré. Une réutilisation de la même clé avec un contenu différent doit être rejetée.

### Facturation exactly-once

Le `billing-service` applique les écritures de facturation une seule fois par référence métier externe, par exemple `externalUsageId`, `paymentReference` ou identifiant de cycle.

Les écritures critiques doivent utiliser:

- une contrainte unique sur la référence externe;
- une transaction locale;
- un statut explicite;
- une trace d'audit associée;
- une réponse stable lors d'un retry.

Le système ne promet pas une livraison réseau exactly-once. Il vise un effet métier exactly-once dans la base du service responsable.

### Audit append-only

Le `audit-service` conserve les événements sensibles en insertion seule. Les événements ne sont pas mis à jour ni supprimés par les flux applicatifs ordinaires.

Chaque événement d'audit doit contenir au minimum:

- un identifiant d'événement;
- un `traceId` ou identifiant de corrélation;
- l'acteur;
- l'action;
- la ressource visée;
- l'horodatage;
- le résultat;
- les signaux de risque pertinents.

Les corrections éventuelles se font par ajout d'un nouvel événement compensatoire, pas par modification de l'événement initial.

## Conséquences

- Les retries deviennent sûrs pour les opérations critiques si la même clé est réutilisée correctement.
- Les doubles soumissions peuvent être détectées et retournées sans effet de bord.
- Les erreurs réseau restent possibles, mais les effets persistés sont contrôlés par le service propriétaire.
- Les services doivent exposer et documenter les règles d'utilisation des clés d'idempotence.
- Les contraintes de base de données deviennent une partie active de l'architecture, pas seulement un détail technique.
- Les opérations sensibles deviennent plus faciles à diagnostiquer grâce au `traceId` et au journal append-only.
- Les politiques de rétention, d'accès aux données personnelles et d'anonymisation doivent être précisées pour respecter Loi 25/LPRPDE.

## Conformité

Cette décision répond aux exigences du cahier de charge sur:

- l'idempotence des prises de commande et activations;
- l'exactly-once des écritures de facturation;
- le journal d'audit append-only;
- la conformité CRTC, Loi 25 et LPRPDE;
- la traçabilité des opérations sensibles et des contrôles anti-fraude.

La conformité est vérifiée par:

- des contraintes uniques sur les clés d'idempotence et références externes;
- des tests de double soumission;
- des tests de retry après timeout ou erreur simulée;
- l'existence d'événements d'audit pour les opérations sensibles;
- la propagation du `X-Trace-Id` par le gateway vers les services amont.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-23.
- Cette décision complète l'ADR 0003 sur la persistance par service.
- Le terme exactly-once désigne ici l'effet métier persistant, pas une garantie absolue de livraison réseau.
