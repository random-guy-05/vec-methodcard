
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
TRACKS = {"human", "agent"}
PACKAGE_NAMES = [
    "numpy",
    "scipy",
    "pandas",
    "anndata",
    "h5py",
    "scikit-learn",
    "torch",
    "jax",
    "tensorflow",
    "veckit",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_card(name: str, track: str) -> dict[str, Any]:
    track = track.lower()
    if track not in TRACKS:
        raise ValueError("track must be human or agent")
    return {
        "schema_version": SCHEMA_VERSION,
        "method": {
            "name": name,
            "version": "1.0",
            "track": track,
            "technical_summary": "TODO",
        },
        "data": {
            "preprocessing": "TODO",
            "external_data_statement": "TODO: state none, or list and justify every source",
        },
        "model": {
            "training": "TODO",
            "generation": "TODO",
            "seeds": [],
        },
        "reproduction": {
            "command": "TODO",
            "compute": "TODO",
            "git_commit": None,
            "packages": {},
        },
        "artifacts": [],
        "agent_evidence": {
            "trajectory": "",
            "prompts": "",
            "harness": "",
        },
        "created_utc": utc_now(),
        "updated_utc": utc_now(),
    }


def load_card(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("method card must be a JSON object")
    return payload


def save_card(path: Path, card: dict[str, Any]) -> None:
    card["updated_utc"] = utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(card, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def artifact_record(path: Path, role: str, board: str | None) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return {
        "role": role,
        "board": board,
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def capture_environment(card: dict[str, Any]) -> None:
    packages: dict[str, str] = {}
    for distribution in PACKAGE_NAMES:
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            continue
    card["reproduction"]["git_commit"] = git_sha()
    card["reproduction"]["packages"] = packages
    card["reproduction"]["python"] = platform.python_version()
    card["reproduction"]["platform"] = platform.platform()


def _is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return not value
    stripped = value.strip()
    return not stripped or stripped.upper().startswith("TODO")


def validate_card(card: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if card.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    method = card.get("method", {})
    track = str(method.get("track", "")).lower()
    if track not in TRACKS:
        errors.append("method.track must be human or agent")

    required_paths = [
        ("method.name", method.get("name")),
        ("method.technical_summary", method.get("technical_summary")),
        ("data.preprocessing", card.get("data", {}).get("preprocessing")),
        (
            "data.external_data_statement",
            card.get("data", {}).get("external_data_statement"),
        ),
        ("model.training", card.get("model", {}).get("training")),
        ("model.generation", card.get("model", {}).get("generation")),
        ("reproduction.command", card.get("reproduction", {}).get("command")),
        ("reproduction.compute", card.get("reproduction", {}).get("compute")),
    ]
    for name, value in required_paths:
        if _is_placeholder(value):
            errors.append(f"{name} is missing or still TODO")

    for index, artifact in enumerate(card.get("artifacts", [])):
        path = Path(str(artifact.get("path", "")))
        if not path.is_file():
            errors.append(f"artifacts[{index}] file is missing: {path}")
            continue
        actual = sha256_file(path)
        if actual != artifact.get("sha256"):
            errors.append(f"artifacts[{index}] SHA-256 no longer matches")

    if track == "agent":
        evidence = card.get("agent_evidence", {})
        for key in ("trajectory", "prompts", "harness"):
            if _is_placeholder(evidence.get(key)):
                errors.append(f"agent_evidence.{key} is required for agent track")

    return errors


def render_markdown(card: dict[str, Any]) -> str:
    method = card["method"]
    data = card["data"]
    model = card["model"]
    reproduction = card["reproduction"]
    lines = [
        f"# {method['name']}",
        "",
        f"- **Method version:** {method.get('version', '')}",
        f"- **Track:** {method['track']}",
        f"- **Card schema:** {card['schema_version']}",
        f"- **Updated:** {card.get('updated_utc', '')}",
        "",
        "## Technical summary",
        "",
        str(method["technical_summary"]),
        "",
        "## Data and preprocessing",
        "",
        str(data["preprocessing"]),
        "",
        "**External data statement:**",
        "",
        str(data["external_data_statement"]),
        "",
        "## Model / training",
        "",
        str(model["training"]),
        "",
        "## Prediction generation",
        "",
        str(model["generation"]),
        "",
        f"**Seeds:** {', '.join(map(str, model.get('seeds', []))) or 'not recorded'}",
        "",
        "## Reproduction",
        "",
        "    " + str(reproduction["command"]),
        "",
        f"**Compute:** {reproduction['compute']}",
        f"**Git commit:** {reproduction.get('git_commit') or 'not captured'}",
        f"**Python:** {reproduction.get('python', 'not captured')}",
        "",
        "## Artifacts",
        "",
        "| role | board | file | bytes | SHA-256 |",
        "|---|---|---|---:|---|",
    ]
    for artifact in card.get("artifacts", []):
        lines.append(
            f"| {artifact['role']} | {artifact.get('board') or ''} | "
            f"{Path(artifact['path']).name} | {artifact['size_bytes']} | "
            f"{artifact['sha256']} |"
        )

    packages = reproduction.get("packages", {})
    if packages:
        lines.extend(["", "## Captured packages", ""])
        for name, version in sorted(packages.items()):
            lines.append(f"- {name}=={version}")

    if method["track"] == "agent":
        evidence = card.get("agent_evidence", {})
        lines.extend(
            [
                "",
                "## Agent evidence",
                "",
                f"- **Trajectory:** {evidence.get('trajectory', '')}",
                f"- **Prompts:** {evidence.get('prompts', '')}",
                f"- **Harness:** {evidence.get('harness', '')}",
            ]
        )
    return "\n".join(lines) + "\n"
