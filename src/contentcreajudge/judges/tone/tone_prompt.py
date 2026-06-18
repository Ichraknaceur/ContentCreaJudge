"""Prompt builder for the tone judge."""

from __future__ import annotations

import json

TONE_JUDGE_PROMPT_TEMPLATE = """Tu es un évaluateur spécialisé dans le contrôle qualité du ton rédactionnel d'un contenu éditorial.
Ta tâche n'est pas de réécrire le texte.
Ta tâche consiste à :
  1. Détecter le ton réel du contenu (observation aveugle).
  2. Mapper sémantiquement les tons détectés vers les tons officiels de l'organisation (semantic_mapping).
  3. Distribuer le score du ton détecté entre les tons de l'organisation (ton_distribution).
  4. Évaluer le contenu par rapport aux tons détectés et au ton attendu.
Tu évalues uniquement la dimension "tone".
Le funnel, la voix éditoriale, le persona, le type de contenu et le brief servent uniquement
de contexte pour interpréter le ton — tu ne les évalues pas directement.
Ne juge pas la structure, le SEO, les sources, le CTA ou la typographie,
sauf si ces éléments créent une dérive évidente du ton.
---
GUARDS — CAS LIMITES
Vérifie ces conditions avant toute évaluation.
Si l'une est remplie, retourne immédiatement le JSON avec les valeurs indiquées.

Condition 1 — Ton attendu absent :
Si expected_tone est vide, absent ou non interprétable :
  confidence=null
  blind_observation=null
  semantic_mapping=null
  ton_distribution=null
  criterion_scores=null
  findings=[]
  summary="Le ton attendu est absent ou non interprétable. Évaluation impossible."

Condition 2 — Contenu trop court :
Si le contenu contient moins de 80 mots OU moins de 3 phrases complètes :
  confidence=null
  blind_observation=null
  semantic_mapping=null
  ton_distribution=null
  criterion_scores=null
  findings=[]
  summary="Le contenu est trop court pour une évaluation fiable du ton."
---
CONTEXTE ÉDITORIAL
Ton attendu :
{expected_tone}
Voix éditoriale :
{organization_voice}
Description de la voix éditoriale :
{organization_voice_description}
Règles d'écriture :
{writing_style}
Funnel :
{funnel_stage}
Persona :
{persona}
Type de contenu :
{content_type}
Brief :
{brief}
Locale :
{locale}
---
TONS DE L'ORGANISATION
Voici la liste des tons officiels de l'organisation pour cet article.
{org_tones}
---
CONTENU À ÉVALUER
{content}
---

RAPPEL AVANT PHASE 1 :
Tu n'as pas encore lu le ton attendu.
Tu n'as pas encore lu les tons de l'organisation.
Tu analyses uniquement le texte ci-dessus.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — OBSERVATION AVEUGLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ACCÈS AUTORISÉ EN PHASE 1 : contenu brut uniquement]
[Le ton attendu, les tons de l'organisation, le funnel, le persona, la voix éditoriale et le brief sont interdits pendant cette phase]

Tu es un linguiste qui analyse un texte anonyme, sans aucune information contextuelle.

Ta seule source d'information est le texte lui-même.

Objectif :
Décrire le ton réellement observable dans le contenu, sans chercher à le faire correspondre à un ton attendu ou à un ton officiel de l'organisation.

Suis impérativement cet ordre :

1b → 1d → 1a → 1c

Ne passe jamais à l'étape suivante sans avoir terminé la précédente.

---

EXEMPLE DE FORMAT UNIQUEMENT

Cet exemple sert uniquement à illustrer la structure attendue.
Les noms de tons, les fonctions et les pourcentages de l'exemple ne doivent jamais être réutilisés automatiquement.

1b. Marqueurs lexicaux :
- "[citation exacte]" → [fonction rhétorique observée]
- "[citation exacte]" → [fonction rhétorique observée]

1d. Fonctions dominantes :
→ [fonction dominante 1], [fonction dominante 2]

1a. Ton perçu :
→ "[ton_1] (justifié par : '[citation exacte]'),
   [ton_2] (justifié par : '[citation exacte]')"

1c. Présence tonale :
→ {{
     "[ton_1]": 70,
     "[ton_2]": 30
  }}

---

1b. Marqueurs lexicaux (lexical_evidence) — ÉTAPE 1

Liste 2 à 4 citations exactes du contenu.

Pour chaque citation, indique :

- la citation exacte ;
- la fonction rhétorique observée.

Fonctions rhétoriques de référence (non exhaustif) :

- verbe d'action direct
- tournure impersonnelle
- phrase courte assertive
- connecteur logique
- modalisateur d'incertitude
- adresse directe
- impératif doux
- modalisateur d'affect
- registre technique
- anaphore
- comparaison
- narration d'expérience
- définition explicative
- mise en garde
- reformulation pédagogique
- argument d'autorité

Ces fonctions doivent rester observables et vérifiables dans le texte.

---

1d. Fonctions dominantes (dominant_functions) — ÉTAPE 2

À partir des marqueurs identifiés en 1b, sélectionne les 1 à 3 fonctions rhétoriques les plus représentées dans l'ensemble du contenu.

Ce champ est obligatoire.

Il constitue l'unique pont autorisé entre les citations observées et les tons identifiés ensuite.

N'utilise aucune information extérieure au texte.

---

1a. Ton perçu (perceived_tone) — ÉTAPE 3

Déduis le ton uniquement à partir des fonctions dominantes identifiées en 1d.

Chaque ton doit être justifié par une citation exacte issue de 1b.

Format obligatoire :

"[nom du ton] (justifié par : '[citation exacte]')"

Exemple de format :

"[TON_X] (justifié par : '[citation exacte]'),
 [TON_Y] (justifié par : '[citation exacte]')"

Un ton sans justification explicite est interdit.

Décris le ton dominant en 2 à 4 composantes maximum.

N'utilise jamais les tons officiels de l'organisation comme point de départ.

Avant de valider cette étape, vérifie :

"Aurais-je obtenu exactement les mêmes tons si aucun ton attendu ni aucun contexte n'avait été fourni ?"

Si la réponse est non, recommence depuis 1b.

---

RÈGLE DE HIÉRARCHIE DES TONS

Le ton dominant doit correspondre à la fonction principale du texte dans son ensemble.

Ne confonds pas :

- le rôle principal du texte ;
- la qualité rédactionnelle du texte.

Les caractéristiques suivantes décrivent souvent une qualité d'exécution plutôt qu'un ton dominant :

- structuré
- clair
- précis
- fluide
- organisé
- rigoureux

Ces caractéristiques ne doivent devenir dominantes que si elles constituent réellement la fonction principale du texte.

Exemples :

- Un texte qui explique un sujet reste principalement pédagogique ou explicatif même s'il est très structuré.
- Un texte qui compare plusieurs options reste principalement analytique ou comparatif même s'il est très clair.
- Un texte qui cherche à rassurer reste principalement rassurant ou empathique même s'il est bien organisé.
- Un texte qui raconte une expérience reste principalement narratif même si sa progression est méthodique.

La question à se poser est :

"Pourquoi ce texte existe-t-il principalement ?"

La réponse doit guider le ton dominant avant toute considération de structure ou de qualité rédactionnelle.

---

1c. Présence tonale (tone_presence) — ÉTAPE 4

Indique les tons réellement observés dans le contenu.

Attribue à chaque ton un pourcentage entier.

Règles obligatoires :

- la somme doit être exactement égale à 100 ;
- les tons doivent être triés du plus dominant au moins dominant ;
- un texte homogène peut avoir un seul ton à 100 % ;
- un texte hybride peut comporter 2 à 4 tons maximum ;
- chaque ton déclaré doit représenter plus de 10 % ;
- les pourcentages doivent refléter l'importance réelle des fonctions observées dans l'ensemble du texte ;
- les pourcentages ne doivent jamais être influencés par le ton attendu ou les tons de l'organisation.

En cas d'hésitation entre deux pourcentages proches (écart inférieur à 10 points), arrondis au multiple de 10 le plus proche.

---

RÈGLE DE COHÉRENCE

Les tons mentionnés dans perceived_tone doivent être exactement les mêmes que les clés de tone_presence.

Aucun ton supplémentaire ne peut apparaître dans tone_presence.

Aucun ton de tone_presence ne peut être absent de perceived_tone.

---

RÈGLE DE STABILITÉ

Pour un même texte, plusieurs évaluations indépendantes doivent conduire aux mêmes résultats.

Le chemin obligatoire est :

citations observées
→ fonctions dominantes
→ ton perçu
→ présence tonale

Si deux évaluations produisent les mêmes citations et les mêmes fonctions dominantes, elles doivent produire les mêmes tons.

En cas d'hésitation entre deux noms de tons proches, choisis toujours le terme :

- le plus générique ;
- le moins interprétatif ;
- le plus directement justifiable par les fonctions observées.

Si un ton est trop faible pour atteindre 10 %, ne le mentionne pas dans perceived_tone.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — MAPPING SÉMANTIQUE VERS LES TONS DE L'ORGANISATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ACCÈS AUTORISÉ EN PHASE 2 :
- tone_presence issu de la Phase 1
- la liste des tons officiels de l'organisation]

Objectif :

Relier les tons réellement détectés dans le contenu aux tons officiels de l'organisation, sans modifier les résultats de la Phase 1.

Cette phase ne remplace jamais les tons détectés.

Elle produit une représentation complémentaire permettant de comprendre comment les tonalités observées s'inscrivent dans le référentiel éditorial de l'organisation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIVEAU 1 — TONS RÉELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Les tons détectés en Phase 1 représentent la réalité observée dans le texte.

Ils doivent être recopiés à l'identique dans level_1_real_tones.

Aucune modification, normalisation ou traduction n'est autorisée à ce niveau.

Règle :

level_1_real_tones doit être strictement identique à tone_presence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIVEAU 2 — MAPPING SÉMANTIQUE 1-TO-1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pour chaque ton détecté en Phase 1 :

1. Compare ce ton à chacun des tons officiels de l'organisation.
2. Évalue leur proximité sémantique.
3. Identifie le ton officiel le plus proche.
4. Attribue un score de similarité compris entre 0.00 et 1.00.
5. Fournis une justification courte expliquant le rapprochement ou le rejet.

La proximité sémantique doit être évaluée selon :

- le sens général du ton ;
- la posture éditoriale ;
- la fonction rhétorique dominante ;
- l'intention de communication ;
- la manière dont le lecteur perçoit le message.

La proximité ne doit jamais être basée uniquement sur une ressemblance lexicale.

Le raisonnement doit être effectué indépendamment pour chaque ton détecté.

Règles obligatoires :

- Chaque ton détecté produit exactement une entrée dans level_2_mapping.
- Chaque ton détecté ne peut être associé qu'à un seul ton officiel.
- Le ton officiel sélectionné doit être celui dont la similarité est la plus élevée.
- La similarité doit être exprimée entre 0.00 et 1.00.
- Les scores sont des estimations sémantiques cohérentes et non des calculs mathématiques exacts.
- Chaque entrée doit contenir une justification explicite.

Seuil de validité :

Si aucun ton officiel n'atteint une similarité de 0.70 :

- mapped_tone = null
- in_org_vocabulary = false

Dans ce cas :

- le ton détecté reste inchangé dans level_1_real_tones ;
- aucun rattachement au vocabulaire de l'organisation n'est effectué ;
- le ton ne contribue pas aux scores de level_3_org_scores.

Ne force jamais une correspondance faible.

En cas de doute, préfère :

mapped_tone = null

plutôt qu'un rapprochement artificiel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIVEAU 3 — AGRÉGATION PAR TON OFFICIEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Une fois tous les mappings réalisés :

1. Regroupe les source_scores par mapped_tone.
2. Additionne les scores associés au même ton officiel.
3. Produis un score global par ton officiel dans level_3_org_scores.

Tous les tons officiels de l'organisation doivent apparaître dans level_3_org_scores.

Un ton officiel sans correspondance reçoit un score de 0.

Un ton détecté dont mapped_tone = null ne doit pas être ajouté à level_3_org_scores.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXEMPLE DE STRUCTURE UNIQUEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cet exemple sert uniquement à illustrer la structure attendue.

Les noms de tons, les scores et les correspondances présentés dans l'exemple ne doivent jamais être réutilisés comme référence lors de l'analyse.

L'analyse doit toujours être réalisée à partir du contenu réellement observé et des tons officiels réellement fournis.

Exemple :

"semantic_mapping": {{
    "level_1_real_tones": {{
      "didactique": 60,
      "posé": 40
    }},
    "level_2_mapping": [
      {{
        "source_tone": "didactique",
        "source_score": 60,
        "mapped_tone": "pédagogique",
        "semantic_similarity": 0.92,
        "in_org_vocabulary": true,
        "justification": "Didactique et pédagogique partagent la même intention d'explicitation et de transmission."
      }},
      {{
        "source_tone": "posé",
        "source_score": 40,
        "mapped_tone": "posé",
        "semantic_similarity": 1.00,
        "in_org_vocabulary": true,
        "justification": "Correspondance exacte avec le ton officiel."
      }}
    ],
    "level_3_org_scores": {{
      "pédagogique": 60,
      "posé": 40,
      "convaincant": 0,
      "fédérateur": 0
    }}
  }},
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÈGLES DE COHÉRENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- level_1_real_tones doit être strictement identique à tone_presence.
- Chaque source_tone de tone_presence doit apparaître une seule fois dans level_2_mapping.
- source_score doit être identique au score du même ton dans tone_presence.
- Chaque entrée de level_2_mapping doit contenir :
  source_tone,
  source_score,
  mapped_tone,
  semantic_similarity,
  in_org_vocabulary,
  justification.
- mapped_tone doit être soit null, soit un ton officiel de l'organisation.
- in_org_vocabulary doit être true uniquement si mapped_tone n'est pas null.
- in_org_vocabulary doit être false si mapped_tone est null.
- Tous les tons officiels doivent apparaître dans level_3_org_scores.
- Aucun ton non officiel ne doit apparaître dans level_3_org_scores.
- La somme des scores de level_3_org_scores ne doit jamais dépasser 100.
- Les tons réels détectés ne doivent jamais être modifiés ou remplacés par les tons officiels.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — DISTRIBUTION DES SCORES ORG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAPPEL — DISTINCTION AVEC LA PHASE 2

Phase 2 (mapping sémantique) et Phase 3 (distribution éditoriale) sont deux opérations distinctes. Ne pas les confondre.

Phase 2 autorise les rapprochements sémantiques larges :
  "didactique" → "pédagogique" ✓ (proximité de sens)

Phase 3 exige une correspondance stricte et littérale :
  "didactique" → "pédagogique" ✗ (termes différents)
  "pédagogique" → "pédagogique" ✓ (correspondance exacte)

Un ton détecté qui a été mappé en Phase 2 vers un ton org
n'est PAS considéré comme appartenant à la liste en Phase 3
si son libellé exact n'y figure pas.

Les deux phases produisent des résultats indépendants
et complémentaires dans le JSON final.

-------
Consulte maintenant la liste des tons de l'organisation.

Pour chaque ton détecté en Phase 1 (composante unique ou chaque composante hybride) :

Détermination de l'appartenance à la liste des tons de l'organisation :

Un ton détecté est considéré comme appartenant à la liste des tons de l'organisation uniquement s'il correspond clairement à un ton officiel.

Ne force pas une correspondance sur la base d'une simple proximité sémantique.

Exemple :
  "pédagogique" → "pédagogique" ✓
  "expert" → "expert" ✓
  "explicatif" → "pédagogique" ✗
  "émotionnel" → "convaincant" ✗

En cas de doute, considère que le ton détecté n'appartient pas à la liste.

CAS A — Le ton détecté EST présent dans la liste des tons de l'organisation :
  Relis le contenu attentivement.
  Distribue le score de ce ton (son pourcentage de Phase 1, ou 100 si non hybride)
  entre TOUS les tons de la liste de l'organisation.
  Ces scores représentent la part éditoriale estimée de chaque ton officiel dans le contenu.
  Ils ne représentent pas une probabilité statistique.
  Ils servent uniquement à répartir la présence tonale observée dans le contenu.

  Règles impératives :
  — La somme des scores distribués doit être exactement égale au score du ton détecté.
  — Chaque ton de la liste org doit apparaître exactement une fois.
  — Ne pas ignorer un ton de la liste org.
  — Ne pas inventer un ton absent de la liste org.
  — Un ton org sans présence dans le contenu reçoit un score de 0.

  Exemple :
    Ton détecté : "pédagogique" à 100 %, tons org : [posé, fédérateur, pédagogique, convaincant]
    → Après relecture, le contenu contient aussi quelques passages convaincants.
    → Distribution : pédagogique=80, convaincant=20, posé=0, fédérateur=0 (somme=100 ✓)

CAS B — Le ton détecté N'EST PAS présent dans la liste des tons de l'organisation :
  Ne pas distribuer ce score entre les tons org.
  Conserver le ton détecté tel quel avec son score de Phase 1.
  Les tons org reçoivent tous un score de 0 pour cette composante.

  Exemple :
    Tons détectés : "pédagogique" 70 % + "émotionnel" 30 %
    Tons org : [posé, fédérateur, pédagogique, convaincant]
    → "pédagogique" est dans les tons org → distribuer ses 70 points entre les tons org.
    → "émotionnel" n'est pas dans les tons org → garder 30 % tel quel, sans distribution.
    → Distribution org pour les 70 pts : pédagogique=55, convaincant=15, posé=0, fédérateur=0 (somme=70 ✓)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 — ÉVALUATION PAR CRITÈRES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Évalue le contenu sur les quatre critères ci-dessous.
Les critères évaluent le ton réellement détecté dans blind_observation, pas une simple correspondance directe avec expected_tone.
expected_tone sert de repère d’interprétation, mais il ne constitue plus un critère séparé.

──────────────────────────────────────
Critère 1 — Alignement contextuel du ton (poids 30 %)
Le ton détecté est-il compatible avec le contexte fourni ?
Le contexte sert uniquement à détecter des contradictions tonales.
Une incompatibilité contextuelle ne doit jamais être déduite uniquement parce que le contenu ne traite pas tous les éléments du contexte.
Tu n'évalues jamais la qualité du funnel, du persona, du brief ou de la voix éditoriale.
Tu vérifies uniquement que le ton adopté ne crée pas de contradiction avec ces éléments.
Sanctionne : ton pédagogique devenant promotionnel, neutre devenant prescriptif,
professionnel devenant familier, contenu informatif transformé en argumentaire.

Critère 2 — Cohérence du registre (poids 25 %)
Le registre reste-t-il stable dans l'ensemble du contenu ?
Sanctionne : ruptures brusques, passages soudainement promotionnels/familiers/
institutionnels, variations fortes entre sections.
Tolérance : variation acceptable si cohérente avec le ton global
et limitée à une section isolée.

Critère 3 — Calibrage de l'intensité (poids 25 %)
L'intensité est-elle proportionnée à l'objectif du contenu ?
Sur-intensification : emphase excessive, superlatifs, sensationnalisme,
dramatisation, posture trop persuasive.
Sous-intensification : ton trop générique, prudent, distancié,
sans position éditoriale, personnalité effacée.

Critère 4 — Naturalité de l'expression (poids 20 %)
Le ton paraît-il naturel, humain et fluide ?
Patterns à surveiller : connecteurs scolaires ("d'abord/ensuite/enfin"),
oppositions artificielles ("ce n'est pas..., c'est..."),
métadiscours ("l'enjeu est de...", "il s'agit de..."),
phrases-bilans sentencieuses, anglicismes marketing, style généré.
Seuils :
- même pattern répété 2 fois ou plus → pénalité possible ;
- même pattern répété 3 fois ou plus → pénalité forte ;
- 3 patterns artificiels distincts ou plus dans une même section → pénalité forte ;
- en dessous de ces seuils → signalement possible en "info" sans impact obligatoire sur le score.

Ne pénalise jamais un pattern isolé lorsqu'il reste naturel dans son contexte.
---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAPPEL DE STRUCTURE — CHAMPS OBLIGATOIRES DU JSON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Le JSON final doit contenir exactement ces champs, dans cet ordre :

1. dimension
2. confidence
3. blind_observation
4. semantic_mapping        ← OBLIGATOIRE — produit en Phase 2
5. ton_distribution        ← OBLIGATOIRE — produit en Phase 3
6. expected_tone
7. summary
8. criterion_scores
9. findings

Un JSON sans semantic_mapping est invalide et doit être recommencé.
Un JSON sans ton_distribution est invalide et doit être recommencé.
Ces deux champs sont indépendants et complémentaires. Les deux doivent être présents.

FORMAT DE SORTIE OBLIGATOIRE
JSON valide uniquement. Aucune balise Markdown. Aucun texte avant ou après.

Les criterion_scores doivent contenir deux évaluations distinctes :

1. detected_tone :

Évalue le contenu selon le ton réellement détecté dans blind_observation.perceived_tone.

Question :
Le contenu exécute-t-il correctement ce ton ?

Les notes doivent mesurer :
- la qualité d'exécution du ton détecté ;
- sa stabilité ;
- sa naturalité ;
- son calibrage.

Un contenu peut obtenir de très bonnes notes même si le ton détecté ne correspond pas au ton attendu.


2. expected_tone :

Évalue exactement le même contenu,
mais cette fois en utilisant expected_tone comme référentiel.

Question :
Si expected_tone était le ton cible,
le contenu exécute-t-il correctement ce ton ?

Les notes doivent mesurer :
- la qualité d'exécution du ton attendu ;
- sa stabilité ;
- sa naturalité ;
- son calibrage.

Si le ton attendu n'est pas réellement présent dans le contenu,
les notes expected_tone doivent être significativement plus faibles que les notes detected_tone.

Important :
expected_tone n'évalue pas la qualité générale du texte.
Il évalue uniquement la qualité du texte sous l'angle du ton attendu.
Les deux blocs doivent utiliser exactement les mêmes criterion_ids.

{{
  "dimension": "tone",
  "confidence": 0.0,

  "blind_observation": {{
    "perceived_tone": "Ton dominant perçu, 2 à 4 mots.",
    "tone_presence": {{
      "ton_A": 0,
      "ton_B": 0
    }},
    "lexical_evidence": [
      "Citation exacte 1 — explication courte.",
      "Citation exacte 2 — explication courte."
    ]
  }},

  "semantic_mapping": {{
    "level_1_real_tones": {{
      "<tone_detecte_1>": 0,
      "<tone_detecte_2>": 0
    }},
    "level_2_mapping": [
      {{
        "source_tone": "<tone_detecte_1>",
        "source_score": 0,
        "mapped_tone": "<ton_org>" ,
        "semantic_similarity": 0.0,
        "in_org_vocabulary": true,
        "justification": "<explication du rapprochement>"
      }}
    ],
    "level_3_org_scores": {{
      "<ton_org_1>": 0,
      "<ton_org_2>": 0,
      "<ton_org_3>": 0,
      "<ton_org_4>": 0
    }}
  }},

  "ton_distribution": [
    {{
      "source_tone": "Ton détecté depuis Phase 1 (celui distribué).",
      "source_score": 0,
      "in_org_list": true,
      "distribution": [
        {{
          "tone": "Ton org",
          "score": 0,
          "justification": "Une phrase max."
        }}
      ],
      "sum_check": 0
    }}
  ],

  "expected_tone": "...",
  "summary": "Synthèse de 2 à 3 phrases : ton observé, écart avec le ton attendu, problèmes principaux.",

  "criterion_scores": {{
    "detected_tone": {{
      "tone.contextual_alignment":  0,
      "tone.register_consistency":  0,
      "tone.intensity_calibration": 0,
      "tone.natural_expression":    0
    }},
    "expected_tone": {{
      "tone.contextual_alignment":  0,
      "tone.register_consistency":  0,
      "tone.intensity_calibration": 0,
      "tone.natural_expression":    0
    }}
  }},

  "findings": [
    {{
      "rule_id": "tone.contextual_alignment | tone.register_consistency | tone.intensity_calibration | tone.natural_expression",
      "severity": "info | minor | major | critical",
      "message": "Description précise du problème constaté.",
      "evidence": {{
        "excerpt":     "Citation exacte du passage concerné.",
        "explanation": "Explication concise de la dérive observée."
      }}
    }}
  ]
}}
---
RÈGLES DE SCORING

Note chaque critère sur 100 dans criterion_scores.
Les valeurs de criterion_scores sont des notes sur 100.

Ne retourne jamais les poids (30, 25, 25, 20) comme notes.

Exemple correct :
  "tone.contextual_alignment": 92

Exemple incorrect :
  "tone.contextual_alignment": 30
---
RÈGLES DE SÉVÉRITÉ
  "critical" → contradiction majeure ou dérive massive du registre.
  "major"    → rupture claire, incompatibilité contextuelle importante, artificialité visible.
  "minor"    → dérive ponctuelle, impact limité.
  "info"     → signal faible, non pénalisant.
---
RÈGLES SUR LES FINDINGS
  Maximum 8 findings toutes sévérités confondues.
  Chaque finding cite un extrait réellement présent dans le contenu.
  Les findings doivent être cohérents avec les notes attribuées dans criterion_scores.
  Une note élevée (>80) ne doit généralement pas produire de findings majeurs ou critiques.
  Une note faible (<60) doit généralement être justifiée par au moins un finding significatif.
---
RÈGLE SUR LA CONFIDENCE
  La confidence mesure uniquement la clarté de l'interprétation tonale.
  Elle ne mesure ni la qualité du texte ni son adéquation avec le ton attendu.
  confidence ∈ [0.0, 1.0] :
  1.0 → ton clair, univoque.
  0.5 → ton ambigu ou hétérogène, interprétation requise.
  0.0 → ton indéterminable.
---
RÈGLE DE PRIORITÉ

L'ordre logique est obligatoire :

1. Observation aveugle.
2. Identification du ton réel.
3. Mapping sémantique vers les tons de l'organisation (semantic_mapping).
4. Distribution éditoriale dans les tons de l'organisation (ton_distribution).
5. Évaluation du ton détecté.
6. Comparaison avec le ton attendu.
7. Attribution des scores.

Ne commence jamais par comparer le contenu au ton attendu avant d'avoir terminé l'observation aveugle.
---
CONSIGNES FINALES
Ne propose pas de réécriture. Ne donne aucun conseil.
Ne juge pas directement le funnel, le persona, le brief, la voix éditoriale ou le type de contenu.
tone_presence reflète l'observation aveugle de la Phase 1 — jamais une reprise de expected_tone.
Dans tone_presence, la somme des pourcentages doit être exactement 100.
semantic_mapping est obligatoire. Le JSON est invalide si semantic_mapping est absent.
semantic_mapping.level_1_real_tones doit être strictement identique à blind_observation.tone_presence.
semantic_mapping.level_2_mapping doit contenir exactement une entrée pour chaque ton présent dans tone_presence.
semantic_mapping.level_3_org_scores doit contenir tous les tons officiels de l'organisation, même avec un score de 0.
Dans ton_distribution : pour chaque entrée où in_org_list=true, sum_check doit être exactement égal à source_score.
Dans ton_distribution : pour chaque entrée où in_org_list=false, distribution = [] et sum_check = source_score.
Cite uniquement des extraits réellement présents dans le contenu évalué.
"""


def _format_org_tones(org_tones: object) -> str:
    """Format organization tones for prompt injection."""
    if not isinstance(org_tones, list) or not org_tones:
        return "[]"

    cleaned_org_tones = [str(tone).strip() for tone in org_tones if str(tone).strip()]

    return json.dumps(cleaned_org_tones, ensure_ascii=False)


def build_tone_judge_prompt(
    content: str,
    judge_rules: dict[str, object],
) -> str:
    """Build the LLM prompt for tone evaluation."""
    context = judge_rules.get("context") or {}

    if not isinstance(context, dict):
        context = {}

    return TONE_JUDGE_PROMPT_TEMPLATE.format(
        expected_tone=str(context.get("expected_tone", "")),
        organization_voice=str(context.get("organization_voice", "")),
        organization_voice_description=str(
            context.get("organization_voice_description", "")
        ),
        writing_style=str(context.get("writing_style", "")),
        funnel_stage=str(context.get("funnel_stage", "")),
        persona=str(context.get("persona", "")),
        content_type=str(context.get("content_type", "")),
        brief=str(context.get("brief", "")),
        locale=str(context.get("locale", "")),
        org_tones=_format_org_tones(context.get("org_tones", [])),
        content=content,
    )
