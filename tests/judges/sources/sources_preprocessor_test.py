from __future__ import annotations

from typing import TYPE_CHECKING

import contentcreajudge.preprocessing.sources_preprocessor as sources_module
from contentcreajudge.preprocessing.sources_preprocessor import (
    preprocess_sources_content,
)

if TYPE_CHECKING:
    import pytest


INTERNAL_DOMAIN = "https://contentcrea.com"


def test_preprocess_sources_extracts_html_anchor() -> None:
    """Verify that preprocess sources extracts html anchor."""
    content = """
    <p>Selon <a href="https://example.com/report"
    target="_blank" rel="noopener noreferrer">Example Report</a>,
    le contenu doit être vérifié.</p>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["external_links_count"] == 1
    assert result["body_external_links_count"] == 1
    assert result["complementary_reading_external_links_count"] == 0
    assert result["has_external_links"] is True

    link = result["links"][0]
    assert link["href"] == "https://example.com/report"
    assert link["anchor_text"] == "Example Report"
    assert link["target"] == "_blank"
    assert link["rel"] == "noopener noreferrer"
    assert link["is_external"] is True
    assert link["section"] == "body"


def test_preprocess_sources_detects_internal_link() -> None:
    """Verify that preprocess sources detects internal link."""
    content = """
    <p>Lire aussi <a href="https://contentcrea.com/blog/article"
    target="_blank" rel="noopener noreferrer">un article ContentCrea</a>.</p>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["internal_links_count"] == 1
    assert result["external_links_count"] == 0

    link = result["links"][0]
    assert link["is_internal"] is True
    assert link["is_external"] is False
    assert link["section"] == "body"


def test_preprocess_sources_treats_relative_url_as_internal() -> None:
    """Verify that preprocess sources treats relative url as internal."""
    content = '<p>Voir <a href="/blog/article">un article interne</a>.</p>'

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["internal_links_count"] == 1
    assert result["external_links_count"] == 0

    link = result["links"][0]
    assert link["href"] == "/blog/article"
    assert link["is_internal"] is True
    assert link["is_external"] is False
    assert link["section"] == "body"


def test_preprocess_sources_uses_empty_rel_when_attribute_is_missing() -> None:
    """Verify that preprocess sources uses empty rel when attribute is missing."""
    content = '<p>Voir <a href="https://example.com/report">Example Report</a>.</p>'

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["links"][0]["rel"] == ""


def test_preprocess_sources_casts_scalar_rel_value_to_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that preprocess sources casts scalar rel value to string."""

    class FakeAnchor:
        def get(self, key: str, default: object = None) -> object:
            values = {
                "href": "https://example.com/report",
                "target": "_blank",
                "rel": 123,
            }
            return values.get(key, default)

        def get_text(self, separator: str = " ", strip: bool = True) -> str:
            return "Example Report"

        def find_previous(self, tags: list[str]) -> None:
            return None

        def __str__(self) -> str:
            return (
                '<a href="https://example.com/report" target="_blank" rel="123">'
                "Example Report</a>"
            )

    class FakeSoup:
        def __init__(self, content: str, parser: str) -> None:
            self.content = content
            self.parser = parser

        def find_all(self, tag_name: str) -> list[FakeAnchor]:
            assert tag_name == "a"
            return [FakeAnchor()]

    monkeypatch.setattr(sources_module, "BeautifulSoup", FakeSoup)

    result = preprocess_sources_content("<p>ignored by fake soup</p>", INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["links"][0]["rel"] == "123"
    assert result["links"][0]["section"] == "body"


def test_preprocess_sources_detects_raw_url() -> None:
    """Verify that preprocess sources detects raw url."""
    content = "<p>Voir cette source : https://example.com/report</p>"

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["raw_urls_count"] == 1
    assert result["has_raw_urls"] is True
    assert result["raw_urls"] == ["https://example.com/report"]


def test_preprocess_sources_does_not_count_href_as_raw_url() -> None:
    """Verify that preprocess sources does not count href as raw url."""
    content = """
    <p><a href="https://example.com/report"
    target="_blank" rel="noopener noreferrer">Example Report</a></p>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["raw_urls_count"] == 0
    assert result["has_raw_urls"] is False


def test_preprocess_sources_detects_markdown_link() -> None:
    """Verify that preprocess sources detects markdown link."""
    content = "<p>Voir [Example Report](https://example.com/report)</p>"

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["markdown_links_count"] == 1
    assert result["has_markdown_links"] is True


def test_preprocess_sources_detects_attached_anchor() -> None:
    """Verify that preprocess sources detects attached anchor."""
    content = """
    <p>objectifs<a href="https://example.com/report"
    target="_blank" rel="noopener noreferrer">Example Report</a></p>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["attached_anchor_count"] == 1
    assert result["has_attached_anchors"] is True


def test_preprocess_sources_handles_escaped_html_quotes() -> None:
    """Verify that preprocess sources handles escaped html quotes."""
    content = (
        '<p>Selon <a href=\\"https://example.com/report\\" '
        'target=\\"_blank\\" rel=\\"noopener noreferrer\\">'
        "Example Report</a>.</p>"
    )

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["links_count"] == 1
    assert result["external_links_count"] == 1

    link = result["links"][0]
    assert link["href"] == "https://example.com/report"
    assert link["target"] == "_blank"
    assert link["rel"] == "noopener noreferrer"


def test_preprocess_sources_marks_body_external_link() -> None:
    """Verify that preprocess sources marks body external link."""
    content = """
    <p>Selon <a href="https://example.com/report"
    target="_blank" rel="noopener noreferrer">Example Report</a>.</p>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["body_external_links_count"] == 1
    assert result["complementary_reading_external_links_count"] == 0
    assert result["links"][0]["section"] == "body"


def test_preprocess_sources_detects_complementary_reading_link() -> None:
    """Verify that preprocess sources detects complementary reading link."""
    content = """
    <p>Texte principal sans source.</p>
    <h2>Lecture complémentaire</h2>
    <ul>
      <li><a href="https://liris.cnrs.fr/mediation-scientifique">
      Médiation scientifique</a></li>
    </ul>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["external_links_count"] == 1
    assert result["body_external_links_count"] == 0
    assert result["complementary_reading_links_count"] == 1
    assert result["complementary_reading_external_links_count"] == 1
    assert result["links"][0]["section"] == "complementary_reading"


def test_preprocess_sources_detects_learn_more_section() -> None:
    """Verify that preprocess sources detects learn more section."""
    content = """
    <p>Main content.</p>
    <h2>Learn more</h2>
    <ul>
      <li><a href="https://example.com/resource">Resource</a></li>
    </ul>
    """

    result = preprocess_sources_content(content, INTERNAL_DOMAIN)

    assert result["body_external_links_count"] == 0
    assert result["complementary_reading_external_links_count"] == 1
    assert result["links"][0]["section"] == "complementary_reading"
