# ADR 0007 - Choix du frontend Expo React Native Web

## Statut

Accepté

## Contexte

CanTelcoX doit offrir un parcours client démontrable pour créer un compte, se connecter, sélectionner un canal MFA, consulter le catalogue, commander un forfait et afficher la facture ou l'historique.

Le frontend doit rester simple à lancer en laboratoire, fonctionner dans un navigateur pendant les démonstrations et rester compatible avec un usage mobile. Il doit consommer le BSS via l'API Gateway, sans connaître les adresses internes des microservices.

Le dépôt frontend existant utilise Expo, React Native, React Native Web et TypeScript. Les scripts disponibles permettent de lancer la même application en web, Android ou iOS.

## Forces de décision

- Fournir une interface client rapidement démontrable.
- Garder une base de code unique pour web et mobile.
- Réduire la configuration locale pour les démonstrations.
- Valider le parcours bout-en-bout via l'API Gateway.
- Éviter que le frontend dépende directement des URLs Tailnet des services internes.
- Rester compatible avec Node.js, npm et les outils Expo déjà utilisés par l'équipe.

## Options considérées

| Option | Exemple | Avantages | Inconvénients |
| --- | --- | --- | --- |
| Application web React classique | Vite ou Next.js consommant le gateway depuis le navigateur | Très adaptée au web, écosystème riche, build simple | Ne couvre pas naturellement le besoin mobile sans autre application |
| Application mobile native séparée | Android Kotlin ou iOS Swift dédié au parcours client | Expérience mobile native complète | Coût élevé, deux bases de code possibles, démonstration web moins directe |
| Expo React Native Web | Une application Expo pouvant tourner avec `npm run web`, `npm run android` ou `npm run ios` | Base de code unique, démonstration web rapide, compatible mobile, TypeScript | Dépend d'Expo et demande une attention aux différences web/mobile |
| Interface minimale Swagger/Postman seulement | Démonstration des endpoints via `/docs` ou collections HTTP | Très simple pour tester l'API | Ne démontre pas un parcours client réaliste |

## Décision

Utiliser Expo avec React Native Web et TypeScript pour le frontend client CanTelcoX.

Le frontend:

- appelle uniquement l'API Gateway configurée par `EXPO_PUBLIC_API_BASE_URL`;
- ne connaît pas les adresses Tailnet des microservices;
- centralise les appels HTTP dans `src/api/client.ts`;
- utilise TypeScript pour typer les payloads et réponses API;
- peut être lancé en web avec `npm run web` pour les démonstrations;
- conserve la possibilité d'un lancement mobile avec Expo Android ou iOS.

## Conséquences

- Une seule interface permet de démontrer le parcours client principal.
- Les changements d'adresse des services restent absorbés par le gateway et sa configuration.
- Le frontend doit gérer les variations de contrats API dans son client HTTP, par exemple la normalisation des réponses catalogue ou facturation.
- Les scénarios mobiles restent possibles, mais doivent être testés séparément des scénarios web.
- Les contraintes CORS se concentrent sur le couple navigateur/gateway plutôt que sur chaque microservice.
- L'application frontend ne doit pas contenir de logique métier critique; les invariants restent dans les services backend.

## Conformité

Cette décision répond aux besoins du projet sur:

- la démonstration d'un scénario bout-en-bout utilisateur;
- l'accès REST via API Gateway;
- la séparation entre frontend public et services internes;
- la maintenabilité d'un client typé;
- la capacité de présenter le système en laboratoire depuis un navigateur.

La conformité est vérifiée par:

- la configuration `EXPO_PUBLIC_API_BASE_URL`;
- l'absence d'appels directs aux URLs Tailnet dans le frontend;
- le client HTTP `src/api/client.ts`;
- le script `npm run typecheck`;
- les démonstrations du parcours inscription, authentification, commande et facturation via le gateway.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-28.
- Cette décision complète l'ADR 0002 sur l'API Gateway comme point d'entrée HTTP unique.
