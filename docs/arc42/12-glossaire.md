# 12. Glossaire

| Terme | Définition |
| --- | --- |
| API Gateway | Service d'entrée qui reçoit les requêtes clientes et les route vers les microservices internes. |
| ADR | Architecture Decision Record, document court qui explique une décision d'architecture. |
| Adapter | Composant d'infrastructure qui relie un port applicatif à une technologie externe. |
| arc42 | Gabarit de documentation d'architecture logicielle. |
| BSS | Business Support System, domaine télécom couvrant notamment catalogue, clients, facturation et audit. |
| Blackbox Exporter | Composant Prometheus qui sonde des endpoints externes, par exemple `/health`. |
| Bounded context | Frontière logique d'un sous-domaine métier. |
| DNN | Data Network Name, nom de réseau de données utilisé dans une session 5G. |
| FastAPI | Framework Python utilisé pour exposer l'API HTTP du gateway. |
| free5GC | Coeur réseau 5G open source utilisé en laboratoire pour valider le provisioning et l'attachement réseau. |
| Idempotency-Key | Clé applicative permettant de rejouer une opération sans produire de doublon métier. |
| LXC | Technologie de conteneurisation système utilisée comme option d'hébergement laboratoire. |
| Microservice | Service autonome responsable d'un domaine fonctionnel précis. |
| MSISDN | Numéro d'appel mobile associé à une ligne. |
| Port | Interface applicative qui décrit un besoin d'entrée ou de sortie sans imposer une technologie. |
| SUPI | Identifiant permanent d'abonné 5G provisionné dans le coeur réseau. |
| Tailnet | Réseau privé Tailscale reliant les VM/LXC du laboratoire. |
| UERANSIM | Simulateur gNB/UE utilisé pour tester l'accès radio 5G avec free5GC. |
| URL amont | URL du service cible vers lequel le gateway proxifie une requête. |
| VM | Machine virtuelle utilisée pour héberger certains services. |
