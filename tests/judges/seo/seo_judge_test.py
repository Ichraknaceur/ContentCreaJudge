from __future__ import annotations

from unittest.mock import patch

import torch

import contentcreajudge.judges.seo.seo_judge as seo_judge_module
from contentcreajudge.judges.seo.seo_judge import (
    _compute_semantic_compensation,
    _compute_semantic_signals,
    _compute_weighted_top_chunk_score,
    _get_rule_severity,
    _is_conclusion_title,
    run_seo_judge,
    _compute_overoptimization_sentence_similarities,
    _compute_density_score,
    _compute_concentration_score,
    _compute_local_repetition_score,
    _compute_overoptimization_score,
)
from contentcreajudge.preprocessing.seo_preprocessor import preprocess_seo_content
from contentcreajudge.rules.judges.seo.seo_resolver import resolve_seo_rules


class _FakeSemanticModel:
    def encode(self, texts, convert_to_tensor=True, normalize_embeddings=True):
        return torch.tensor(
            [
                [1.0, 0.0],  # main keyword
                [0.9, 0.1],  # chunk 1
                [0.4, 0.6],  # chunk 2
                [0.8, 0.2],  # chunk 3
            ],
            dtype=torch.float,
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


def _run_judge_with_semantic_score(
    preprocessed: dict[str, object],
    judge_rules: dict[str, object],
    semantic_score: int = 75,
    overoptimization_sentence_signals: dict[str, object] | None = None,
) -> dict[str, object]:
    semantic_patch = patch(
        "contentcreajudge.judges.seo.seo_judge._compute_semantic_signals",
        return_value={
            "main_keyword": "différenciation éditoriale en milieu saturé",
            "top_chunks": [],
            "best_similarity": semantic_score / 100,
            "semantic_score": semantic_score,
        },
    )

    if overoptimization_sentence_signals is None:
        with semantic_patch:
            return run_seo_judge(preprocessed, judge_rules)

    overoptimization_patch = patch(
        "contentcreajudge.judges.seo.seo_judge."
        "_compute_overoptimization_sentence_similarities",
        return_value=overoptimization_sentence_signals,
    )

    with semantic_patch, overoptimization_patch:
        return run_seo_judge(preprocessed, judge_rules)


def _empty_overoptimization_sentence_signals() -> dict[str, object]:
    return {
        "main_keyword": "diffÃ©renciation Ã©ditoriale en milieu saturÃ©",
        "total_words": 100,
        "paragraphs": [],
        "semantic_occurrences": 0,
        "similarity_threshold": 0.75,
        "semantic_available": True,
    }


# ************** Lexical **************


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
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=90,
    )

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
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=90,
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "seo.main_keyword_presence" in rule_ids
    assert "seo.main_keyword_locations" in rule_ids


def test_run_seo_judge_detects_distribution_issue_as_minor() -> None:
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
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

    distribution_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.keyword_distribution"
    )

    assert distribution_finding["severity"] == "minor"


def test_run_seo_judge_does_not_penalize_distribution_when_no_secondary_or_long_tail_keywords() -> (
    None
):
    content = """
    <p>La différenciation éditoriale en milieu saturé commence ici.</p>

    <h2>différenciation éditoriale en milieu saturé</h2>
    <p>Le texte reste centré sur le sujet principal.</p>

    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé reste le fil directeur.</p>
    """

    context = _build_context(expected_length="SIMPLE")
    context["secondary_keywords"] = []
    context["long_tail_keywords"] = []

    judge_rules = resolve_seo_rules(context)
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=80,
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.keyword_distribution" not in rule_ids


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
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.formatting_constraints" in rule_ids


def test_run_seo_judge_does_not_use_long_tail_repetition_as_over_optimization() -> None:
    repeated_long_tail = (
        "repetition strategique du message sans impression de deja-vu en b2b"
    )

    content = f"""
    <p>différenciation éditoriale en milieu saturé</p>
    <h2>Section</h2>
    <p>{repeated_long_tail} {repeated_long_tail} {repeated_long_tail}</p>
    <h2>Conclusion</h2>
    <p>différenciation éditoriale en milieu saturé coherence de la voix editoriale</p>
    """

    judge_rules = resolve_seo_rules(
        _build_context(content_type="articles", expected_length="LONG")
    )
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "seo.over_optimization" not in rule_ids


