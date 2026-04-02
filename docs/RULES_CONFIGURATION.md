# Configuration Des Règles

## Objectif du document

Ce document explique comment organiser la configuration des règles dans le
projet ContentCreaEvaluator.

L'objectif est de rendre la structure claire pour l'équipe dès maintenant, même
si les règles métier détaillées ne sont pas encore toutes figées.

Ce document couvre :

- la logique de séparation des fichiers YAML
- les profils
- les fichiers de règles par mini-judge
- les fichiers partagés
- des exemples concrets de structure YAML

Ce document ne fige pas encore :

- les seuils métier définitifs
- les messages finaux côté produit
- les inputs et outputs détaillés de chaque mini-judge

## Pourquoi utiliser des fichiers YAML

Les règles sont de bonnes candidates pour de la configuration YAML parce que :

- elles restent lisibles par l'équipe
- elles sont faciles à versionner dans Git
- elles séparent le paramétrage de l'implémentation
- elles sont plus simples à relire en atelier produit ou métier

Le principe important est :

- YAML décrit
- le code exécute

Le YAML ne doit pas devenir un mini moteur métier caché.

## Arborescence recommandée

```text
src/contentcreajudge/rules/
  profiles/
    default.yaml
    blog.yaml
    landing_page.yaml
  judges/
    structure.yaml
    length.yaml
    typography.yaml
    evergreen.yaml
    cta.yaml
    sources.yaml
    seo.yaml
  shared/
    statuses.yaml
    severities.yaml
    criticality.yaml
```

## Vue d'ensemble

La séparation recommandée est la suivante :

- `profiles/`
  - définit quels judges sont actifs, avec quels poids et quelle criticité
- `judges/`
  - définit les paramètres d'un judge donné
- `shared/`
  - définit le vocabulaire commun de configuration

## Comprendre simplement un `profile`

Un `profile`, c'est le contexte global d'évaluation.

Il répond à la question :

- dans quel cadre on évalue ce contenu ?

Exemples de contexte :

- article de blog
- landing page
- newsletter
- profil par défaut

Le `profile` ne décrit pas comment un mini-judge fonctionne en détail.
Il décrit plutôt comment plusieurs mini-judges doivent être utilisés ensemble.

En pratique, un `profile` permet de dire :

- quels mini-judges sont activés
- lesquels sont plus importants que d'autres
- lesquels peuvent être bloquants
- quels paramètres par défaut s'appliquent au contexte

## Différence simple entre `profile` et `judge`

- un `judge` décrit comment contrôler une dimension
- un `profile` décrit dans quel cadre on utilise les judges

## Image mentale simple

- les `judges` sont les instruments
- le `profile` est la manière d'organiser l'orchestre

## Exemple très simple

Le judge `length` décrit par exemple :

- qu'il existe une règle de longueur minimale
- qu'il existe une règle de longueur maximale
- quels paramètres de configuration il utilise

Le profile `blog` décrit par exemple :

- qu'on active `length`
- qu'on active `seo`
- qu'on active `sources`
- que `sources` peut être bloquant
- que `length` a un certain poids dans l'évaluation globale

Donc :

- le `judge` dit comment vérifier
- le `profile` dit quand et comment l'utiliser dans l'ensemble

## Mini schéma

```text
Judge = logique d'une dimension
Profile = combinaison et importance des dimensions
```

## Exemple de comparaison

```text
Judge "length"
  -> vérifie la longueur d'un contenu

Profile "blog"
  -> utilise length + structure + seo + sources

Profile "landing_page"
  -> utilise structure + cta + seo
```

Le même mini-judge peut donc être utilisé dans plusieurs profils différents.

## 1. Les profils

## Rôle

Un profil décrit la manière dont une évaluation doit être assemblée.

Un profil ne décrit pas toute la logique d'un judge. Il dit plutôt :

- quels judges sont actifs
- quel est leur poids relatif
- quelle est leur criticité
- quels paramètres de contexte s'appliquent

## Exemples de profils

- `default`
- `blog`
- `landing_page`
- `newsletter`

## Exemple de structure YAML pour un profil

```yaml
profile_id: default
version: 1
label: "Profil par défaut"

enabled_judges:
  - structure
  - length
  - typography
  - evergreen
  - cta
  - sources
  - seo

weights:
  structure: 0.20
  length: 0.15
  typography: 0.10
  evergreen: 0.15
  cta: 0.10
  sources: 0.15
  seo: 0.15

criticality:
  structure: major
  length: major
  typography: minor
  evergreen: major
  cta: major
  sources: blocking
  seo: minor

defaults:
  locale: en-US
  content_type: article
```

## Comment lire cet exemple

- `enabled_judges`
  - liste les dimensions actives pour ce profil
- `weights`
  - prépare la future agrégation
- `criticality`
  - indique l'importance relative des dimensions
- `defaults`
  - fixe un contexte commun si le client ne le fournit pas

## Ce qu'un profil ne doit pas contenir

- la logique détaillée du judge
- des calculs complexes
- des expressions métier exécutables

## 2. Les fichiers par judge

## Rôle

Un fichier judge décrit la configuration d'une dimension particulière.

Il contient en général :

- un identifiant
- une version
- une description
- des paramètres de configuration
- des règles nommées
- des messages configurables

## Exemple : `length.yaml`

