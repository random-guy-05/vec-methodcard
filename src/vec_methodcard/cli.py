
from __future__ import annotations

import argparse
from pathlib import Path

from .core import (
    artifact_record,
    capture_environment,
    load_card,
    new_card,
    render_markdown,
    save_card,
    validate_card,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Structured VEC method cards.")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--out", type=Path, default=Path("methodcard.json"))
    init.add_argument("--name", required=True)
    init.add_argument("--track", required=True, choices=["human", "agent"])

    artifact = subparsers.add_parser("add-artifact")
    artifact.add_argument("--card", type=Path, required=True)
    artifact.add_argument("--role", required=True)
    artifact.add_argument("--board")
    artifact.add_argument("--path", type=Path, required=True)

    environment = subparsers.add_parser("capture-env")
    environment.add_argument("--card", type=Path, required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--card", type=Path, required=True)

    render = subparsers.add_parser("render")
    render.add_argument("--card", type=Path, required=True)
    render.add_argument("--out", type=Path, default=Path("METHOD_CARD.md"))

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command_name == "init":
        if args.out.exists():
            raise SystemExit(f"refusing to overwrite existing card: {args.out}")
        save_card(args.out, new_card(args.name, args.track))
        print(args.out)
        return 0

    card = load_card(args.card)

    if args.command_name == "add-artifact":
        card.setdefault("artifacts", []).append(
            artifact_record(args.path, args.role, args.board)
        )
        save_card(args.card, card)
        print(args.card)
        return 0

    if args.command_name == "capture-env":
        capture_environment(card)
        save_card(args.card, card)
        print(args.card)
        return 0

    if args.command_name == "validate":
        errors = validate_card(card)
        if errors:
            for error in errors:
                print(f"FAIL: {error}")
            return 3
        print("PASS")
        return 0

    errors = validate_card(card)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("refusing to render an invalid/incomplete method card")
        return 3
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(card), encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
