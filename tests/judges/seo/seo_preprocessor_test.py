from __future__ import annotations

from contentcreajudge.core.errors import ConfigurationError
from contentcreajudge.preprocessing.seo_preprocessor import (
    _build_semantic_body_text,
    _build_semantic_chunks,
    preprocess_seo_content,
    _build_overoptimization_inputs,
    _build_overoptimization_paragraphs,
    _split_text_into_sentences,
)


def _build_judge_rules() -> dict[str, object]:
    return {
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "secondary_keywords": [
            "coherence de la voix editoriale",
            "autorite thematique de la marque",
        ],
        "long_tail_keywords": [
            "repetition strategique du message sans impression de deja-vu en b2b",
        ],
        "formatting_constraints_rules": {
            "forbid_emphasis_tags_on_keywords": ["em", "strong"],
        },
    }


def test_preprocess_seo_content_extracts_zones() -> None:
    content = """
    <p>Introduction part 1.</p>
    <p>Introduction part 2.</p>

    <h2>First section</h2>
    <p>First section paragraph.</p>
    <h3>First subsection</h3>
    <p>First subsection paragraph.</p>

    <h2>Conclusion</h2>
    <p>Final thoughts here.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["is_empty"] is False
    assert result["introduction"] == "Introduction part 1. Introduction part 2."
    assert result["headings_h2_h3"] == [
        "First section",
        "First subsection",
        "Conclusion",
    ]
    assert result["conclusion"] == "Final thoughts here."
    assert len(result["h2_sections"]) == 2

    assert result["h2_sections"][0]["h2"] == "First section"
    assert result["h2_sections"][0]["h3_headings"] == ["First subsection"]
    assert "First section paragraph." in result["h2_sections"][0]["text"]
    assert "First subsection paragraph." in result["h2_sections"][0]["text"]

    assert result["h2_sections"][1]["h2"] == "Conclusion"
    assert result["h2_sections"][1]["h3_headings"] == []
    assert result["h2_sections"][1]["text"] == "Final thoughts here."


def test_preprocess_seo_content_extracts_explicit_conclusion_before_read_more() -> None:
    content = """
    <p>Introduction generale.</p>

    <h2>Section 1</h2>
    <p>Contenu de section.</p>

    <h2>Conclusion</h2>
    <p>La place de l intelligence artificielle doit etre explicitee avec precision.</p>

    <h2>Lecture complémentaire</h2>
    <ul>
      <li><a href="https://example.com">Lien utile</a></li>
    </ul>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["conclusion"] == (
        "La place de l intelligence artificielle doit etre explicitee avec precision."
    )


def test_preprocess_seo_content_falls_back_to_last_non_utility_h2_section() -> None:
    content = """
    <p>Introduction generale.</p>

    <h2>Section 1</h2>
    <p>Premier passage.</p>

    <h2>Derniere vraie section</h2>
    <p>Texte final important.</p>

    <h2>Lecture complémentaire</h2>
    <p>Passage annexe.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["conclusion"] == "Texte final important."


def test_preprocess_seo_content_falls_back_to_last_h2_when_all_h2_are_utility_sections() -> (
    None
):
    content = """
    <p>Introduction generale.</p>

    <h2>Learn more</h2>
    <p>Passage annexe utilise comme dernier recours.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["conclusion"] == "Passage annexe utilise comme dernier recours."


def test_preprocess_seo_content_returns_empty_conclusion_when_no_h2() -> None:
    content = """
    <p>Seulement un paragraphe.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["conclusion"] == ""


def test_preprocess_seo_content_handles_content_without_h2() -> None:
    content = """
    <p>Only one paragraph.</p>
    <p>Another paragraph.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["introduction"] == "Only one paragraph. Another paragraph."
    assert result["headings_h2_h3"] == []
    assert result["h2_sections"] == []
    assert result["conclusion"] == ""
    assert result["body_text"] == "Only one paragraph. Another paragraph."
    assert result["is_empty"] is False


def test_preprocess_seo_content_detects_empty_content() -> None:
    content = ""

    result = preprocess_seo_content(content, _build_judge_rules())

    assert result["introduction"] == ""
    assert result["headings_h2_h3"] == []
    assert result["h2_sections"] == []
    assert result["conclusion"] == ""
    assert result["body_text"] == ""
    assert result["is_empty"] is True


