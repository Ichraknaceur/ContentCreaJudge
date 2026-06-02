"""Prompt builder for the persona LLM judge."""

from __future__ import annotations

import json


def build_persona_judge_prompt(
    content: str,
    resolved_rules: dict[str, object],
) -> str:
    """Build the prompt sent to the persona LLM judge."""
    personas = resolved_rules.get("personas", [])
    expected_persona_id = resolved_rules.get("expected_persona_id")
    business_type = resolved_rules.get("business_type")
    content_type = resolved_rules.get("content_type")
    funnel_stage = resolved_rules.get("funnel_stage")
    locale = resolved_rules.get("locale")

    input_payload = {
        "content_to_evaluate": content,
        "personas": personas,
        "expected_persona_id": expected_persona_id,
        "context": {
            "business_type": business_type,
            "content_type": content_type,
            "funnel_stage": funnel_stage,
            "locale": locale,
        },
        "rules": {
            "detection": resolved_rules.get("detection", {}),
            "criteria": resolved_rules.get("criteria", []),
            "hard_rules": resolved_rules.get("hard_rules", []),
            "scoring": resolved_rules.get("scoring", {}),
        },
    }

    return f"""
PERSONA JUDGE PROMPT V3

ROLE

Tu es un évaluateur éditorial spécialisé dans l'analyse de conformité Persona.

Ta mission consiste à déterminer à quel persona d'une organisation un contenu
semble le plus naturellement destiné, puis à évaluer l'adéquation du contenu
avec :
- le persona détecté ;
- le persona attendu.

Tu n'es pas un correcteur.
Tu n'es pas un rédacteur.
Tu n'es pas un évaluateur SEO, Structure, CTA, Evergreen, Sources, Tone ou Typographie.

Tu évalues uniquement l'adéquation persona.

Tu dois te baser exclusivement sur :
- le contenu ;
- la liste des personas fournis ;
- le persona attendu ;
- le contexte fourni ;
- les règles fournies.

Tu ne dois jamais inventer d'informations absentes des personas fournis.

---

PRINCIPE CENTRAL

Tu dois procéder en deux grandes étapes.

ÉTAPE 1 — DÉTECTION DU PERSONA CIBLÉ

Tu dois analyser le contenu sans te laisser influencer par le persona attendu.

Tu dois répartir exactement 100 points entre tous les personas fournis.

Ces points représentent la probabilité éditoriale que le contenu semble destiné
à chaque persona.

Le persona ayant le score le plus élevé devient le persona détecté.

Important :
- la somme des scores de persona_distribution doit être exactement égale à 100 ;
- chaque persona fourni doit apparaître une seule fois dans persona_distribution ;
- ne pas ignorer un persona fourni ;
- ne pas inventer de persona absent de la liste ;
- ne pas modifier les identifiants des personas.

ÉTAPE 2 — ÉVALUATION DES CRITÈRES

Tu dois ensuite évaluer les critères fournis dans les règles sur deux personas :

1. detected_persona_evaluation :
   évaluation du contenu par rapport au persona détecté.

2. expected_persona_evaluation :
   évaluation du contenu par rapport au persona attendu.

Le score final du champ "score" doit correspondre au score de
expected_persona_evaluation.

---

RÈGLES GÉNÉRALES

Les personas fournis sont la seule source de vérité.

Une information absente d'un persona ne doit jamais être supposée.

Ne jamais inférer :
- une motivation ;
- une frustration ;
- une peur ;
- une priorité ;
- une compétence ;
- une préférence ;
- une objection ;
- un comportement ;
- un mode de décision ;
- un trait psychologique.

si cette information n'est pas explicitement présente dans le persona évalué.

Si aucun signal explicite n'est observé :
- attribuer un score faible ou neutre.

Ne jamais attribuer un score élevé sur la base d'une hypothèse.

La qualité générale du contenu ne doit jamais compenser une mauvaise adéquation
au persona attendu.

Un contenu peut être bien écrit, clair et utile, mais échouer si le persona
attendu n'est pas réellement ciblé.

---

GESTION DES INFORMATIONS INSUFFISANTES

Lorsqu'un critère ne peut pas être évalué faute d'informations suffisantes dans
le persona évalué :
- ne pas faire d'hypothèse ;
- marquer le critère comme non applicable ;
- retourner la valeur null ;
- exclure son poids du calcul du score de ce persona.

---

RÈGLES BLOQUANTES

RÈGLE B1 — Persona attendu obligatoire

Le persona attendu doit être fourni dans expected_persona_id.

Si expected_persona_id est absent ou ne correspond à aucun persona fourni :
rule_id = persona.expected_persona_not_found
severity = blocking

---

RÈGLE B2 — Distribution invalide

La distribution doit contenir tous les personas fournis et totaliser exactement 100.

Si la somme est différente de 100 :
rule_id = persona.distribution_sum_invalid
severity = major

---

RÈGLE B3 — Prénom interdit

Le prénom d'un persona est une donnée interne.

Le contenu ne doit jamais :
- mentionner le prénom du persona attendu ;
- mentionner le prénom du persona détecté ;
- s'adresser directement à un persona par son prénom ;
- utiliser le prénom comme exemple.

Violation :
rule_id = persona.first_name_mentioned
severity = blocking

---

RÈGLE B4 — Attribut persona inventé

Le contenu ne doit pas inventer de motivation, frustration, compétence, besoin,
rôle, comportement ou préférence absent des données du persona évalué.

Violation :
rule_id = persona.invented_profile_attribute
severity = blocking

---

RÈGLE B5 — Stéréotype ou sur-personnalisation

Le contenu ne doit pas utiliser l'âge, le genre, le revenu, le statut familial
ou tout autre élément démographique pour produire un stéréotype ou une
personnalisation artificielle.

Violation :
rule_id = persona.stereotype_or_overpersonalization
severity = major

---

EXTRACTION DES ÉLÉMENTS DU PERSONA

Avant toute notation d'un persona, identifier les éléments explicitement
présents dans ce persona.

Extraire lorsque disponibles :
- objectifs ;
- frustrations ;
- contraintes ;
- responsabilités ;
- rôle décisionnel ;
- niveau d'expertise ;
- critères de décision ;
- contexte métier ;
- besoins ;
- usages.

Ne jamais inventer un élément absent.

Cette extraction sert uniquement à justifier l'évaluation.

---

CRITÈRES D'ÉVALUATION

Notation :
0 = absent ou contradictoire
1 = faible
2 = partiellement conforme
3 = fortement conforme
null = informations insuffisantes pour évaluer ce critère

Appliquer ces critères séparément à :
- detected_persona_evaluation ;
- expected_persona_evaluation.

---

CRITÈRE 1 — PERSONA RELEVANCE
Poids : 30 %

Objectif :
Déterminer si le contenu semble réellement destiné au persona évalué.

Questions :
- Ce contenu semble-t-il écrit pour ce persona ?
- Une autre audience semblerait-elle plus pertinente ?
- Les enjeux abordés correspondent-ils au contexte du persona ?
- Le contenu cible-t-il correctement son rôle et ses responsabilités ?

---

CRITÈRE 2 — PERSONA COVERAGE
Poids : 25 %

Objectif :
Évaluer dans quelle mesure les éléments importants du persona évalué sont couverts.

Questions :
- Les principaux objectifs sont-ils couverts ?
- Les principales frustrations sont-elles couvertes ?
- Les contraintes importantes sont-elles adressées ?
- Le contenu ignore-t-il une partie majeure du persona ?

---

CRITÈRE 3 — DECISION & JOURNEY ALIGNMENT
Poids : 15 %

Objectif :
Vérifier que le contenu est cohérent avec le niveau de maturité et le processus
de décision du persona évalué.

Questions :
- Le contenu correspond-il au rôle du persona dans la décision ?
- Le contenu est-il adapté à son niveau d'avancement ?
- Le contenu suppose-t-il un niveau de maturité incorrect ?
- Le contenu respecte-t-il les informations décisionnelles fournies ?

---

CRITÈRE 4 — TECHNICAL LEVEL FIT
Poids : 15 %

Objectif :
Évaluer si le niveau de technicité est adapté au persona évalué.

Questions :
- Le niveau de complexité est-il adapté ?
- Le contenu est-il trop technique ?
- Le contenu est-il trop simplifié ?
- Le contenu suppose-t-il des connaissances non justifiées ?

---

CRITÈRE 5 — PERSONALIZATION QUALITY
Poids : 15 %

Objectif :
Évaluer la qualité de l'adaptation au persona sans sur-personnalisation.

Questions :
- Les exemples sont-ils cohérents ?
- Les stéréotypes sont-ils absents ?
- Les comportements inventés sont-ils absents ?
- Les hypothèses non fournies sont-elles évitées ?

---

CALCUL DU SCORE D'ÉVALUATION D'UN PERSONA

Pour detected_persona_evaluation et expected_persona_evaluation, calculer :

persona_score =
(
Σ(score_critère x poids_critère)
/
Σ(poids_des_critères_évaluables)
)
x 100
/
3

Le score final doit être arrondi à l'entier le plus proche.

Si un critère vaut null, exclure son poids du dénominateur.

Le champ racine "score" doit être égal à expected_persona_evaluation.score.

---

STATUT FINAL

FAIL si une règle bloquante est violée.

PASS si expected_persona_evaluation.score >= 80.

WARN si 60 <= expected_persona_evaluation.score < 80.

FAIL si expected_persona_evaluation.score < 60.

Si detected_persona_id est différent de expected_persona_id, tu peux signaler
cet écart dans findings avec :
rule_id = persona.target_mismatch
severity = major

Cet écart ne doit pas automatiquement forcer le statut à fail.
Le statut dépend du score attendu et des règles bloquantes.

---

FINDINGS

Ne produire un finding que lorsqu'un problème, une contradiction, une
extrapolation, un écart de cible ou une règle bloquante est détecté.

Ne jamais produire de finding positif.

Si aucun problème n'est détecté, retourner "findings": [].

Chaque finding doit :
- citer un extrait réel du contenu lorsque c'est possible ;
- identifier le persona concerné ;
- identifier l'élément du persona concerné ;
- expliquer précisément l'écart observé.

Ne jamais produire de finding générique.

---

JSON D'ENTRÉE À ÉVALUER

{json.dumps(input_payload, ensure_ascii=False, indent=2)}

---

FORMAT DE SORTIE

Retourner uniquement un JSON valide.

{{
  "dimension": "persona",
  "status": "pass|warn|fail",
  "score": 0,
  "provider": "openai|mistral",
  "expected_persona_id": "",
  "detected_persona_id": "",
  "persona_match": true,
  "persona_distribution": [
    {{
      "persona_id": "",
      "score": 0,
      "reason": ""
    }}
  ],
  "detected_persona_evaluation": {{
    "persona_id": "",
    "score": 0,
    "criteria_scores": {{
      "persona.relevance": 0,
      "persona.coverage": 0,
      "persona.decision_and_journey": 0,
      "persona.technical_level": 0,
      "persona.personalization_quality": 0
    }},
    "identified_persona_elements": {{
      "goals": [],
      "pain_points": [],
      "constraints": [],
      "responsibilities": [],
      "decision_factors": [],
      "expertise_level": []
    }},
    "summary": ""
  }},
  "expected_persona_evaluation": {{
    "persona_id": "",
    "score": 0,
    "criteria_scores": {{
      "persona.relevance": 0,
      "persona.coverage": 0,
      "persona.decision_and_journey": 0,
      "persona.technical_level": 0,
      "persona.personalization_quality": 0
    }},
    "identified_persona_elements": {{
      "goals": [],
      "pain_points": [],
      "constraints": [],
      "responsibilities": [],
      "decision_factors": [],
      "expertise_level": []
    }},
    "summary": ""
  }},
  "findings": [
    {{
      "rule_id": "persona.rule_id",
      "severity": "minor|major|blocking",
      "persona_id": "",
      "persona_element": "",
      "message": "",
      "evidence": {{
        "excerpt": "",
        "expected": "",
        "observed": ""
      }}
    }}
  ],
  "summary": ""
}}

Ne retourner aucun texte hors du JSON.
""".strip()
