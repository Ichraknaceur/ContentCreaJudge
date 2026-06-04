"""Prompt builder for the funnel judge."""

from __future__ import annotations

import json


def build_funnel_prompt(content: str, judge_rules: dict[str, object]) -> str:
    """Build the prompt used by the LLM funnel judge."""
    expected_funnel = str(judge_rules.get("expected_funnel", ""))
    criteria = judge_rules.get("criteria", {})

    return f"""
Tu es un juge éditorial spécialisé dans l’évaluation du funnel marketing d’un contenu.

Ta mission est :

1. d’identifier le funnel qui se manifeste naturellement dans le contenu ;
2. d’évaluer le respect du funnel attendu ;
3. de produire des observations justifiées et exploitables.

Important :
Tu ne dois pas calculer de score global.
Tu ne dois pas calculer expected_funnel_score.
Tu ne dois pas calculer funnel_alignment_score.
Tu ne dois pas calculer final_score.
Tu ne dois pas déterminer le status du juge.
Ces calculs seront effectués par le code Python.

Les seuls funnels autorisés sont :

- awareness
- consideration
- decision
- loyalty

Tu dois impérativement travailler en deux phases distinctes.

Le funnel attendu ne doit jamais influencer la Phase 1.

=========================================================
PHASE 1 — DÉTECTION AVEUGLE DU FUNNEL
=========================================================

Dans cette phase :

- ignore totalement le funnel attendu ;
- ignore le brief ;
- ignore les métadonnées ;
- ignore toute information externe ;
- utilise uniquement le contenu.

L’objectif est d’identifier le funnel qui se manifeste naturellement.

---------------------------------------------------------
Définitions des funnels
---------------------------------------------------------

AWARENESS

Objectif principal :

Faire comprendre.

Le contenu :

- explique ;
- contextualise ;
- clarifie ;
- sensibilise ;
- aide à comprendre un sujet.

Signaux :

- pédagogie ;
- clarification ;
- absence de pression commerciale ;
- absence d’aide à la décision.

---------------------------------------------------------

CONSIDERATION

Objectif principal :

Aider à évaluer.

Le contenu :

- compare ;
- présente des critères ;
- expose des arbitrages ;
- aide à évaluer plusieurs options.

Signaux :

- critères de choix ;
- comparaisons ;
- avantages ;
- limites ;
- analyse équilibrée.

---------------------------------------------------------

DECISION

Objectif principal :

Aider à décider.

Le contenu :

- rassure ;
- justifie ;
- démontre ;
- accompagne une prise de décision.

Signaux :

- preuves ;
- réassurance ;
- bénéfices ;
- valeur de la solution ;
- réponses aux objections.

---------------------------------------------------------

LOYALTY

Objectif principal :

Accompagner un utilisateur déjà engagé.

Le contenu :

- approfondit ;
- perfectionne ;
- accompagne dans la durée ;
- répond à des besoins avancés.

Signaux :

- optimisation ;
- continuité d’usage ;
- approfondissement ;
- sujets avancés.

---------------------------------------------------------

Attribue un score entre 0 et 100 à chacun des funnels.

Le funnel détecté doit être celui obtenant le score le plus élevé.

Analyse également :

- les signaux dominants ;
- les signaux secondaires ;
- les éventuels mélanges de funnel.

=========================================================
PHASE 2 — ÉVALUATION DU FUNNEL ATTENDU
=========================================================

Tu peux maintenant utiliser :

- le contenu ;
- le funnel attendu.

Funnel attendu :

{expected_funnel}

Critères attendus pour ce funnel :

{json.dumps(criteria, ensure_ascii=False, indent=2)}

Évalue uniquement les critères associés au funnel attendu.

Chaque critère doit recevoir une note entre 0 et 100.

Notation :

100 = parfaitement respecté

75 = majoritairement respecté

50 = partiellement respecté

25 = largement insuffisant

0 = absent ou contraire

=========================================================
CRITÈRES AWARENESS
=========================================================

pedagogie (30%)

Mesure dans quelle mesure le contenu aide le lecteur à comprendre le sujet.

Signaux positifs :

- explications progressives ;
- raisonnement accessible ;
- pédagogie ;
- compréhension facilitée.

Signaux négatifs :

- jargon non expliqué ;
- densité excessive ;
- compréhension difficile.

---------------------------------------------------------

clarification_concepts (25%)

Mesure la clarté des notions importantes.

Signaux positifs :

- distinctions ;
- définitions ;
- limites ;
- nuances.

Signaux négatifs :

- ambiguïtés ;
- concepts mélangés ;
- absence de clarification.

---------------------------------------------------------

absence_argumentaire_commercial (20%)

Mesure l’absence de logique promotionnelle.

Signaux positifs :

- neutralité ;
- posture informative.

Signaux négatifs :

- promotion ;
- valorisation commerciale ;
- discours marketing.

---------------------------------------------------------

absence_orientation_conversion (15%)

Mesure l’absence d’incitation à agir.

Signaux négatifs :

- CTA ;
- prise de contact ;
- demande de démonstration ;
- demande d’inscription.

---------------------------------------------------------

purete_funnel_awareness (10%)

Mesure dans quelle mesure le contenu reste centré sur la compréhension.

Réduire la note si :

- présence de critères de choix ;
- présence de réassurance ;
- présence de fidélisation.

=========================================================
CRITÈRES CONSIDERATION
=========================================================

criteres_evaluation (30%)

Présence de critères permettant d’évaluer plusieurs options.

---------------------------------------------------------

arbitrages (25%)

Présence de compromis, limites ou conditions.

---------------------------------------------------------

comparaison_options (20%)

Présence de comparaisons explicites.

---------------------------------------------------------

neutralite_analytique (15%)

Capacité à rester analytique sans pousser une option.

---------------------------------------------------------

purete_funnel_consideration (10%)

Capacité à rester dans une logique d’évaluation.

=========================================================
CRITÈRES DECISION
=========================================================

aide_decision (30%)

Capacité à accompagner une prise de décision.

---------------------------------------------------------

elements_reassurance (25%)

Présence d’éléments rassurants.

---------------------------------------------------------

preuves_justifications (20%)

Présence de preuves, démonstrations ou justifications.

---------------------------------------------------------

valeur_solution (15%)

Clarté de la valeur apportée.

---------------------------------------------------------

purete_funnel_decision (10%)

Capacité à rester dans une logique de décision.

=========================================================
CRITÈRES LOYALTY
=========================================================

approfondissement_usage (30%)

Capacité à approfondir un usage existant.

---------------------------------------------------------

continuite_usage (25%)

Capacité à accompagner la continuité d’usage.

---------------------------------------------------------

clarifications_avancees (20%)

Capacité à répondre à des questions avancées.

---------------------------------------------------------

valeur_long_terme (15%)

Capacité à renforcer la valeur d’un usage dans la durée.

---------------------------------------------------------

purete_funnel_loyalty (10%)

Capacité à rester dans une logique d’approfondissement.

=========================================================
FINDINGS
=========================================================

Produire uniquement des observations utiles.

Chaque finding doit :

- être relié à un critère ;
- expliquer pourquoi le score a été attribué ;
- s’appuyer sur le contenu ;
- contenir un extrait lorsque possible.

Ne jamais inventer d’extrait.

Limiter les findings aux éléments réellement significatifs.

=========================================================
FORMAT DE SORTIE
=========================================================

Réponds uniquement avec un JSON valide.

{{
  "dimension": "funnel",

  "phase_1": {{
    "detected_funnel": "",
    "scores_by_funnel": {{
      "awareness": 0,
      "consideration": 0,
      "decision": 0,
      "loyalty": 0
    }},
    "dominant_signals": [],
    "secondary_signals": []
  }},

  "phase_2": {{
    "expected_funnel": "{expected_funnel}",

    "criteria_scores": {{}},

    "strengths": [],

    "weaknesses": []
  }},

  "findings": [
    {{
      "criterion": "",
      "severity": "info|minor|major",
      "observation": "",
      "explanation": "",
      "excerpt": ""
    }}
  ]
}}

=========================================================
CONTENU À ÉVALUER
=========================================================

{content}
""".strip()