def test_preprocess_seo_content_extracts_lexical_signals() -> None:
    content = """
    <p>La différenciation éditoriale en milieu saturé commence des l'introduction.</p>

    <h2>Clarifier la strategie</h2>
    <p>La coherence de la voix editoriale structure la lecture.</p>

    <h2>Conclusion</h2>
    <p>La différenciation éditoriale en milieu saturé demeure un repère utile.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    lexical = result["lexical_signals"]

    assert lexical["main_keyword_presence"]["body"] is True
    assert lexical["main_keyword_presence"]["introduction"] is True
    assert lexical["main_keyword_presence"]["headings_h2_h3"] is False
    assert lexical["main_keyword_presence"]["conclusion"] is True

    assert lexical["main_keyword_occurrences"]["body"] == 2
    assert (
        lexical["secondary_keyword_occurrences"]["coherence de la voix editoriale"] == 1
    )
    assert (
        lexical["long_tail_keyword_occurrences"][
            "repetition strategique du message sans impression de deja-vu en b2b"
        ]
        == 0
    )


def test_preprocess_seo_content_builds_section_distribution() -> None:
    content = """
    <p>Introduction generale.</p>

    <h2>Section 1</h2>
    <p>La coherence de la voix editoriale est importante.</p>

    <h2>Section 2</h2>
    <p>Texte generique sans mot-cle secondaire.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    distribution = result["lexical_signals"]["section_distribution"]

    assert len(distribution) == 2
    assert distribution[0]["has_secondary_or_long_tail"] is True
    assert distribution[1]["has_secondary_or_long_tail"] is False
    assert result["lexical_signals"]["single_section_concentration_detected"] is True


def test_preprocess_seo_content_detects_forbidden_keyword_emphasis() -> None:
    content = """
    <p><strong>différenciation éditoriale en milieu saturé</strong></p>
    <h2>Section</h2>
    <p><em>coherence de la voix editoriale</em></p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    forbidden = result["lexical_signals"]["forbidden_keyword_emphasis"]

    assert len(forbidden) == 2
    assert forbidden[0]["tag"] in {"strong", "em"}
    assert forbidden[1]["tag"] in {"strong", "em"}


def test_preprocess_seo_content_handles_absent_keywords() -> None:
    content = """
    <p>Introduction generique.</p>
    <h2>Section</h2>
    <p>Contenu sans les expressions attendues.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    lexical = result["lexical_signals"]

    assert lexical["main_keyword_presence"]["body"] is False
    assert lexical["main_keyword_occurrences"]["body"] == 0
    assert (
        lexical["secondary_keyword_occurrences"]["coherence de la voix editoriale"] == 0
    )
    assert lexical["forbidden_keyword_emphasis"] == []


# ***Test if the conclusion is taken into account and that Learn more section is no longer taken into account***#
def test_preprocess_seo_content_excludes_utility_sections_from_distribution() -> None:
    content = """
    <p>Introduction generale.</p>

    <h2>Section 1</h2>
    <p>La coherence de la voix editoriale est presente ici.</p>

    <h2>Lecture complémentaire</h2>
    <p>Passage annexe sans mot-cle.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    distribution = result["lexical_signals"]["section_distribution"]

    assert len(distribution) == 1
    assert distribution[0]["h2"] == "Section 1"


def test_preprocess_seo_content_keeps_conclusion_in_distribution() -> None:
    content = """
    <p>Introduction generale.</p>

    <h2>Section 1</h2>
    <p>La coherence de la voix editoriale est presente ici.</p>

    <h2>Conclusion</h2>
    <p>Texte final sans mot-cle secondaire.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    distribution = result["lexical_signals"]["section_distribution"]

    assert len(distribution) == 2
    assert distribution[0]["h2"] == "Section 1"
    assert distribution[1]["h2"] == "Conclusion"


