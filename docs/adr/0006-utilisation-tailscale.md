# ADR 0006 - Utilisation de Tailscale pour le réseau privé

## Statut

Accepté

## Contexte

CanTelcoX est déployé sous forme de microservices répartis sur plusieurs VM/LXC. Le gateway doit pouvoir joindre directement les services internes, comme `identity-service`, `order-service`, `catalog-service` et l'environnement d'observabilité, même lorsque ces services ne sont pas hébergés sur la même machine.

Sans mécanisme réseau privé, il faudrait exposer les services sur Internet, configurer manuellement des règles réseau plus complexes ou maintenir un VPN traditionnel. Ces options augmentent la complexité de déploiement et peuvent élargir la surface d'attaque.

Le projet utilise aussi des VM/LXC dans un contexte de laboratoire. L'équipe possède déjà une expérience récente avec ces environnements et a besoin d'un accès direct aux machines à tout moment pour tester, diagnostiquer et superviser les services.

## Décision

Utiliser Tailscale pour relier les VM/LXC du laboratoire dans un réseau privé appelé Tailnet.

Chaque machine reçoit une adresse Tailnet stable, utilisée dans les variables d'environnement du gateway:

- `IDENTITY_SERVICE_URL`
- `ORDER_SERVICE_URL`
- `CATALOG_SERVICE_URL`
- `CUSTOMERS_SERVICE_URL`
- `BILLING_SERVICE_URL`
- `AUDIT_SERVICE_URL`

Le gateway utilise ces adresses pour router les requêtes vers les services amont sans exposer directement les services internes sur Internet.

## Conséquences

- Les services internes restent accessibles à travers un réseau privé plutôt que par exposition publique directe.
- Les communications entre machines passent par un réseau chiffré basé sur WireGuard.
- L'accès aux machines peut être limité aux appareils et utilisateurs autorisés du Tailnet.
- Les adresses Tailnet simplifient la configuration du gateway et des outils d'observabilité.
- Le déploiement dépend de la disponibilité de Tailscale et de la bonne configuration des accès.
- Les règles de sécurité applicatives restent nécessaires: Tailscale ne remplace pas l'authentification, l'autorisation, les logs d'audit ni la gestion des secrets.

## Conformité

La conformité à cette décision est vérifiée par:

- la présence des services sur le Tailnet;
- l'utilisation des adresses Tailnet dans `.env`;
- la capacité du gateway à joindre les endpoints `/health` des services amont;
- l'absence d'exposition publique inutile des ports internes;
- la limitation des accès Tailscale aux utilisateurs et appareils autorisés.

## Notes

- Auteur: Équipe LOG430.
- Date: 2026-06-08.
- Cette décision complète l'ADR 0005 sur l'observabilité dédiée.
- Le choix est motivé par la familiarité de l'équipe avec Tailscale, par le besoin d'accès direct aux VM/LXC et par la réduction de l'exposition réseau des services internes.
