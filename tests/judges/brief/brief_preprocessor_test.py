from contentcreajudge.preprocessing.brief_preprocessor import (
    preprocess_brief_content,
)


def test_preprocess_brief_content_removes_html_from_article() -> None:
    result = preprocess_brief_content(
        article="<p>Bonjour <strong>le monde</strong></p>",
        brief="Angle et message central : test",
    )

    assert result["article_text"] == "Bonjour le monde"


def test_preprocess_brief_content_counts_article_words() -> None:
    result = preprocess_brief_content(
        article="<p>Un deux trois</p>",
        brief="Brief test",
    )

    assert result["article_word_count"] == 3


def test_preprocess_brief_content_detects_empty_article() -> None:
    result = preprocess_brief_content(
        article="   ",
        brief="Brief test",
    )

    assert result["is_article_empty"] is True


def test_preprocess_brief_content_detects_empty_brief() -> None:
    result = preprocess_brief_content(
        article="Article test",
        brief="   ",
    )

    assert result["is_brief_empty"] is True


def test_preprocess_brief_content_decodes_html_entities() -> None:
    result = preprocess_brief_content(
        article="<p>L&rsquo;IA et la recherche</p>",
        brief="Angle &amp; message",
    )

    assert result["article_text"] == "L\u2019IA et la recherche"
    assert result["normalized_brief"] == "Angle & message"