def test_run_seo_judge_detects_too_many_main_keyword_occurrences() -> None:
    repeated_main = "différenciation éditoriale en milieu saturé"

    content = f"""
    <p>{repeated_main} {repeated_main}</p>
    <h2>{repeated_main}</h2>
    <p>{repeated_main} {repeated_main}</p>
    <h2>Conclusion</h2>
    <p>{repeated_main} {repeated_main} {repeated_main} {repeated_main} {repeated_main} {repeated_main}</p>
    """

    judge_rules = resolve_seo_rules(_build_context(expected_length="MEDIUM"))
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

    occurrence_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.keyword_occurrences"
    )

    assert occurrence_finding["evidence"]["main_keyword_occurrences_in_body"] > 10
    assert occurrence_finding["evidence"]["expected_max_total"] == 10


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
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

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
    judge_rules["keyword_distribution_rules"][
        "require_at_least_one_secondary_or_long_tail_per_h2_section"
    ] = False

    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

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
    judge_rules["keyword_distribution_rules"][
        "require_at_least_one_secondary_or_long_tail_per_h2_section"
    ] = False
    judge_rules["rules"] = [
        rule
        for rule in judge_rules["rules"]
        if rule["rule_id"] != "seo.formatting_constraints"
    ]

    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(preprocessed, judge_rules)

    formatting_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.formatting_constraints"
    )

    assert formatting_finding["severity"] == "minor"
    assert result["status"] == "warn"


# ************** Semantic helpers **************


def test_compute_weighted_top_chunk_score_returns_zero_without_chunks() -> None:
    score = _compute_weighted_top_chunk_score([])

    assert score == 0


def test_compute_weighted_top_chunk_score_with_three_chunks() -> None:
    top_chunks = [
        {"similarity": 0.81},
        {"similarity": 0.70},
        {"similarity": 0.60},
    ]

    score = _compute_weighted_top_chunk_score(top_chunks)

    assert score == 75


def test_compute_weighted_top_chunk_score_with_one_chunk() -> None:
    top_chunks = [{"similarity": 0.72}]

    score = _compute_weighted_top_chunk_score(top_chunks)

    assert score == 72


def test_compute_semantic_compensation_returns_strong_level() -> None:
    result = _compute_semantic_compensation({"semantic_score": 80})

    assert result["body_compensation_level"] == "strong"
    assert result["body_penalty_reduction"] == 10
    assert result["body_compensated"] is True


def test_compute_semantic_compensation_returns_medium_level() -> None:
    result = _compute_semantic_compensation({"semantic_score": 65})

    assert result["body_compensation_level"] == "medium"
    assert result["body_penalty_reduction"] == 5
    assert result["body_compensated"] is True


def test_compute_semantic_compensation_returns_none_level() -> None:
    result = _compute_semantic_compensation({"semantic_score": 40})

    assert result["body_compensation_level"] == "none"
    assert result["body_penalty_reduction"] == 0
    assert result["body_compensated"] is False


def test_compute_semantic_signals_returns_zero_when_main_keyword_is_missing() -> None:
    result = _compute_semantic_signals(
        {
            "main_keyword": "",
            "chunks": [{"chunk_id": 1, "text": "texte utile"}],
        }
    )

    assert result["top_chunks"] == []
    assert result["best_similarity"] == 0.0
    assert result["semantic_score"] == 0


def test_compute_semantic_signals_returns_zero_when_chunks_are_empty() -> None:
    result = _compute_semantic_signals(
        {
            "main_keyword": "différenciation éditoriale en milieu saturé",
            "chunks": [],
        }
    )

    assert result["top_chunks"] == []
    assert result["best_similarity"] == 0.0
    assert result["semantic_score"] == 0


def test_compute_semantic_signals_returns_zero_when_chunks_have_no_valid_text() -> None:
    result = _compute_semantic_signals(
        {
            "main_keyword": "différenciation éditoriale en milieu saturé",
            "chunks": [
                {"chunk_id": 1, "text": "   "},
                {"chunk_id": 2, "text": ""},
                {"chunk_id": 3},
            ],
        }
    )

    assert result["main_keyword"] == "différenciation éditoriale en milieu saturé"
    assert result["top_chunks"] == []
    assert result["best_similarity"] == 0.0
    assert result["semantic_score"] == 0