```yaml
judge_id: length
version: 1
label: "Length judge"
description: "Vérifie la longueur globale d'un contenu."

thresholds:
  min_words: 300
  max_words: 1200

rules:
  - rule_id: length.min_words
    enabled: true
    severity: major
    threshold_ref: min_words

  - rule_id: length.max_words
    enabled: true
    severity: major
    threshold_ref: max_words

messages:
  pass: "La longueur du contenu est dans la plage attendue."
  too_short: "Le contenu est trop court."
  too_long: "Le contenu est trop long."
```

## Exemple : `structure.yaml`

```yaml
judge_id: structure
version: 1
label: "Structure judge"
description: "Vérifie la structure générale du contenu."

requirements:
  title_required: true
  intro_required: true
  min_heading_count: 2

rules:
  - rule_id: structure.title_present
    enabled: true
    severity: major

  - rule_id: structure.intro_present
    enabled: true
    severity: major

  - rule_id: structure.min_headings
    enabled: true
    severity: minor

messages:
  missing_title: "Le contenu doit inclure un titre."
  missing_intro: "Le contenu doit inclure une introduction."
  insufficient_headings: "Le contenu ne contient pas assez d'intertitres."
```

## Exemple : `seo.yaml`

```yaml
judge_id: seo
version: 1
label: "SEO judge"
description: "Vérifie la présence de mots-clés et quelques contraintes SEO de base."

parameters:
  keyword_match_mode: contains
  require_all_keywords: false
  case_sensitive: false

rules:
  - rule_id: seo.keyword_presence
    enabled: true
    severity: major

messages:
  pass: "Les mots-clés requis sont présents."
  missing_keywords: "Certains mots-clés attendus sont absents."
```

## Comment lire ces exemples

Les exemples montrent une structure stable, pas des valeurs définitives.

Ce qu'il faut retenir :

- chaque fichier judge est autonome
- chaque règle a un `rule_id`
- les paramètres restent lisibles
- les messages restent séparés des calculs

## 3. Les fichiers partagés

## Rôle

Les fichiers partagés évitent de répéter la même sémantique partout.

Ils servent à centraliser :

- les statuts
- les niveaux de sévérité
- la criticité

## Exemple : `statuses.yaml`

```yaml
statuses:
  - pass
  - warn
  - fail
  - unknown
  - not_applicable
```

## Exemple : `severities.yaml`

```yaml
severities:
  - info
  - minor
  - major
  - critical
```

## Exemple : `criticality.yaml`

```yaml
criticality_levels:
  - minor
  - major
  - blocking
```

## Pourquoi c'est utile

- cohérence entre profils et judges
- validation plus simple
- vocabulaire stable à travers tout le projet

## 4. Différence entre profil et judge

La confusion la plus fréquente est ici :

- un profil ne remplace pas un judge
- un judge ne remplace pas un profil

## Résumé simple

- le profil décide du cadre global
- le judge décrit les paramètres de sa propre dimension

## Exemple concret

Le profil `blog` peut dire :

- active `length`
- donne à `length` un poids de `0.15`
- considère `length` comme `major`

Le fichier `length.yaml` dit :

- le judge `length` existe
- il a une version
- il utilise `min_words`
- il utilise `max_words`
- il expose ses règles nommées

## 5. Conventions recommandées

## Nommage

- utiliser des ids stables
- utiliser des noms courts et prévisibles
- éviter les espaces dans les identifiants

Exemples :

- `profile_id: blog`
- `judge_id: length`
- `rule_id: length.min_words`

## Versioning

Chaque fichier doit porter sa version.

Exemple :

```yaml
version: 1
```

Cela prépare :

- la traçabilité
- les évolutions futures
- les comparaisons de règles dans le temps

## Validation

Les YAML doivent être validés côté backend au chargement.

Il faut vérifier au minimum :

- présence des champs obligatoires
- cohérence des ids
- poids valides
- références de judges valides dans les profils
- criticité autorisée

## 6. Ce qu'il ne faut pas faire

Pour garder une architecture saine, il faut éviter :

- mettre du calcul dans les YAML
- multiplier les structures différentes selon les judges sans raison
- dupliquer les mêmes niveaux de sévérité dans plusieurs fichiers
- laisser des ids instables ou ambigus

## Mauvaise approche

```yaml
rule_logic: "if word_count > 300 and title_present then pass"
```

Ce type de logique ne doit pas vivre dans les fichiers de config.

## Bonne approche

```yaml
thresholds:
  min_words: 300

rules:
  - rule_id: length.min_words
    enabled: true
```

Le YAML décrit le paramétrage. Le code décide comment l'utiliser.

## 7. Recommandation d'équipe

Pour que ce soit clair pour tout le monde, je recommande ce découpage :

- un développeur ou binôme définit la convention de chargement des YAML
- un développeur ou binôme prépare les profils
- les développeurs backend branchent ensuite les mini-judges sur cette structure
- la UI consomme les résultats mais ne dépend jamais directement des YAML

## 8. Ce qu'on peut figer maintenant

On peut figer dès aujourd'hui :

- l'arborescence `profiles / judges / shared`
- la présence d'un `version`
- la présence d'ids stables
- la distinction profil vs judge
- l'usage de YAML comme couche de configuration

On n'a pas besoin de figer maintenant :

- toutes les clés finales de chaque judge
- tous les seuils exacts
- tous les messages finaux

## Conclusion

Le but n'est pas encore d'avoir les bonnes règles métier partout. Le but est
d'avoir une structure de configuration simple, cohérente et partageable.

Si l'équipe suit cette organisation :

- les fichiers resteront lisibles
- les règles seront versionnables
- les mini-judges pourront évoluer indépendamment
- l'architecture restera claire même quand le nombre de règles augmentera
