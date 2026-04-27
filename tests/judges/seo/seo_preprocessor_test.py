from __future__ import annotations

from contentcreajudge.preprocessing.seo_preprocessor import (
    _filter_keyphrases,
    preprocess_seo_content,
    _clean_keyphrases,
    _extract_candidate_keyphrases,
    _get_spacy_model,
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
    assert lexical["secondary_keyword_occurrences"]["coherence de la voix editoriale"] == 1
    assert lexical["long_tail_keyword_occurrences"][
        "repetition strategique du message sans impression de deja-vu en b2b"
    ] == 0


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
    assert lexical["secondary_keyword_occurrences"]["coherence de la voix editoriale"] == 0
    assert lexical["forbidden_keyword_emphasis"] == []

def test_preprocess_seo_content_extracts_keyphrases() -> None:
    content = """
    <p>Construire une ligne éditoriale cohérente permet de se démarquer et de renforcer l’autorité de la marque.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    keyphrases = result["thematic_signals"]["keyphrases"]

    assert len(keyphrases) > 0

    phrases = [kp["keyphrase"] for kp in keyphrases]

    assert any("ligne éditoriale" in phrase or "ligne editoriale" in phrase for phrase in phrases)

def test_preprocess_seo_content_handles_empty_keyphrases() -> None:
    result = preprocess_seo_content("", _build_judge_rules())

    assert result["thematic_signals"]["keyphrases"] == []

def test_preprocess_seo_content_filters_low_score_keyphrases() -> None:
    content = "<p>texte très simple</p>"

    result = preprocess_seo_content(content, _build_judge_rules())
    keyphrases = result["thematic_signals"]["keyphrases"]

    assert all(kp["score"] >= 0.3 for kp in keyphrases)


def test_filter_keyphrases_removes_low_scores() -> None:
    raw_keyphrases = [
        {"keyphrase": "ligne editoriale", "score": 0.65},
        {"keyphrase": "autorite marque", "score": 0.30},
        {"keyphrase": "contenu seo", "score": 0.12},
    ]

    filtered = _filter_keyphrases(raw_keyphrases)

    assert filtered == [
        {"keyphrase": "ligne editoriale", "score": 0.65},
        {"keyphrase": "autorite marque", "score": 0.30},
    ]

#***Test if the conclusion is taken into account and that Learn more section is no longer taken into account***#
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

#***Test if keyphrases are formed without stopwords***#
def test_clean_keyphrases_removes_noisy_phrases() -> None:
    raw_keyphrases = [
        {"keyphrase": "intelligence artificielle doit", "score": 0.75},
        {"keyphrase": "de intelligence artificielle", "score": 0.70},
        {"keyphrase": "intelligence artificielle", "score": 0.65},
        {"keyphrase": "apprentissage automatique", "score": 0.60},
    ]

    result = _clean_keyphrases(raw_keyphrases)

    phrases = [kp["keyphrase"] for kp in result]

    assert "intelligence artificielle doit" not in phrases
    assert "de intelligence artificielle" not in phrases
    assert "intelligence artificielle" in phrases
    assert "apprentissage automatique" in phrases

def test_clean_keyphrases_deduplicates_exact_phrases() -> None:
    raw_keyphrases = [
        {"keyphrase": "intelligence artificielle", "score": 0.80},
        {"keyphrase": "intelligence artificielle", "score": 0.75},
        {"keyphrase": "apprentissage automatique", "score": 0.60},
    ]

    result = _clean_keyphrases(raw_keyphrases)

    phrases = [kp["keyphrase"] for kp in result]

    assert phrases.count("intelligence artificielle") == 1
    assert "apprentissage automatique" in phrases

def test_preprocess_seo_content_returns_cleaned_keyphrases() -> None:
    content = """
    <p>La place de l’intelligence artificielle dans la recherche dépend du rôle du modèle.
    L’apprentissage automatique peut être un outil d’analyse.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    keyphrases = result["thematic_signals"]["keyphrases"]

    phrases = [kp["keyphrase"] for kp in keyphrases]

    assert all(not phrase.endswith(("doit", "peut", "dans")) for phrase in phrases)
    assert all(not phrase.startswith(("de ", "dans ", "in ", "the ")) for phrase in phrases)

def test_clean_keyphrases_removes_english_noisy_phrases() -> None:
    raw_keyphrases = [
        {"keyphrase": "artificial intelligence is", "score": 0.75},
        {"keyphrase": "in artificial intelligence", "score": 0.70},
        {"keyphrase": "artificial intelligence", "score": 0.65},
        {"keyphrase": "machine learning", "score": 0.60},
    ]

    result = _clean_keyphrases(raw_keyphrases)

    phrases = [kp["keyphrase"] for kp in result]

    assert "artificial intelligence is" not in phrases
    assert "in artificial intelligence" not in phrases
    assert "artificial intelligence" in phrases
    assert "machine learning" in phrases


def test_clean_keyphrases_trims_noisy_trailing_words() -> None:
    raw_keyphrases = [
        {"keyphrase": "souverainete numerique comme", "score": 0.72},
        {"keyphrase": "souverainete numerique prend", "score": 0.71},
        {"keyphrase": "infrastructures numeriques", "score": 0.69},
    ]

    result = _clean_keyphrases(raw_keyphrases)
    phrases = [kp["keyphrase"] for kp in result]

    assert "souverainete numerique" in phrases
    assert "infrastructures numeriques" in phrases
    assert "souverainete numerique comme" not in phrases
    assert "souverainete numerique prend" not in phrases


def test_extract_candidate_keyphrases_excludes_grammatical_noise() -> None:
    doc = _get_spacy_model()(
        "La souverainete numerique prend de l importance. "
        "Les infrastructures numeriques comme les plateformes cloud "
        "demeurent critiques dans des contextes numeriques lorsque "
        "la pression technologique augmente."
    )

    candidates = _extract_candidate_keyphrases(doc)

    assert "souverainete numerique prend" not in candidates
    assert "infrastructures numeriques comme" not in candidates
    assert "contextes numeriques lorsque" not in candidates
    assert any("souverainete numerique" == candidate for candidate in candidates)

def test_extract_keyphrases_returns_clean_ranked_candidates() -> None:
    content = """
    <p>La souverainete numerique repose sur des infrastructures numeriques robustes
    et sur une meilleure maitrise des contraintes technologiques.</p>
    """

    result = preprocess_seo_content(content, _build_judge_rules())
    keyphrases = result["thematic_signals"]["keyphrases"]

    phrases = [kp["keyphrase"] for kp in keyphrases]

    assert len(keyphrases) > 0
    assert any("souverainete numerique" in phrase for phrase in phrases)
    assert any("infrastructures numeriques" in phrase for phrase in phrases)
