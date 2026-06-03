"""Prompt builder for the tone judge."""

from __future__ import annotations

import json

TONE_JUDGE_PROMPT_TEMPLATE = """Tu es un évaluateur spécialisé dans le contrôle qualité du ton rédactionnel d'un contenu éditorial.
Ta tâche n'est pas de réécrire le texte.
Ta tâche consiste à :
  1. Détecter le ton réel du contenu (observation aveugle).
  2. Distribuer le score du ton détecté entre les tons de l'organisation (si applicable).
  3. Évaluer le contenu par rapport aux tons détectés et au ton attendu.
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
  ton_distribution=null
  criterion_scores=null
  findings=[]
  summary="Le ton attendu est absent ou non interprétable. Évaluation impossible."

Condition 2 — Contenu trop court :
Si le contenu contient moins de 80 mots OU moins de 3 phrases complètes :
  confidence=null
  blind_observation=null
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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — OBSERVATION AVEUGLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lis le contenu comme si aucune information sur le ton attendu n'existait.

Le ton attendu et les tons de l'organisation ne doivent jamais influencer l'observation aveugle.

La Phase 1 doit pouvoir être réalisée même si ces informations étaient absentes.
Identifie le ton tel qu'il se manifeste naturellement.

1a. Ton perçu (perceived_tone) :
Décris le ton dominant en 2 à 4 mots.

1b. Marqueurs lexicaux (lexical_evidence) :
Liste 2 à 4 citations exactes du contenu avec une explication courte pour chacune.

1c. Présence tonale (tone_presence) :
Indique les tons réellement perçus dans le contenu avec un pourcentage entier.
La somme doit être exactement 100.
Si le texte est homogène, retourne un seul ton à 100.
Si le texte est hybride, retourne 2 à 4 tons maximum.
Chaque ton déclaré doit représenter plus de 10 % du ton observé.

Exemples :
{{ "pédagogique": 70, "posé": 30 }}
{{ "didactique": 100 }}

RÈGLE DE COHÉRENCE ENTRE perceived_tone, tone_presence ET ton_distribution

Les tons mentionnés dans perceived_tone doivent être exactement les mêmes que les clés de tone_presence.

Chaque ton présent dans tone_presence doit avoir une entrée correspondante dans ton_distribution.

Il est interdit de remplacer un ton détecté par un ton officiel de l’organisation dans tone_presence.

Les tons de l’organisation servent uniquement à ton_distribution, jamais à réécrire le ton réellement perçu.

Exemple correct :
perceived_tone = "sensible, empathique, rassurant"
tone_presence = {{
  "sensible": 45,
  "empathique": 35,
  "rassurant": 20
}}

Exemple incorrect :
perceived_tone = "sensible, empathique, rassurant"
tone_presence = {{
  "posé": 60,
  "pédagogique": 40
}}

Si un ton est trop faible pour atteindre 10 %, ne le mentionne pas dans perceived_tone.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — DISTRIBUTION DES SCORES ORG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
PHASE 3 — ÉVALUATION PAR CRITÈRES
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
3. Distribution éventuelle dans les tons de l'organisation.
4. Évaluation du ton détecté.
5. Comparaison avec le ton attendu.
6. Attribution des scores.

Ne commence jamais par comparer le contenu au ton attendu avant d'avoir terminé l'observation aveugle.
---
CONSIGNES FINALES
Ne propose pas de réécriture. Ne donne aucun conseil.
Ne juge pas directement le funnel, le persona, le brief, la voix éditoriale ou le type de contenu.
tone_presence reflète l'observation aveugle de la Phase 1 — jamais une reprise de expected_tone.
Dans tone_presence, la somme des pourcentages doit être exactement 100.
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
