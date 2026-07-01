# 04. Stratégie de solution

## 4.1 Décisions structurantes

| Sujet | Stratégie |
| --- | --- |
| Style architectural | API Gateway devant des microservices par domaine. |
| Stack technologique | Expo, TypeScript, Python, FastAPI, PostgreSQL, Docker Compose, variables d'environnement. |
| Réseau interne | Tailscale/Tailnet pour relier le gateway, les VM/LXC applicatives, free5GC et l'environnement d'observabilité. |
| Qualité atteinte par | Configuration explicite, endpoints `/health`, `/routes`, `/metrics`, erreurs `502`/`503`. |
| Intégration 5G | Encapsuler free5GC derrière un adapter d'activation plutôt que l'exposer au gateway public. |
| Observabilité | Superviser les endpoints `/health` depuis un environnement dédié et exposer les métriques gateway. |
| Organisation | Documentation arc42, décisions ADR, services déployables indépendamment. |

## 4.2 Approche retenue

Le gateway utilise une table de routage en mémoire qui associe un segment de route `/v1/{service}` à une URL de service amont.
Cette approche est simple, explicite et adaptée au MVP.

Les services déjà disponibles sont renseignés dans `.env`.
Les services non encore créés disposent de variables dédiées laissées vides; le gateway retourne alors une réponse `503` claire lorsque la route est appelée.
Le coeur free5GC est traité comme système technique voisin: `line-service` l'appelle pour provisionner la ligne, tandis que `order-service` se limite à créer la commande et demander l'activation.

## 4.3 Avantages

- Les clients utilisent une seule base URL.
- Les services peuvent changer d'adresse sans modifier le frontend.
- Les services existants sur VM/LXC peuvent être consommés sans être reconstruits dans ce dépôt.
- La documentation des routes est visible via `/routes`.
- L'intégration free5GC reste remplaçable ou simulable par adapter.

## 4.4 Limites acceptées

- Le routage est statique au démarrage de l'application.
- Il n'y a pas encore de découverte automatique de services.
- Il n'y a pas encore de mécanisme commun d'authentification, de rate limiting ou de circuit breaker dans le gateway.
- Le gateway ne gère pas de transaction distribuée; l'idempotence, l'exactly-once et l'audit sont portés par les services métier.
