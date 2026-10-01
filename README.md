# VEC MethodCard

A structured, hash-backed reproducibility record for VEC methods.

Instead of maintaining a prose methods note and a separate pile of artifact hashes, VEC MethodCard keeps one JSON source of truth and renders a readable Markdown card.

## Workflow

    pip install -e .

    vec-methodcard init --out methodcard.json --name "Temporal transport baseline" --track human
    # Edit methodcard.json and replace TODO fields
    vec-methodcard add-artifact --card methodcard.json --role prediction --board T1:val --path predictions/final_t1.h5ad
    vec-methodcard capture-env --card methodcard.json
    vec-methodcard validate --card methodcard.json
    vec-methodcard render --card methodcard.json --out METHOD_CARD.md

## What it records

- method name, version, track and technical summary;
- training/preprocessing/generation description;
- explicit external-data statement;
- seeds and reproduction command;
- exact artifacts with size + SHA-256 + optional board;
- Git commit and selected package versions;
- compute notes;
- Agent-track evidence locations.

For Agent cards, validation requires non-placeholder trajectory, prompts and harness entries. For Human cards, those fields are not required.

The tool does not decide whether a method is eligible under Challenge rules. It makes the disclosure/reproducibility record explicit and checkable; the official rules remain authoritative.

## Development

    pip install -e '.[dev]'
    pytest
    ruff check src tests
