
import json
import subprocess
import sys


def test_cli_init_complete_validate_render(tmp_path):
    card_path = tmp_path / "methodcard.json"
    output = tmp_path / "METHOD_CARD.md"

    init = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_methodcard.cli",
            "init",
            "--out",
            str(card_path),
            "--name",
            "Synthetic method",
            "--track",
            "human",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert init.returncode == 0

    card = json.loads(card_path.read_text())
    card["method"]["technical_summary"] = "Synthetic test."
    card["data"]["preprocessing"] = "None."
    card["data"]["external_data_statement"] = "No external data."
    card["model"]["training"] = "No training."
    card["model"]["generation"] = "Deterministic synthetic output."
    card["reproduction"]["command"] = "python synthetic.py"
    card["reproduction"]["compute"] = "CPU"
    card_path.write_text(json.dumps(card, indent=2) + "\n")

    validate = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_methodcard.cli",
            "validate",
            "--card",
            str(card_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr

    render = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_methodcard.cli",
            "render",
            "--card",
            str(card_path),
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert render.returncode == 0
    assert "# Synthetic method" in output.read_text()
