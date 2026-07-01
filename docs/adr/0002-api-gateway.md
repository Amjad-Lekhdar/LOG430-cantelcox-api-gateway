# ADR 0002 - API Gateway comme point d'entrée HTTP unique

## Statut

Accepté

## Contexte

CanTelcoX expose plusieurs services métier: identité, clients, catalogue, commandes, facturation et audit. Le frontend et les clients externes ne doivent pas connaître les adresses internes de chaque service, ni gérer directement la dispersion réseau entre VM/LXC.

Le cahier de charge demande une API RESTful sécurisée, documentée, versionnée et orchestrée par une API Gateway. Le projet doit aussi permettre des démonstrations simples: consulter les routes disponibles, vérifier la santé du système, observer les métriques et comparer les appels directs aux appels via gateway.

Dans l'état actuel, le dépôt contient le gateway FastAPI. Les services métier sont joints par URLs configurables, principalement sur le Tailnet.

## Forces de décision

- Offrir une URL d'entrée unique au frontend.
- Masquer les adresses Tailnet et les ports des services internes.
- Centraliser les diagnostics techniques transversaux: `/health`, `/routes`, `/metrics`.
- Garder les règles métier dans les services responsables.
- Permettre une configuration simple par variables d'environnement.
- Préparer l'ajout progressif de sécurité, rate limiting, circuit breaker et validation de jetons.

## Options considérées

| Option | Exemple | Avantages | Inconvénients |
| --- | --- | --- | --- |
| Appels directs du frontend vers chaque service | Le frontend appelle `http://100.83.57.43:8020/v1/auth/login`, puis `http://100.95.65.46:8040/v1/catalog/plans`, puis `http://100.108.225.1:8030/v1/orders` | Simplicité initiale, moins de code gateway | Couplage fort au réseau interne, CORS multiplié, difficile à sécuriser et observer uniformément |
| API Gateway applicative légère | Le frontend appelle seulement `http://gateway/v1/...`; FastAPI relaie vers le service cible selon le premier segment de route | URL unique, routage explicite, diagnostics centralisés, adaptée au MVP | Composant supplémentaire, gestion des erreurs réseau à maintenir |
| Gateway complet de type Kong/Traefik/NGINX | Déployer Kong, Traefik ou NGINX avec routes, plugins, politiques de sécurité et métriques intégrées | Fonctionnalités avancées prêtes à l'emploi | Configuration plus lourde pour le laboratoire, moins de contrôle pédagogique sur le comportement |

## Décision

Utiliser une API Gateway applicative légère implémentée avec FastAPI.

Le gateway expose:

- `GET /health` pour la santé du gateway;
- `GET /routes` pour inspecter les routes configurées;
- `GET /metrics` pour les métriques Prometheus du gateway;
- `GET /docs` et `GET /openapi.json` pour la documentation OpenAPI;
- `/v1/*` pour relayer les appels vers les services métier.

La résolution de route repose sur le premier segment après `/v1`:

| Route publique | Service cible |
| --- | --- |
| `/v1/users/*` | `identity-service` |
| `/v1/auth/*` | `identity-service` |
| `/v1/orders/*` | `order-service` |
| `/v1/catalog/*` | `catalog-service` |
| `/v1/customers/*` | `customers-service` |
| `/v1/billing/*` | `billing-service` |
| `/v1/audit/*` | `audit-service` |

Les URLs amont sont chargées depuis les variables `*_SERVICE_URL`. Le gateway conserve la méthode HTTP, le chemin, le corps, les paramètres de requête et les headers applicatifs. Les headers hop-by-hop sont filtrés.

Le gateway normalise les erreurs techniques suivantes:

| Cas | Réponse |
| --- | --- |
| Famille de route inconnue | `404` |
| Famille de route connue mais URL absente | `503` |
| Service amont inaccessible | `502` |
| Erreur retournée par l'amont | Statut et contenu de l'amont |

## Conséquences

- Le frontend utilise une seule base URL pour accéder au BSS.
- Les services internes peuvent changer d'adresse sans modifier le frontend.
- Le gateway devient un point d'observation naturel pour le trafic entrant, la latence et les erreurs.
- Le gateway ne doit pas accumuler de logique métier; les invariants restent dans les services.
- Le routage est statique au démarrage: une modification d'URL exige un redémarrage.
- Les fonctionnalités avancées restent à ajouter ou documenter: authentification centralisée, validation JWT, MFA applicatif, rate limiting, circuit breaker et stratégie de versionnement plus stricte.

## Conformité

Cette décision répond aux exigences du cahier de charge relatives à:

- l'exposition RESTful versionnée;
- l'orchestration via API Gateway;
- la documentation OpenAPI/Swagger;
- la gestion d'erreurs normalisée;
- l'observabilité par métriques et santé applicative.

La conformité est vérifiée par:

- les endpoints `/health`, `/routes`, `/metrics`, `/docs` et `/openapi.json`;
- les tests automatisés du gateway;
- la documentation README et Arc42;
- les campagnes de charge comparant appels directs et appels via gateway.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-23.
- Cette décision complète l'ADR 0001 sur le style microservices et l'ADR 0006 sur le réseau privé Tailscale.
