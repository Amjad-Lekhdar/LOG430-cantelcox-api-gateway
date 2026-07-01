# ADR 0005 - Environnement d'observabilité dédié

## Statut

Accepté

## Contexte

CanTelcoX est déployé sous forme de microservices exécutés sur des VM/LXC distinctes. Comme chaque service peut être hébergé sur une machine différente, il devient nécessaire d'observer l'état des VM afin de vérifier qu'elles restent disponibles et qu'elles ne régressent pas en termes de performance.

## Options considérées

| Option | Exemple | Avantages | Inconvénients |
| --- | --- | --- | --- |
| Observabilité locale dans chaque dépôt | Chaque service lance son propre Prometheus ou ses propres scripts de surveillance | Simple pour un service isolé | Vision fragmentée, duplication de configuration, comparaison difficile entre services |
| Observabilité sur la même machine que le gateway | Prometheus, Grafana et Blackbox Exporter tournent à côté de `api-gateway` | Déploiement initial rapide, accès simple aux métriques gateway | Couplage avec le gateway, risque de perte d'observabilité si cette machine tombe |
| Environnement d'observabilité dédié | Un hôte `cantelcox-observability` exécute Prometheus, Blackbox Exporter et Grafana pour superviser les endpoints `/health` | Supervision centralisée, indépendante des services applicatifs, adaptée aux VM/LXC | Environnement supplémentaire à maintenir, connectivité réseau à surveiller |
| Solution SaaS externe | Datadog, Grafana Cloud ou équivalent collecte les métriques et alertes | Fonctionnalités avancées, moins d'exploitation locale | Dépendance externe, coût possible, moins adapté au laboratoire hors Internet |

## Décision

Déployer une pile d'observabilité dans un environnement dédié nommé `cantelcox-observability`.

Pour le laboratoire, cet environnement peut être un conteneur LXC, une VM ou un hôte Linux dédié. Le projet n'impose pas de plateforme de virtualisation particulière.

L'environnement d'observabilité contient le code et la configuration de supervision. Les microservices applicatifs tournent sur des VM séparées et sont référencés depuis la configuration des cibles Prometheus.

La pile initiale contient:

- Prometheus pour la collecte et le stockage des métriques.
- Blackbox Exporter pour sonder les endpoints HTTP de santé.
- Grafana pour les tableaux de bord.

La pile est définie dans `infrastructure/observability/docker-compose.yml` et déployée avec Docker Compose. Les endpoints des VM de microservices sont listés dans `infrastructure/observability/prometheus/targets/microservices.yml`.

## Conséquences

- L'observabilité peut être opérée indépendamment de la pile applicative.
- La supervision de santé fonctionne immédiatement grâce aux endpoints `/health` existants.
- Les métriques applicatives par service nécessitent une étape d'instrumentation ultérieure, par exemple l'exposition de `/metrics` dans chaque service FastAPI.
- La connectivité réseau entre l'environnement d'observabilité et les services applicatifs doit être maintenue.

## Conformité

La conformité à cette décision est vérifiée par:

- la présence d'un environnement distinct pour l'observabilité;
- l'exécution de Prometheus, Blackbox Exporter et Grafana dans cet environnement;
- la configuration des endpoints `/health` des microservices comme cibles de supervision;
- la validation régulière de la connectivité réseau entre l'environnement d'observabilité et les VM/LXC applicatives.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-08.
- Décision liée aux objectifs d'observabilité du cahier de charge.
- Évolution prévue: ajouter des métriques applicatives `/metrics` et, plus tard, des traces distribuées.
