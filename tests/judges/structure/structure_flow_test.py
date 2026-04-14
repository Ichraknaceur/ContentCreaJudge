from contentcreajudge.application.judge_flow.structure_flow import (
    execute_structure_flow,
)


def test_execute_structure_flow_passes_with_valid_structure() -> None:
    payload = {
        "content": """
        <p>Introduction générée.</p>
        <h2>Section A</h2>
        <p>Contenu</p>
        <h3>Sous-section A.1</h3>
        <p>Contenu</p>
        <h2>Conclusion</h2>
        <p>Contenu final</p>
        """,
        "profile": "default",
        "context": {
            "expected_outline_html": """
            <p>Introduction attendue.</p>
            <h2>Section A</h2>
            <p>Texte</p>
            <h3>Sous-section A.1</h3>
            <p>Texte</p>
            <h2>Conclusion</h2>
            <p>Texte final</p>
            """,
            "locale": "fr-FR",
        },
    }

    result = execute_structure_flow(payload)

    assert result["request_echo"]["profile"] == "default"
    assert result["rule_resolution"]["enabled_judges"] == ["structure"]
    assert result["judge_result"]["dimension"] == "structure"
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"
    assert result["aggregation"]["score"] == 100

 
def test_execute_structure_flow_fails_with_invalid_structure() -> None:
    payload = {
        "content": """
        <h1>Titre interdit</h1>
        <p>Introduction générée.</p>
        <h2>Section A</h2>
        <h2>Sous-section A.1</h2>
        <script>alert('x')</script>
        """,
        "profile": "default",
        "context": {
            "expected_outline_html": """
            <p>Introduction attendue.</p>
            <h2>Section A</h2>
            <h3>Sous-section A.1</h3>
            """,
            "locale": "fr-FR",
        },
    }

    result = execute_structure_flow(payload)

    assert result["judge_result"]["status"] == "fail"
    assert result["aggregation"]["status"] == "fail"

    rule_ids = {finding["rule_id"] for finding in result["judge_result"]["findings"]}

    assert "structure.no_h1_in_body" in rule_ids
    assert "structure.heading_levels" in rule_ids
    assert "structure.no_scripts" in rule_ids