def test_compute_semantic_signals_ranks_top_chunks() -> None:
    semantic_inputs = {
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "chunks": [
            {
                "chunk_id": 1,
                "text": "chunk 1",
                "start_word": 0,
                "end_word": 10,
                "word_count": 10,
            },
            {
                "chunk_id": 2,
                "text": "chunk 2",
                "start_word": 10,
                "end_word": 20,
                "word_count": 10,
            },
            {
                "chunk_id": 3,
                "text": "chunk 3",
                "start_word": 20,
                "end_word": 30,
                "word_count": 10,
            },
        ],
    }

    with patch(
        "contentcreajudge.judges.seo.seo_judge._get_semantic_model",
        return_value=_FakeSemanticModel(),
    ):
        result = _compute_semantic_signals(semantic_inputs)

    assert result["main_keyword"] == "différenciation éditoriale en milieu saturé"
    assert len(result["top_chunks"]) == 3
    assert result["top_chunks"][0]["chunk_id"] == 1
    assert result["semantic_score"] > 0
    assert result["best_similarity"] > 0


def test_compute_semantic_signals_skips_non_dict_and_empty_chunks() -> None:
    semantic_inputs = {
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "chunks": [
            "not-a-dict",
            {"chunk_id": 1, "text": "   "},
            {
                "chunk_id": 2,
                "text": "chunk valide",
                "start_word": 10,
                "end_word": 20,
                "word_count": 10,
            },
        ],
    }

    with patch(
        "contentcreajudge.judges.seo.seo_judge._get_semantic_model",
        return_value=_FakeSemanticModel(),
    ):
        result = _compute_semantic_signals(semantic_inputs)

    assert len(result["top_chunks"]) == 1
    assert result["top_chunks"][0]["chunk_id"] == 2
    assert result["top_chunks"][0]["text"] == "chunk valide"
    assert result["semantic_score"] > 0


def test_get_semantic_model_caches_model_instance() -> None:
    seo_judge_module._load_semantic_model.cache_clear()

    with patch(
        "contentcreajudge.judges.seo.seo_judge.SentenceTransformer"
    ) as mocked_constructor:
        fake_instance = object()
        mocked_constructor.return_value = fake_instance

        first = seo_judge_module._get_semantic_model()
        second = seo_judge_module._get_semantic_model()

    assert first is fake_instance
    assert second is fake_instance
    assert mocked_constructor.call_count == 1

    seo_judge_module._load_semantic_model.cache_clear()


def test_get_rule_severity_returns_minor_when_rule_is_missing() -> None:
    severity = _get_rule_severity([], "unknown.rule")

    assert severity == "minor"


def test_is_conclusion_title_detects_conclusion() -> None:
    assert _is_conclusion_title("Conclusion") is True
    assert _is_conclusion_title("Section") is False


# ************** Semantic integration **************


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
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=78,
    )

    assert "subscores" in result
    assert "lexical" in result["subscores"]
    assert "semantic" in result["subscores"]
    assert result["subscores"]["semantic"] == 78


def test_run_seo_judge_applies_strong_body_compensation_to_occurrence_issue() -> None:
    content = """
    <p>différenciation éditoriale en milieu saturé.</p>
    <h2>Section</h2>
    <p>Le contenu parle du bon sujet avec coherence de la voix editoriale.</p>
    <h2>Conclusion</h2>
    <p>Conclusion cohérente avec autorite thematique de la marque.</p>
    """

    judge_rules = resolve_seo_rules(_build_context(expected_length="SIMPLE"))
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=80,
    )

    occurrence_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.keyword_occurrences"
    )

    assert occurrence_finding["evidence"]["semantic_body_compensation"] is True
    assert occurrence_finding["evidence"]["body_compensation_level"] == "strong"
    assert occurrence_finding["evidence"]["body_penalty_reduction"] == 10


