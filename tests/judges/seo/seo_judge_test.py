from __future__ import annotations

from contentcreajudge.preprocessing.seo_preprocessor import preprocess_seo_content
from contentcreajudge.rules.judges.seo.seo_resolver import resolve_seo_rules
from unittest.mock import patch
from contentcreajudge.judges.seo.seo_judge import (
    _compute_thematic_signals,
    run_seo_judge,
)


def _build_context(
    content_type: str = "articles",
    expected_length: str = "MEDIUM",
    funnel_stage: str = "AWARENESS",
) -> dict[str, object]:
    return {
        "content_type": content_type,
        "expected_length": expected_length,
        "funnel_stage": funnel_stage,
        "locale": "fr-FR",
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "secondary_keywords": [
            "coherence de la voix editoriale",
            "autorite thematique de la marque",
        ],
        "long_tail_keywords": [
            "repetition strategique du message sans impression de deja-vu en b2b",
        ],
    }

#**************Lexical**************#
def test_run_seo_judge_passes_on_good_lexical_content() -> None:
    content = """
    <p>La différenciation éditoriale en milieu saturé commence ici.</p>

    <h2>différenciation éditoriale en milieu saturé</h2>
    <p>La coherence de la voix editoriale améliore la lisibilite et l autorite thematique de la marque.</p>

    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé demeure un repère stable
    pour l autorite thematique de la marque et repetition strategique du message sans impression de deja-vu en b2b.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    assert result["dimension"] == "seo"
    assert result["status"] in {"pass", "warn"}
    assert result["score"] > 0


def test_run_seo_judge_fails_when_main_keyword_is_missing() -> None:
    content = """
    <p>Introduction generique.</p>
    <h2>Section</h2>
    <p>Contenu sans le sujet attendu.</p>
    <h2>Conclusion</h2>
    <p>Texte final generique.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "seo.main_keyword_presence" in rule_ids
    assert "seo.main_keyword_locations" in rule_ids


def test_run_seo_judge_detects_distribution_issue() -> None:
    content = """
    <p>La différenciation éditoriale en milieu saturé commence ici.</p>

    <h2>Section 1</h2>
    <p>coherence de la voix editoriale autorite thematique de la marque repetition strategique du message sans impression de deja-vu en b2b</p>

    <h2>Section 2</h2>
    <p>Texte generique sans autre mot-cle secondaire.</p>

    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé revient ici.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.keyword_distribution" in rule_ids


def test_run_seo_judge_detects_forbidden_keyword_emphasis() -> None:
    content = """
    <p><strong>différenciation éditoriale en milieu saturé</strong></p>
    <h2>Section</h2>
    <p>coherence de la voix editoriale</p>
    <h2>Conclusion</h2>
    <p>autorite thematique de la marque</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.formatting_constraints" in rule_ids


def test_run_seo_judge_detects_long_tail_over_optimization() -> None:
    repeated_long_tail = "repetition strategique du message sans impression de deja-vu en b2b"

    content = f"""
    <p>différenciation éditoriale en milieu saturé</p>
    <h2>Section</h2>
    <p>{repeated_long_tail} {repeated_long_tail} {repeated_long_tail}</p>
    <h2>Conclusion</h2>
    <p>différenciation éditoriale en milieu saturé coherence de la voix editoriale</p>
    """

    judge_rules = resolve_seo_rules(_build_context(content_type="articles", expected_length="LONG"))
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.over_optimization" in rule_ids


def test_run_seo_judge_detects_too_many_keyword_occurrences() -> None:
    repeated_main = "différenciation éditoriale en milieu saturé"
    repeated_secondary = "coherence de la voix editoriale"
    repeated_long_tail = "repetition strategique du message sans impression de deja-vu en b2b"

    content = f"""
    <p>{repeated_main} {repeated_main}</p>
    <h2>{repeated_main}</h2>
    <p>{repeated_secondary} {repeated_secondary}</p>
    <h2>Conclusion</h2>
    <p>{repeated_main} {repeated_long_tail} {repeated_long_tail} {repeated_secondary} {repeated_secondary} autorite thematique de la marque</p>
    """

    judge_rules = resolve_seo_rules(_build_context(expected_length="MEDIUM"))
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.keyword_occurrences" in rule_ids


