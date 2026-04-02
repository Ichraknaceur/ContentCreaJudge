# Cadrage Équipe

## Objectif du document

Ce document fixe un cadre de travail clair pour l'équipe sur la phase actuelle
du projet ContentCreaEvaluator.

L'objectif n'est pas de définir les règles métier détaillées de chaque
mini-judge aujourd'hui. L'objectif est de donner à l'équipe :

- une architecture projet lisible
- une architecture UI cohérente
- une répartition claire des responsabilités
- une roadmap de mise en oeuvre par lots

Ce document est volontairement centré sur la structure, l'organisation et les
interfaces de collaboration entre modules.

## Objectif de la phase actuelle

La mission actuelle est de livrer une base de travail suffisamment claire pour
que plusieurs développeurs puissent avancer en parallèle sans ambiguïté.

Cette phase couvre :

- le socle backend FastAPI
- la structure du futur moteur d'évaluation
- la surface de démonstration Streamlit
- le découpage modulaire du projet
- la préparation des futures briques mini-judges

Cette phase ne couvre pas encore :

- la logique métier complète des mini-judges
- les règles détaillées par dimension
- les formats métier finaux de tous les inputs et outputs de judges
- l'algorithme final d'agrégation

## Vision d'ensemble

Le système doit être compris comme deux surfaces reliées :

```text
UI Streamlit
    ->
API FastAPI
    ->
Orchestration d'évaluation
    ->
Préprocessing
    ->
Mini-judges
    ->
Agrégation
```

Aujourd'hui, seule une partie de ce flux est réellement implémentée. Le reste
doit être préparé proprement pour permettre une montée en puissance progressive.

## Architecture projet

## Principe général

Le projet est organisé en couches simples :

- une couche d'entrée API
- une couche d'orchestration applicative
- une couche de domaine
- une couche de règles/configuration
- une couche de mini-judges
- une couche UI

L'idée centrale est la suivante :

- l'API expose
- l'application orchestre
- le domaine définit le vocabulaire
- les judges exécutent des contrôles spécialisés
- l'agrégation combine les résultats
- la UI consomme l'API comme un vrai client

## Arborescence cible

```text
src/contentcreajudge/
  api/
    app.py
    root.py
    health.py
    evaluations.py
    judges/
  application/
    evaluation_flow/
    judge_flow/
  domain/
    evaluation/
    judge/
    rules/
    shared/
  preprocessing/
  judges/
    structure/
    length/
    typography/
    evergreen/
    cta/
    sources/
    seo/
  aggregation/
  rules/
    profiles/
    judges/
    shared/
  adapters/
    sources/
  ui/
    app.py
    pages/
    components/
    services/
    viewmodels/
    theme/
  observability/
```

## Règles d'organisation

- Pas de logique métier directement dans `api/`
- Pas de logique de présentation dans `application/`
- Pas de dépendance UI dans `domain/`
- Pas d'agrégation dans les mini-judges
- Pas de logique métier dans les fichiers de configuration

## Architecture backend

## Couche API

La couche API expose le système au monde extérieur.

Responsabilités :

- exposer les endpoints HTTP
- valider les payloads transport
- normaliser les réponses
- gérer les erreurs HTTP

Endpoints déjà présents :

- `GET /`
- `GET /health`
- `POST /api/v1/evaluations`

Évolution prévue :

- endpoints dédiés aux mini-judges
- endpoints de découverte de profils et de judges

## Couche application

La couche application orchestre les cas d'usage.

Responsabilités :

- lancer une évaluation globale
- lancer un mini-judge isolé
- coordonner preprocessing, judge, agrégation
- garantir l'ordre et la cohérence du flux

Cette couche ne doit pas contenir la logique détaillée de chaque règle.

## Couche domaine

La couche domaine porte le vocabulaire commun.

Responsabilités :

- définir les concepts stables du projet
- centraliser les statuts et notions transverses
- éviter la duplication sémantique

Exemples de notions concernées :

- évaluation
- judge
- règle
- finding
- score
- statut
- criticité

## Couche preprocessing