def test_preprocess_seo_content_excludes_sources_from_distribution() -> None:
    content = """
    <p>Introduction generale.</p>

    <h2>Section principale</h2>
    <p>La coherence de la voix editoriale est importante.</p>

    <h2>Sources</h2>
    <ul>
      <li>https://example.com/source-1</li>
    </ul>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    distribution = result["lexical_signals"]["section_distribution"]

    assert len(distribution) == 1
    assert distribution[0]["h2"] == "Section principale"


# *********************Chunking****************#
def test_build_semantic_chunks_returns_empty_list_for_empty_text() -> None:
    chunks = _build_semantic_chunks("")

    assert chunks == []


def test_build_semantic_chunks_creates_one_chunk_for_short_text() -> None:
    text = "un deux trois quatre cinq"

    chunks = _build_semantic_chunks(
        body_text=text,
        chunk_size=128,
        overlap=20,
    )

    assert len(chunks) == 1
    assert chunks[0]["chunk_id"] == 1
    assert chunks[0]["text"] == text
    assert chunks[0]["start_word"] == 0
    assert chunks[0]["end_word"] == 5
    assert chunks[0]["word_count"] == 5


def test_build_semantic_chunks_creates_overlapping_chunks() -> None:
    words = [f"mot{i}" for i in range(1, 14)]
    text = " ".join(words)

    chunks = _build_semantic_chunks(
        body_text=text,
        chunk_size=8,
        overlap=3,
    )

    assert len(chunks) == 2

    assert chunks[0]["text"] == "mot1 mot2 mot3 mot4 mot5 mot6 mot7 mot8"
    assert chunks[0]["start_word"] == 0
    assert chunks[0]["end_word"] == 8
    assert chunks[0]["word_count"] == 8

    assert chunks[1]["text"] == "mot6 mot7 mot8 mot9 mot10 mot11 mot12 mot13"
    assert chunks[1]["start_word"] == 5
    assert chunks[1]["end_word"] == 13
    assert chunks[1]["word_count"] == 8


def test_build_semantic_chunks_rejects_invalid_chunk_size() -> None:
    try:
        _build_semantic_chunks(
            body_text="un deux trois",
            chunk_size=0,
            overlap=0,
        )
    except ConfigurationError as exc:
        assert str(exc) == "chunk_size must be greater than 0."
    else:
        raise AssertionError("Expected ConfigurationError")


def test_build_semantic_chunks_rejects_negative_overlap() -> None:
    try:
        _build_semantic_chunks(
            body_text="un deux trois",
            chunk_size=8,
            overlap=-1,
        )
    except ConfigurationError as exc:
        assert str(exc) == "overlap must be greater than or equal to 0."
    else:
        raise AssertionError("Expected ConfigurationError")


def test_build_semantic_chunks_rejects_overlap_equal_to_chunk_size() -> None:
    try:
        _build_semantic_chunks(
            body_text="un deux trois",
            chunk_size=8,
            overlap=8,
        )
    except ConfigurationError as exc:
        assert str(exc) == "overlap must be smaller than chunk_size."
    else:
        raise AssertionError("Expected ConfigurationError")


def test_preprocess_seo_content_builds_new_semantic_inputs_with_chunks() -> None:
    content = """
    <p>Introduction generale avec un premier paragraphe.</p>
    <h2>Section principale</h2>
    <p>La différenciation éditoriale en milieu saturé demande une lecture claire du positionnement.</p>
    <p>Elle permet de structurer les messages et de garder une voix cohérente dans le temps.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    semantic_inputs = result["semantic_inputs"]

    assert (
        semantic_inputs["main_keyword"] == "différenciation éditoriale en milieu saturé"
    )
    assert semantic_inputs["chunk_size"] == 128
    assert semantic_inputs["chunk_overlap"] == 16
    assert isinstance(semantic_inputs["chunks"], list)
    assert len(semantic_inputs["chunks"]) == 1
    assert (
        "différenciation éditoriale en milieu saturé"
        in semantic_inputs["chunks"][0]["text"]
    )


def test_preprocess_seo_content_does_not_return_old_semantic_inputs() -> None:
    result = preprocess_seo_content("", _build_judge_rules())
    semantic_inputs = result["semantic_inputs"]

    assert "main_keyword_query" not in semantic_inputs
    assert "keyword_cluster_query" not in semantic_inputs
    assert "introduction_passage" not in semantic_inputs
    assert "conclusion_passage" not in semantic_inputs
    assert "heading_passages" not in semantic_inputs
    assert "body_passage" not in semantic_inputs
    assert "section_passages" not in semantic_inputs


def test_preprocess_seo_content_does_not_return_thematic_signals_anymore() -> None:
    result = preprocess_seo_content("", _build_judge_rules())

    assert "thematic_signals" not in result


def test_build_semantic_body_text_excludes_utility_sections() -> None:
    introduction = "Introduction utile."

    h2_sections = [
        {
            "h2": "Section principale",
            "h3_headings": [],
            "text": "Texte principal utile.",
        },
        {
            "h2": "Lecture complémentaire",
            "h3_headings": [],
            "text": "Texte annexe à exclure.",
        },
        {
            "h2": "Sources",
            "h3_headings": [],
            "text": "Source à exclure.",
        },
    ]

    result = _build_semantic_body_text(
        introduction=introduction,
        h2_sections=h2_sections,
        body_text="Fallback complet.",
    )

    assert "Introduction utile." in result
    assert "Section principale. Texte principal utile." in result
    assert "Texte annexe à exclure." not in result
    assert "Source à exclure." not in result