def test_run_seo_judge_detects_main_keyword_below_min_main() -> None:
    content = """
    <p>différenciation éditoriale en milieu saturé</p>
    <h2>différenciation éditoriale en milieu saturé</h2>
    <p>coherence de la voix editoriale</p>
    <h2>Conclusion</h2>
    <p>autorite thematique de la marque</p>
    """

    judge_rules = resolve_seo_rules(_build_context(expected_length="SIMPLE"))
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    occurrence_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.keyword_occurrences"
    )

    assert occurrence_finding["evidence"]["expected_min_main"] == 3
    assert occurrence_finding["evidence"]["main_keyword_occurrences_in_body"] < 3


def test_run_seo_judge_returns_warn_when_only_minor_findings_exist() -> None:
    content = """
    <p><strong>différenciation éditoriale en milieu saturé</strong></p>
    <h2>différenciation éditoriale en milieu saturé</h2>
    <p>coherence de la voix editoriale et autorite thematique de la marque</p>
    <h2>Conclusion</h2>
    <p>différenciation éditoriale en milieu saturé repetition strategique du message sans impression de deja-vu en b2b et autorite thematique de la marque</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    assert result["status"] == "warn"
    assert all(finding["severity"] == "minor" for finding in result["findings"])
    assert any(
        finding["rule_id"] == "seo.formatting_constraints"
        for finding in result["findings"]
    )


def test_run_seo_judge_defaults_to_minor_when_rule_severity_is_missing() -> None:
    content = """
    <p><strong>différenciation éditoriale en milieu saturé</strong></p>
    <h2>différenciation éditoriale en milieu saturé</h2>
    <p>coherence de la voix editoriale et autorite thematique de la marque</p>
    <h2>Conclusion</h2>
    <p>différenciation éditoriale en milieu saturé repetition strategique du message sans impression de deja-vu en b2b et autorite thematique de la marque</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    judge_rules["rules"] = [
        rule
        for rule in judge_rules["rules"]
        if rule["rule_id"] != "seo.formatting_constraints"
    ]

    preprocessed = preprocess_seo_content(content, judge_rules)
    result = run_seo_judge(preprocessed, judge_rules)

    formatting_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.formatting_constraints"
    )

    assert formatting_finding["severity"] == "minor"
    assert result["status"] == "warn"

#****************Semantic***************#
def test_run_seo_judge_compensates_heading_location_with_semantics() -> None:
    content = """
    <p>La différenciation éditoriale en milieu saturé commence ici.</p>
    <h2>Un titre reformule mais proche du sujet</h2>
    <p>La coherence de la voix editoriale aide la lecture.</p>
    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé demeure importante.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)

    with patch(
        "contentcreajudge.judges.seo.seo_judge._semantic_similarity",
        side_effect=[0.86, 0.86, 0.88, 0.86],
    ):
        result = run_seo_judge(preprocessed, judge_rules)

    findings = result["findings"]
    location_finding = next(
        finding for finding in findings
        if finding["rule_id"] == "seo.main_keyword_locations"
    )

    assert "heading_h2_or_h3" in location_finding["evidence"]["compensated_locations"]
    assert result["status"] in {"warn", "pass"}

def test_run_seo_judge_does_not_compensate_heading_when_semantics_are_weak() -> None:
    content = """
    <p>Introduction generale.</p>
    <h2>Un titre tres vague</h2>
    <p>Contenu assez faible.</p>
    <h2>Conclusion</h2>
    <p>Conclusion finale.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)

    with patch(
        "contentcreajudge.judges.seo.seo_judge._semantic_similarity",
        side_effect=[0.40, 0.45, 0.42, 0.30],
    ):
        result = run_seo_judge(preprocessed, judge_rules)

    findings = result["findings"]
    location_finding = next(
        finding for finding in findings
        if finding["rule_id"] == "seo.main_keyword_locations"
    )

    assert "heading_h2_or_h3" in location_finding["evidence"]["missing_locations"]
    assert result["status"] == "fail"