La couche preprocessing prépare le contenu avant l'exécution des judges.

Responsabilités :

- normaliser le texte
- extraire les signaux réutilisables
- éviter de refaire le même parsing dans plusieurs judges

Cette couche est stratégique car elle limite la duplication future.

## Couche judges

La couche judges porte les contrôles spécialisés par dimension.

Responsabilités :

- un sous-module par dimension
- exécution d'un contrôle isolé
- retour d'un résultat structuré pour une dimension donnée

Les mini-judges doivent rester indépendants les uns des autres.

## Couche aggregation

La couche aggregation combine les sorties des mini-judges.

Responsabilités :

- consolider les résultats
- appliquer poids et criticité
- produire une vue globale cohérente

Cette couche ne doit pas être mélangée aux judges individuels.

## Couche rules

La couche rules contient la configuration des profils et des règles.

Responsabilités :

- profils d'évaluation
- paramètres par judge
- vocabulaire de configuration partagé

La configuration métier doit être lisible et versionnable.

## Couche adapters

La couche adapters isole les interactions externes.

Responsabilités :

- appels réseau ou intégrations futures
- encapsulation de dépendances externes

En V1, l'adapter principal pressenti est la validation des sources.

## Architecture UI

## Rôle de la UI

La UI Streamlit n'est pas un simple habillage technique. Elle a deux rôles :

- servir de surface de démonstration client
- servir d'outil de test manuel pour l'équipe

Elle doit donc être pensée comme une vraie couche produit, même si elle reste
simple techniquement.

## Principes UI

- la UI ne porte aucune logique métier
- la UI consomme uniquement l'API
- la UI doit pouvoir montrer les briques globales et les briques isolées
- la UI doit rester compréhensible en démo client

## Structure UI cible

```text
ui/
  app.py
  pages/
    overview.py
    global_evaluation.py
    judge_playground.py
    delivery.py
  components/
    status_cards.py
    judge_cards.py
    payload_panel.py
    result_panel.py
  services/
    api_client.py
  viewmodels/
    overview_vm.py
    judge_playground_vm.py
  theme/
    contentcrea_theme.py
```

## Écrans UI recommandés

### 1. Overview

Objectif :

- montrer l'état global du système
- vérifier que l'API répond
- montrer les briques déjà prêtes

Contenu :

- statut backend
- version
- endpoints exposés
- progression produit

### 2. Global Evaluation

Objectif :

- représenter le produit final
- permettre de lancer une évaluation globale

Contenu :

- saisie du contenu
- sélection du profil
- envoi du payload
- affichage du résultat global

### 3. Judge Playground

Objectif :

- tester un mini-judge isolément
- permettre une démo pédagogique
- faciliter les tests manuels de l'équipe

Contenu :

- sélection du mini-judge
- formulaire dédié
- exécution ciblée
- panneau de résultat

### 4. Delivery View

Objectif :

- montrer l'avancement du projet
- clarifier ce qui est prêt, en cours, ou à venir

Contenu :

- livré
- en cours
- prochain lot
- scope V1

## Thème UI

La UI doit rester alignée avec le langage visuel ContentCrea.

Cela implique :

- palette cohérente avec le produit de référence
- hiérarchie visuelle simple et premium
- écrans lisibles en démo
- séparation nette entre branding et zones de travail

Le thème doit être centralisé dans la couche `ui/theme/`.

## Responsabilités par module

## Backend

### `api/`

Responsabilité :

- exposition HTTP

Doit contenir :

- endpoints
- schémas transport
- mapping erreur HTTP

Ne doit pas contenir :

- règles métier
- agrégation
- parsing métier avancé

### `application/`

Responsabilité :

- orchestration des cas d'usage

Doit contenir :

- flux d'évaluation globale
- flux d'exécution d'un judge
- coordination entre couches

### `domain/`

Responsabilité :

- vocabulaire métier stable

Doit contenir :

- concepts partagés
- statuts
- notions transverses

### `preprocessing/`

Responsabilité :

- préparation du contenu

Doit contenir :

- normalisation
- extraction de signaux
- préparation de données partagées