def test_run_seo_judge_disables_compensation_when_no_keyword_occurrence_exists() -> (
    None
):
    content = """
    <p>Introduction generique.</p>
    <h2>Section</h2>
    <p>Contenu sans le sujet attendu.</p>
    <h2>Conclusion</h2>
    <p>Texte final generique.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=90,
    )

    presence_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.main_keyword_presence"
    )

    assert presence_finding["evidence"]["semantic_body_compensation"] is False
    assert presence_finding["evidence"]["body_compensation_level"] == "none"
    assert presence_finding["evidence"]["body_penalty_reduction"] == 0


def test_run_seo_judge_does_not_compensate_missing_heading_location() -> None:
    content = """
    <p>La différenciation éditoriale en milieu saturé commence ici.</p>
    <h2>Un titre reformulé</h2>
    <p>La coherence de la voix editoriale aide la lecture.</p>
    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé demeure importante.</p>
    """

    judge_rules = resolve_seo_rules(_build_context())
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=82,
    )

    location_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "seo.main_keyword_locations"
    )

    assert "heading_h2_or_h3" in location_finding["evidence"]["missing_locations"]


def test_run_seo_judge_returns_warn_when_no_findings_but_global_score_between_60_and_84() -> (
    None
):
    content = """
    <p>différenciation éditoriale en milieu saturé commence ici.</p>

    <h2>différenciation éditoriale en milieu saturé</h2>
    <p>Texte centré sur le sujet principal.</p>

    <h2>Conclusion</h2>
    <p>différenciation éditoriale en milieu saturé reste lisible.</p>
    """

    context = _build_context(expected_length="SIMPLE")
    context["secondary_keywords"] = []
    context["long_tail_keywords"] = []

    judge_rules = resolve_seo_rules(context)
    judge_rules["keyword_occurrence_rules"]["enforce_minimum_occurrences"] = False
    judge_rules["keyword_distribution_rules"][
        "require_at_least_one_secondary_or_long_tail_per_h2_section"
    ] = False
    judge_rules["keyword_distribution_rules"]["forbid_single_section_concentration"] = (
        False
    )
    preprocessed = preprocess_seo_content(content, judge_rules)
    result = _run_judge_with_semantic_score(
        preprocessed,
        judge_rules,
        semantic_score=0,
        overoptimization_sentence_signals=_empty_overoptimization_sentence_signals(),
    )

    assert result["findings"] == []
    assert result["subscores"]["lexical"] == 100
    assert result["subscores"]["semantic"] == 0
    assert result["score"] == 65
    assert result["status"] == "warn"


# ********************Overoptimization*******************#


def test_compute_overoptimization_sentence_similarities_returns_empty_when_no_keyword() -> (
    None
):
    result = _compute_overoptimization_sentence_similarities(
        {
            "main_keyword": "",
            "total_words": 10,
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "section": "introduction",
                    "sentences": ["Phrase utile."],
                }
            ],
        }
    )

    assert result["main_keyword"] == ""
    assert result["paragraphs"] == []
    assert result["semantic_occurrences"] == 0


def test_compute_overoptimization_sentence_similarities_returns_empty_when_no_paragraphs() -> (
    None
):
    result = _compute_overoptimization_sentence_similarities(
        {
            "main_keyword": "différenciation éditoriale en milieu saturé",
            "total_words": 10,
            "paragraphs": [],
        }
    )

    assert result["paragraphs"] == []
    assert result["semantic_occurrences"] == 0


class _FakeOveroptimizationModel:
    def encode(self, texts, convert_to_tensor=True, normalize_embeddings=True):
        return torch.tensor(
            [
                [1.0, 0.0],  # main keyword
                [0.9, 0.1],  # sentence 1: high similarity
                [0.2, 0.8],  # sentence 2: low similarity
            ],
            dtype=torch.float,
        )


def test_compute_overoptimization_sentence_similarities_scores_sentences() -> None:
    overoptimization_inputs = {
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "total_words": 20,
        "paragraphs": [
            {
                "paragraph_id": 1,
                "section": "introduction",
                "sentences": [
                    {
                        "sentence_id": 1,
                        "text": "Phrase très proche du sujet.",
                        "exact_main_keyword_match": False,
                    },
                    {
                        "sentence_id": 2,
                        "text": "Phrase plus éloignée.",
                        "exact_main_keyword_match": False,
                    },
                ],
            }
        ],
    }

    with patch(
        "contentcreajudge.judges.seo.seo_judge._get_semantic_model",
        return_value=_FakeOveroptimizationModel(),
    ):
        result = _compute_overoptimization_sentence_similarities(
            overoptimization_inputs
        )

    assert result["main_keyword"] == "différenciation éditoriale en milieu saturé"
    assert result["total_words"] == 20
    assert result["similarity_threshold"] == 0.75
    assert result["semantic_occurrences"] == 1

    paragraph = result["paragraphs"][0]
    assert paragraph["paragraph_id"] == 1
    assert paragraph["section"] == "introduction"
    assert len(paragraph["sentence_similarities"]) == 2

    assert paragraph["sentence_similarities"][0]["is_semantic_match"] is True
    assert paragraph["sentence_similarities"][1]["is_semantic_match"] is False


def test_compute_overoptimization_sentence_similarities_skips_invalid_paragraphs_and_empty_sentences() -> (
    None
):
    overoptimization_inputs = {
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "total_words": 20,
        "paragraphs": [
            "not-a-dict",
            {
                "paragraph_id": 1,
                "section": "introduction",
                "sentences": [
                    {
                        "sentence_id": 1,
                        "text": "   ",
                        "exact_main_keyword_match": False,
                    },
                ],
            },
            {
                "paragraph_id": 2,
                "section": "section",
                "sentences": [
                    {
                        "sentence_id": 1,
                        "text": "Phrase valide.",
                        "exact_main_keyword_match": False,
                    },
                ],
            },
        ],
    }

    class _SingleSentenceModel:
        def encode(self, texts, convert_to_tensor=True, normalize_embeddings=True):
            return torch.tensor(
                [
                    [1.0, 0.0],
                    [0.9, 0.1],
                ],
                dtype=torch.float,
            )

    with patch(
        "contentcreajudge.judges.seo.seo_judge._get_semantic_model",
        return_value=_SingleSentenceModel(),
    ):
        result = _compute_overoptimization_sentence_similarities(
            overoptimization_inputs
        )

    assert len(result["paragraphs"]) == 1
    assert result["paragraphs"][0]["paragraph_id"] == 2
    assert result["semantic_occurrences"] == 1


def test_compute_density_score_returns_perfect_score_when_no_words() -> None:
    result = _compute_density_score(
        semantic_occurrences=3,
        total_words=0,
    )

    assert result["density"] == 0.0
    assert result["density_level"] == "none"
    assert result["density_score"] == 100


def test_compute_density_score_returns_low_density() -> None:
    result = _compute_density_score(
        semantic_occurrences=1,
        total_words=100,
    )

    assert result["density"] == 0.01
    assert result["density_level"] == "low"
    assert result["density_score"] == 100


def test_compute_density_score_returns_medium_density() -> None:
    result = _compute_density_score(
        semantic_occurrences=2,
        total_words=53,
    )

    assert result["density"] == 0.0377
    assert result["density_level"] == "medium"
    assert result["density_score"] == 75


def test_compute_density_score_returns_high_density() -> None:
    result = _compute_density_score(
        semantic_occurrences=5,
        total_words=100,
    )

    assert result["density"] == 0.05
    assert result["density_level"] == "high"
    assert result["density_score"] == 45


def test_compute_density_score_returns_very_high_density() -> None:
    result = _compute_density_score(
        semantic_occurrences=8,
        total_words=100,
    )

    assert result["density"] == 0.08
    assert result["density_level"] == "very_high"
    assert result["density_score"] == 20


def test_compute_concentration_score_returns_perfect_score_without_occurrences() -> (
    None
):
    result = _compute_concentration_score(
        {
            "semantic_occurrences": 0,
            "paragraphs": [],
        }
    )

    assert result["paragraphs_with_matches"] == 0
    assert result["concentration_ratio"] == 1.0
    assert result["concentration_level"] == "none"
    assert result["concentration_score"] == 100


def test_compute_concentration_score_returns_low_concentration_when_distributed() -> (
    None
):
    result = _compute_concentration_score(
        {
            "semantic_occurrences": 2,
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                    ],
                },
                {
                    "paragraph_id": 2,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                    ],
                },
            ],
        }
    )

    assert result["paragraphs_with_matches"] == 2
    assert result["concentration_ratio"] == 1.0
    assert result["concentration_level"] == "low"
    assert result["concentration_score"] == 100


def test_compute_concentration_score_returns_medium_concentration() -> None:
    result = _compute_concentration_score(
        {
            "semantic_occurrences": 2,
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                    ],
                },
            ],
        }
    )

    assert result["paragraphs_with_matches"] == 1
    assert result["concentration_ratio"] == 0.5
    assert result["concentration_level"] == "medium"
    assert result["concentration_score"] == 75


def test_compute_concentration_score_returns_high_concentration() -> None:
    result = _compute_concentration_score(
        {
            "semantic_occurrences": 4,
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                    ],
                },
            ],
        }
    )

    assert result["paragraphs_with_matches"] == 1
    assert result["concentration_ratio"] == 0.25
    assert result["concentration_level"] == "high"
    assert result["concentration_score"] == 45


def test_compute_concentration_score_returns_very_high_concentration() -> None:
    result = _compute_concentration_score(
        {
            "semantic_occurrences": 5,
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                    ],
                },
            ],
        }
    )

    assert result["paragraphs_with_matches"] == 1
    assert result["concentration_ratio"] == 0.2
    assert result["concentration_level"] == "very_high"
    assert result["concentration_score"] == 20


def test_compute_local_repetition_score_returns_perfect_score_without_paragraphs() -> (
    None
):
    result = _compute_local_repetition_score(
        {
            "paragraphs": [],
        }
    )

    assert result["max_local_repetition"] == 0
    assert result["local_repetition_level"] == "none"
    assert result["local_repetition_score"] == 100


def test_compute_local_repetition_score_returns_low_when_one_match_per_paragraph() -> (
    None
):
    result = _compute_local_repetition_score(
        {
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": False},
                    ],
                },
                {
                    "paragraph_id": 2,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                    ],
                },
            ],
        }
    )

    assert result["max_local_repetition"] == 1
    assert result["local_repetition_level"] == "low"
    assert result["local_repetition_score"] == 100


def test_compute_local_repetition_score_returns_medium_when_two_matches_in_same_paragraph() -> (
    None
):
    result = _compute_local_repetition_score(
        {
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": False},
                    ],
                }
            ],
        }
    )

    assert result["max_local_repetition"] == 2
    assert result["local_repetition_level"] == "medium"
    assert result["local_repetition_score"] == 75


def test_compute_local_repetition_score_returns_high_when_three_matches_in_same_paragraph() -> (
    None
):
    result = _compute_local_repetition_score(
        {
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                    ],
                }
            ],
        }
    )

    assert result["max_local_repetition"] == 3
    assert result["local_repetition_level"] == "high"
    assert result["local_repetition_score"] == 45


def test_compute_local_repetition_score_returns_very_high_when_four_matches_in_same_paragraph() -> (
    None
):
    result = _compute_local_repetition_score(
        {
            "paragraphs": [
                {
                    "paragraph_id": 1,
                    "sentence_similarities": [
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                        {"is_semantic_match": True},
                    ],
                }
            ],
        }
    )

    assert result["max_local_repetition"] == 4
    assert result["local_repetition_level"] == "very_high"
    assert result["local_repetition_score"] == 20


def test_compute_overoptimization_score_returns_low_risk() -> None:
    result = _compute_overoptimization_score(
        density_signals={
            "density_score": 100,
        },
        concentration_signals={
            "concentration_score": 100,
        },
        local_repetition_signals={
            "local_repetition_score": 100,
        },
        semantic_occurrences=1,
    )

    assert result["overoptimization_score"] == 100
    assert result["overoptimization_risk"] == "low"


def test_compute_overoptimization_score_returns_medium_low_risk() -> None:
    result = _compute_overoptimization_score(
        density_signals={
            "density_score": 75,
        },
        concentration_signals={
            "concentration_score": 75,
        },
        local_repetition_signals={
            "local_repetition_score": 100,
        },
        semantic_occurrences=1,
    )

    assert result["overoptimization_score"] == 81
    assert result["overoptimization_risk"] == "medium_low"


def test_compute_overoptimization_score_returns_medium_high_risk() -> None:
    result = _compute_overoptimization_score(
        density_signals={
            "density_score": 45,
        },
        concentration_signals={
            "concentration_score": 75,
        },
        local_repetition_signals={
            "local_repetition_score": 75,
        },
        semantic_occurrences=1,
    )

    assert result["overoptimization_score"] == 63
    assert result["overoptimization_risk"] == "medium_high"


def test_compute_overoptimization_score_returns_high_risk() -> None:
    result = _compute_overoptimization_score(
        density_signals={
            "density_score": 20,
        },
        concentration_signals={
            "concentration_score": 20,
        },
        local_repetition_signals={
            "local_repetition_score": 20,
        },
        semantic_occurrences=1,
    )

    assert result["overoptimization_score"] == 20
    assert result["overoptimization_risk"] == "high"
