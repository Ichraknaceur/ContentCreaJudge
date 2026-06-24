from contentcreajudge.judges.persona.persona_prompt import (
    build_persona_judge_prompt,
)


def test_persona_prompt_contains_v2_title() -> None:
    prompt = build_persona_judge_prompt("Contenu test", {"persona": {}})

    assert "PERSONA JUDGE PROMPT" in prompt


def test_persona_prompt_contains_content() -> None:
    prompt = build_persona_judge_prompt("Contenu test", {"persona": {}})

    assert "Contenu test" in prompt


def test_persona_prompt_contains_expected_json_contract() -> None:
    prompt = build_persona_judge_prompt("Contenu test", {"persona": {}})

    assert '"dimension": "persona"' in prompt
    assert '"criteria_scores"' in prompt
    assert '"identified_persona_elements"' in prompt
    assert '"findings"' in prompt


def test_persona_prompt_only_allows_problem_findings() -> None:
    prompt = build_persona_judge_prompt("Contenu test", {"persona": {}})

    assert "Ne jamais produire de finding positif." in prompt
    assert 'retourner "findings": [].' in prompt
