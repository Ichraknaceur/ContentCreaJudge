from contentcreajudge.preprocessing.persona_preprocessor import (
    preprocess_persona_content,
)


def test_preprocess_persona_content_normalizes_html() -> None:
    result = preprocess_persona_content(
        content="<p>Bonjour&nbsp;!</p>",
        context={"personas": []},
    )

    assert result["normalized_text"] == "Bonjour !"


def test_preprocess_persona_content_normalizes_platform_persona() -> None:
    result = preprocess_persona_content(
        content="Contenu test",
        context={
            "personas": [
                {
                    "uuid": "persona-1",
                    "data": {
                        "firstName": "Marc",
                        "function": "Responsable innovation",
                        "personaFields": {
                            "professionalObjectives": "Identifier des opportunités.",
                            "problemsFrustrations": "Manque de cas d'usage.",
                        },
                    },
                }
            ],
            "expected_persona_id": "persona-1",
            "business_type": "B2B",
        },
    )

    persona = result["personas"][0]

    assert persona["persona_id"] == "persona-1"
    assert persona["first_name"] == "Marc"
    assert persona["function"] == "Responsable innovation"
    assert persona["persona_fields"]["professional_objectives"] == (
        "Identifier des opportunités."
    )


def test_preprocess_persona_content_ignores_invalid_personas() -> None:
    result = preprocess_persona_content(
        content="Contenu test",
        context={
            "personas": [
                "invalid",
                {"data": {"function": "Sans id"}},
                {"uuid": "valid-id", "data": {"function": "Doctorant"}},
            ]
        },
    )

    assert len(result["personas"]) == 1
    assert result["personas"][0]["persona_id"] == "valid-id"
