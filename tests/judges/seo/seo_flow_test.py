from __future__ import annotations

from contentcreajudge.application.judge_flow.seo_flow import execute_seo_flow


def _build_payload() -> dict[str, object]:
    return {
        "content": """
        <p>La différenciation éditoriale en milieu saturé commence ici.</p>

        <h2>différenciation éditoriale en milieu saturé</h2>
        <p>La coherence de la voix editoriale améliore la lisibilite.</p>

        <h2>Construire un repère stable</h2>
        <p>L autorite thematique de la marque se construit aussi par la différenciation éditoriale en milieu saturé.</p>

        <h2>Conclusion</h2>
        <p>La différenciation éditoriale en milieu saturé demeure un repère stable
        pour l autorite thematique de la marque et repetition strategique du message sans impression de deja-vu en b2b.</p>
        """,
        "profile": "default",
        "request_id": "seo-test-001",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "funnel_stage": "AWARENESS",
            "locale": "fr-FR",
            "main_keyword": "différenciation éditoriale en milieu saturé",
            "secondary_keywords": [
                "coherence de la voix editoriale",
                "autorite thematique de la marque",
            ],
            "long_tail_keywords": [
                "repetition strategique du message sans impression de deja-vu en b2b",
            ],
        },
    }


def test_execute_seo_flow_returns_full_pipeline_response() -> None:
    result = execute_seo_flow(_build_payload())

    assert "request_echo" in result
    assert "rule_resolution" in result
    assert "preprocessing" in result
    assert "judge_result" in result
    assert "aggregation" in result
    assert "message" in result

    assert result["request_echo"]["request_id"] == "seo-test-001"
    assert result["rule_resolution"]["enabled_judges"] == ["seo"]
    assert result["judge_result"]["dimension"] == "seo"
    assert result["aggregation"]["status"] in {"pass", "warn", "fail"}