### `judges/`

Responsabilité :

- logique spécialisée par dimension

Doit contenir :

- un sous-espace par judge
- exécution isolée par dimension

### `aggregation/`

Responsabilité :

- combinaison des résultats

Doit contenir :

- consolidation
- calcul global
- priorisation globale

### `rules/`

Responsabilité :

- configuration versionnée

Doit contenir :

- profils
- règles par judge
- paramètres partagés

### `adapters/`

Responsabilité :

- dépendances externes

Doit contenir :

- connecteurs techniques
- interactions hors coeur métier

## UI

### `ui/pages/`

Responsabilité :

- structure des écrans

### `ui/components/`

Responsabilité :

- composants visuels réutilisables

### `ui/services/`

Responsabilité :

- appels API

### `ui/viewmodels/`

Responsabilité :

- transformation des réponses API pour affichage

### `ui/theme/`

Responsabilité :

- style global
- couleurs
- conventions visuelles

## Principes de travail équipe

## Principes clés

- chaque couche a une responsabilité claire
- on évite les couplages implicites
- on documente les conventions avant de multiplier les implémentations
- on favorise les points d'entrée simples
- on garde une UI démontrable en continu

## Règles de collaboration

- ne pas contourner l'orchestration applicative
- ne pas coder des règles métier dans la UI
- ne pas dupliquer la logique d'un judge dans plusieurs endpoints
- garder les conventions de nommage stables
- mettre à jour la documentation à chaque changement structurel

## Roadmap de mise en oeuvre par lots

## Lot 0. Fondation

Objectif :

- poser les bases du projet

Contenu :

- structure du package
- docs d'architecture
- docs contrat API
- docs développeur
- endpoints socle
- UI socle

Statut :

- en grande partie déjà en place

## Lot 1. Structuration backend propre

Objectif :

- rendre l'architecture prête pour le travail parallèle

Contenu :

- affiner `api/`
- poser `application/`
- poser `domain/`
- poser `rules/`
- clarifier les conventions inter-modules

Résultat attendu :

- chaque développeur sait où intervenir

## Lot 2. Structuration UI propre

Objectif :

- sortir d'une UI monolithique

Contenu :

- découpage `pages/`
- découpage `components/`
- création d'un `api_client`
- centralisation du thème ContentCrea

Résultat attendu :

- UI plus maintenable
- évolution plus simple des écrans

## Lot 3. Préparation mini-judges

Objectif :

- préparer l'intégration des judges sans coder tout le métier

Contenu :

- conventions de nommage
- structure des endpoints dédiés
- emplacements des règles YAML
- préparation des dossiers judges

Résultat attendu :

- base prête pour brancher un premier judge réel

## Lot 4. Premier flux judge de bout en bout

Objectif :

- démontrer l'architecture sur un cas simple

Contenu :

- un premier mini-judge branché
- endpoint dédié
- affichage UI correspondant
- intégration dans l'évaluation globale

Résultat attendu :

- preuve que l'architecture fonctionne

## Lot 5. Extension progressive

Objectif :

- ajouter les autres judges sans casser la structure

Contenu :

- ajout dimension par dimension
- mise à jour agrégation
- enrichissement UI

Résultat attendu :

- croissance régulière, lisible, démontrable

## Décisions à figer maintenant

Pour débloquer l'équipe, il suffit de figer ces décisions immédiatement :

- l'architecture des couches
- l'arborescence projet
- le rôle de la UI
- la séparation entre évaluation globale et tests de mini-judges
- la place des fichiers de règles
- la roadmap par lots

Il n'est pas nécessaire aujourd'hui de figer :

- les payloads détaillés de chaque judge
- les règles métier finales
- les seuils exacts
- les formats de findings définitifs

## Conclusion

La priorité n'est pas encore l'intelligence métier du système. La priorité est
de construire un socle clair, modulaire et partageable.

Si ce cadrage est respecté, l'équipe pourra :

- travailler en parallèle
- faire évoluer la UI et le backend sans confusion
- brancher progressivement les mini-judges
- démontrer l'avancement au client à chaque étape