def test_run_seo_judge_returns_lexical_and_semantic_subscores() -> None:
    content = """
    <p>La différenciation éditoriale en milieu saturé commence ici.</p>
    <h2>Un titre proche du sujet</h2>
    <p>La coherence de la voix editoriale aide la lecture.</p>
    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé demeure importante.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)

    with patch(
        "contentcreajudge.judges.seo.seo_judge._semantic_similarity",
        side_effect=[0.88, 0.86, 0.90, 0.86],
    ):
        result = run_seo_judge(preprocessed, judge_rules)

    assert "subscores" in result
    assert "lexical" in result["subscores"]
    assert "semantic" in result["subscores"]
    assert result["subscores"]["semantic"] > 0

def test_run_seo_judge_reduces_occurrence_penalty_when_body_semantics_are_good() -> None:
    content = """
    <p>Le texte reformule largement le sujet.</p>
    <h2>Section</h2>
    <p>Le contenu parle du bon sujet avec coherence de la voix editoriale sans répéter le mot-clé principal.</p>
    <h2>Conclusion</h2>
    <p>Conclusion cohérente.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)

    with patch(
        "contentcreajudge.judges.seo.seo_judge._semantic_similarity",
         side_effect=[0.86, 0.86, 0.88, 0.86],
    ):
        result = run_seo_judge(preprocessed, judge_rules)

    occurrence_finding = next(
        finding for finding in result["findings"]
        if finding["rule_id"] == "seo.keyword_occurrences"
    )

    assert occurrence_finding["evidence"]["semantic_body_compensation"] is True

#*****************Thematic****************#
def test_compute_thematic_signals_detects_matched_themes() -> None:
    lexical_signals = {
        "main_keyword": "lisibilité des risques technologiques",
        "secondary_keyword_occurrences": {
            "souveraineté des infrastructures numériques": 1,
        },
        "long_tail_keyword_occurrences": {},
    }

    thematic_inputs = {
        "keyphrases": [
            {"keyphrase": "risques technologiques", "score": 0.9},
        ]
    }

    body_text = (
        "La lisibilité des risques technologiques dépend aussi de la "
        "souveraineté des infrastructures numériques."
    )

    result = _compute_thematic_signals(
        lexical_signals=lexical_signals,
        thematic_inputs=thematic_inputs,
        body_text=body_text,
    )

    assert result["coverage_ratio"] == 1.0
    assert result["missing_themes"] == []
    assert len(result["matched_themes"]) == 2

def test_compute_thematic_signals_detects_missing_themes() -> None:
    lexical_signals = {
        "main_keyword": "lisibilité des risques technologiques",
        "secondary_keyword_occurrences": {
            "souveraineté des infrastructures numériques": 0,
        },
        "long_tail_keyword_occurrences": {},
    }

    thematic_inputs = {
        "keyphrases": [
            {"keyphrase": "communication interne", "score": 0.9},
            {"keyphrase": "climat de confiance", "score": 0.8},
        ]
    }

    body_text = "La communication interne améliore les échanges entre équipes."

    result = _compute_thematic_signals(
        lexical_signals=lexical_signals,
        thematic_inputs=thematic_inputs,
        body_text=body_text,
    )

    assert result["coverage_ratio"] == 0.0
    assert "lisibilité des risques technologiques" in result["missing_themes"]

def test_run_seo_judge_returns_thematic_subscore() -> None:
    content = """
    <p>La lisibilite des risques technologiques aide à mieux comprendre les dépendances numériques.</p>
    <h2>Risques technologiques</h2>
    <p>La souverainete des infrastructures numeriques demeure importante.</p>
    <h2>Conclusion</h2>
    <p>La lisibilite des risques technologiques demeure un repere.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)

    with patch(
        "contentcreajudge.judges.seo.seo_judge._semantic_similarity",
        side_effect=[0.9, 0.9, 0.9, 0.9],
    ):
        result = run_seo_judge(preprocessed, judge_rules)

    assert "thematic" in result["subscores"]
    assert "thematic_signals" in result
