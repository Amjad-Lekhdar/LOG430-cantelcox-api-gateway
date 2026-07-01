# 03. Contexte et portée du système

## 3.1 Contexte métier

CanTelcoX est une plateforme télécom découpée en services spécialisés.
Le gateway sert d'entrée commune pour les clients et délègue les traitements aux services responsables de chaque domaine.
Le découpage tient compte des capacités typiques d'un BSS moderne: gestion client, catalogue produit, gestion des commandes, provisioning, médiation, rating, facturation, paiement, self-care, fraude et revenue assurance.

![Diagramme de contexte métier CanTelcoX API Gateway](../diagrams/plantuml/contexte-metier-3-1.svg)

| Partenaire | Direction | Protocole / format | Description |
| --- | --- | --- | --- |
| Frontend Expo | in | HTTP / JSON | Client utilisateur principal. |
| Clients externes | in | HTTP / JSON | Consommateurs API potentiels. |
| `identity-service` | out | HTTP / JSON | Gestion des utilisateurs et de l'authentification. |
| `order-service` | out | HTTP / JSON | Gestion des commandes. |
| `line-service` | out | HTTP / JSON | Gestion des lignes, SIM/SUPI, activations et état réseau. |
| `catalog-service` | out | HTTP / JSON | Gestion du catalogue. |
| `customers-service` | out | HTTP / JSON | Domaine clients prévu, URL à configurer. |
| `billing-service` | out | HTTP / JSON | Domaine facturation prévu, URL à configurer. |
| `audit-service` | out | HTTP / JSON | Domaine audit prévu, URL à configurer. |
| free5GC core | out | API / configuration réseau 5G | Coeur 5G de laboratoire consommé par l'adapter d'activation de `line-service`. |
| UERANSIM gNB/UE | out | Simulation 5G | Accès radio et terminal simulés pour valider l'attachement réseau. |
| Observability | in | Prometheus / Grafana / Blackbox Exporter | Supervision des endpoints de santé. |

## 3.2 Contexte technique

Le gateway expose les routes publiques sous `/v1`.
Il construit une URL amont à partir du service demandé, du chemin restant et des paramètres de requête.
Les headers HTTP hop-by-hop sont filtrés pour éviter de transmettre des informations propres à une connexion intermédiaire.
Les contrats REST internes peuvent s'inspirer des TM Forum Open APIs, notamment TMF620 pour le catalogue, TMF622 pour les commandes, TMF629 pour la gestion client, TMF635 pour l'usage, TMF678 pour les factures, TMF676 pour les paiements et TMF688 pour les événements inter-domaines.

| Variable | Usage |
| --- | --- |
| `IDENTITY_SERVICE_URL` | Cible des routes `/v1/users/*` et `/v1/auth/*` |
| `ORDER_SERVICE_URL` | Cible des routes `/v1/orders/*` |
| `LINE_SERVICE_URL` | Cible des routes `/v1/lines/*` |
| `CATALOG_SERVICE_URL` | Cible des routes `/v1/catalog/*` |
| `CUSTOMERS_SERVICE_URL` | Cible des routes `/v1/customers/*` |
| `BILLING_SERVICE_URL` | Cible des routes `/v1/billing/*` |
| `AUDIT_SERVICE_URL` | Cible des routes `/v1/audit/*` |

## 3.3 Frontières

Le gateway est responsable du routage et des erreurs de disponibilité amont.
Il n'est pas responsable de la persistance métier, de l'authentification interne détaillée ni des règles métier des services routés.
Il ne pilote pas directement free5GC: le coeur 5G reste derrière l'adapter d'activation de `line-service`.

## 3.4 Carte des contextes

```text
Clients & Identité
  -> Commandes & Activations : client authentifié / profil vérifié
Catalogue & Offres
  -> Commandes & Activations : offres, forfaits, règles d'éligibilité
Commandes & Activations
  -> Lignes & Services : demande d'activation
Lignes & Services
  -> free5GC : provisionnement abonné/SIM, état réseau
Commandes & Activations
  -> Usage / Facturation : commande facturable
Usage / Facturation
  -> Conformité & Audit : paiement, facture, écritures sensibles
Tous les contextes
  -> Conformité & Audit : événements d'audit
```

Les dépendances métier restent dirigées vers le contexte responsable. free5GC est une dépendance technique encapsulée par un adapter, pas un bounded context métier exposé aux clients.
