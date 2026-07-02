from __future__ import annotations

from contentcreajudge.preprocessing.orchestration.global_preprocessor import (
    preprocess_global_content,
)


def test_preprocess_global_content_extracts_shared_signals() -> None:
    content = """
    <p>Introduction de test avec un lien brut https://example.org.</p>
    <h2>Première section</h2>
    <p>Paragraphe avec <a href="https://example.com" target="_blank" rel="noopener noreferrer">source externe</a>.</p>
    <h3>Sous-section</h3>
    <p>Texte de sous-section.</p>
    <p class="cta"><strong>Read more</strong></p>
    <h2>Conclusion</h2>
    <p>Conclusion de test.</p>
    """

    result = preprocess_global_content(content)

    assert result["is_empty"] is False
    assert result["word_count"] > 0
    assert result["normalized_text"]

    assert result["introduction"] == (
        "Introduction de test avec un lien brut https://example.org."
    )
    assert result["conclusion"] == "Conclusion de test."

    assert result["headings_h2_h3"] == [
        "Première section",
        "Sous-section",
        "Conclusion",
    ]

    assert len(result["h2_sections"]) == 2
    assert result["h2_sections"][0]["h2"] == "Première section"

    links = result["links"]
    assert isinstance(links, dict)
    assert links["links_count"] == 1
    assert links["external_links_count"] == 1
    assert links["raw_urls_count"] == 1
    assert links["has_raw_urls"] is True

    cta = result["cta"]
    assert isinstance(cta, dict)
    assert cta["has_cta"] is True
    assert cta["cta_count"] == 1
    assert cta["cta_texts"] == ["Read more"]

    structure = result["structure"]
    assert isinstance(structure, dict)
    assert structure["has_h1"] is False
    assert structure["has_script"] is False
    assert structure["has_span"] is False

    typography = result["typography"]
    assert isinstance(typography, dict)
    assert typography["anchor_tag_count"] == 1


def test_preprocess_global_content_handles_empty_content() -> None:
    result = preprocess_global_content("")

    assert result["is_empty"] is True
    assert result["word_count"] == 0
    assert result["normalized_text"] == ""
    assert result["paragraphs"] == []
    assert result["headings"] == []
    assert result["h2_sections"] == []

    links = result["links"]
    assert isinstance(links, dict)
    assert links["links_count"] == 0
    assert links["raw_urls_count"] == 0

    cta = result["cta"]
    assert isinstance(cta, dict)
    assert cta["has_cta"] is False
