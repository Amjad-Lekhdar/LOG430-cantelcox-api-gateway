# 04. Strategie de solution

## Décisions structurantes

| Sujet | Stratégie |
| --- | --- |
| Point d'entrée | Utiliser un API Gateway unique pour le frontend et les clients externes. |
| Découpage | Router vers des services par domaine métier. |
| Déploiement | Construire le gateway localement et joindre les services amont via URLs configurées. |
| Configuration | Séparer le code et les adresses réseau avec des variables d'environnement. |
| Observabilité | Superviser les endpoints `/health` depuis un environnement dédié. |
| Évolution | Préparer les routes des services futurs sans bloquer le gateway existant. |

## Approche retenue

Le gateway utilise une table de routage en mémoire qui associe un segment de route `/v1/{service}` à une URL de service amont.
Cette approche est simple, explicite et adaptée au MVP.

Les services déjà disponibles sont renseignés dans `.env`.
Les services non encore créés disposent de variables dédiées laissées vides; le gateway retourne alors une réponse `503` claire lorsque la route est appelée.

## Avantages

- Les clients utilisent une seule base URL.
- Les services peuvent changer d'adresse sans modifier le frontend.
- Les services existants sur VM/LXC peuvent être consommés sans être reconstruits dans ce dépôt.
- La documentation des routes est visible via `/routes`.

## Limites acceptées

- Le routage est statique au démarrage de l'application.
- Il n'y a pas encore de découverte automatique de services.
- Il n'y a pas encore de mécanisme commun d'authentification, de rate limiting ou de circuit breaker dans le gateway.