def test_build_semantic_body_text_skips_empty_sections_and_keeps_untitled_text() -> (
    None
):
    result = _build_semantic_body_text(
        introduction="",
        h2_sections=[
            {
                "h2": "Section vide",
                "h3_headings": [],
                "text": "",
            },
            {
                "h2": "",
                "h3_headings": [],
                "text": "Texte sans titre conserve.",
            },
            {
                "h2": "Section titree",
                "h3_headings": [],
                "text": "Texte avec titre conserve.",
            },
        ],
        body_text="Fallback complet.",
    )

    assert result == (
        "Texte sans titre conserve. Section titree. Texte avec titre conserve."
    )


def test_build_semantic_body_text_falls_back_to_body_text_when_no_semantic_parts() -> (
    None
):
    result = _build_semantic_body_text(
        introduction="",
        h2_sections=[
            {
                "h2": "Lecture complémentaire",
                "h3_headings": [],
                "text": "Texte utilitaire seulement.",
            }
        ],
        body_text="Texte complet de secours.",
    )

    assert result == "Texte complet de secours."


def test_preprocess_seo_content_returns_semantic_body_text_without_utility_sections() -> (
    None
):
    content = """
    <p>Introduction utile.</p>

    <h2>Section principale</h2>
    <p>La différenciation éditoriale en milieu saturé est expliquée ici.</p>

    <h2>Lecture complémentaire</h2>
    <p>Ce passage ne doit pas être utilisé dans le texte sémantique.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())

    assert "semantic_body_text" in result
    assert "Introduction utile." in result["semantic_body_text"]
    assert "Section principale." in result["semantic_body_text"]
    assert "différenciation éditoriale en milieu saturé" in result["semantic_body_text"]
    assert "Ce passage ne doit pas être utilisé" not in result["semantic_body_text"]


def test_split_text_into_sentences_splits_simple_sentences() -> None:
    text = "Première phrase. Deuxième phrase ! Troisième phrase ?"

    result = _split_text_into_sentences(text)

    assert result == [
        "Première phrase.",
        "Deuxième phrase !",
        "Troisième phrase ?",
    ]


def test_build_overoptimization_paragraphs_excludes_utility_sections() -> None:
    introduction = "Introduction utile."

    h2_sections = [
        {
            "h2": "Section principale",
            "h3_headings": [],
            "text": "Phrase utile. Autre phrase utile.",
        },
        {
            "h2": "Lecture complémentaire",
            "h3_headings": [],
            "text": "Texte annexe à exclure.",
        },
    ]

    paragraphs = _build_overoptimization_paragraphs(
        main_keyword="diffÃ©renciation Ã©ditoriale en milieu saturÃ©",
        introduction=introduction,
        h2_sections=h2_sections,
    )

    assert len(paragraphs) == 2
    assert paragraphs[0]["section"] == "introduction"
    assert paragraphs[1]["section"] == "Section principale"
    assert "Texte annexe à exclure." not in [
        paragraph["text"] for paragraph in paragraphs
    ]


def test_build_overoptimization_inputs_returns_main_keyword_and_total_words() -> None:
    result = _build_overoptimization_inputs(
        main_keyword="la place de l'intelligence artificielle",
        introduction="Introduction utile.",
        h2_sections=[
            {
                "h2": "Section principale",
                "h3_headings": [],
                "text": "Phrase utile pour analyser le sujet.",
            }
        ],
        body_text="Fallback body text.",
    )

    assert result["main_keyword"] == "la place de l'intelligence artificielle"
    assert result["total_words"] > 0
    assert len(result["paragraphs"]) == 2


def test_preprocess_seo_content_builds_overoptimization_inputs() -> None:
    content = """
    <p>Introduction utile sur la différenciation éditoriale en milieu saturé.</p>

    <h2>Section principale</h2>
    <p>Une phrase utile. Une autre phrase utile.</p>

    <h2>Lecture complémentaire</h2>
    <p>Texte annexe à exclure.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    overoptimization_inputs = result["overoptimization_inputs"]

    assert overoptimization_inputs["main_keyword"] == (
        "différenciation éditoriale en milieu saturé"
    )
    assert overoptimization_inputs["total_words"] > 0
    assert len(overoptimization_inputs["paragraphs"]) == 2
    assert all(
        paragraph["section"] != "Lecture complémentaire"
        for paragraph in overoptimization_inputs["paragraphs"]
    )
