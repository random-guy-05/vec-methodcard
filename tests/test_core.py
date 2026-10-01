
from vec_methodcard.core import (
    artifact_record,
    new_card,
    render_markdown,
    validate_card,
)


def _complete(card):
    card["method"]["technical_summary"] = "A small reproducible baseline."
    card["data"]["preprocessing"] = "Log-normalized released training data."
    card["data"]["external_data_statement"] = "No external data."
    card["model"]["training"] = "Linear model trained on released stages."
    card["model"]["generation"] = "Sample 1000 cells with fixed seed."
    card["model"]["seeds"] = [7]
    card["reproduction"]["command"] = "python train.py && python export.py"
    card["reproduction"]["compute"] = "1 CPU, 8 GB RAM"
    return card


def test_human_complete_card_validates_and_renders(tmp_path):
    artifact = tmp_path / "pred.h5ad"
    artifact.write_bytes(b"prediction")
    card = _complete(new_card("Example", "human"))
    card["artifacts"].append(
        artifact_record(artifact, "prediction", "T1:val")
    )
    assert validate_card(card) == []
    text = render_markdown(card)
    assert "# Example" in text
    assert "T1:val" in text
    assert "SHA-256" in text


def test_todo_fields_fail_validation():
    errors = validate_card(new_card("Example", "human"))
    assert errors
    assert any("technical_summary" in error for error in errors)


def test_agent_requires_three_evidence_fields():
    card = _complete(new_card("Agent method", "agent"))
    errors = validate_card(card)
    assert any("trajectory" in error for error in errors)
    card["agent_evidence"] = {
        "trajectory": "runs/trajectory.jsonl",
        "prompts": "prompts/",
        "harness": "harness/",
    }
    assert validate_card(card) == []


def test_changed_artifact_is_detected(tmp_path):
    artifact = tmp_path / "pred.h5ad"
    artifact.write_bytes(b"a")
    card = _complete(new_card("Example", "human"))
    card["artifacts"].append(artifact_record(artifact, "prediction", None))
    artifact.write_bytes(b"b")
    assert any("SHA-256" in error for error in validate_card(card))
