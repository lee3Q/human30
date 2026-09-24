"""Evaluate two structured Human30 outputs without generator self-assessment.

Pair JSON contract: ``scenario`` contains ``allowed_judgment_ids``,
``allowed_action_ids``, ``allowed_claim_ids``, ``forbidden_choices`` (a mapping
with ``judgment_ids``, ``action_ids``, ``claim_ids`` lists), and
``incompatible_claim_pairs`` (two-element lists). ``outputs`` is a two-element
list of the exact structured output shape defined by the Seed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class InvalidPair(ValueError):
    """The pair cannot be evaluated under the public contract."""


OUTPUT_KEYS = {"judgment_id", "emotion", "action_id", "claim_ids", "utterance"}
SCENARIO_KEYS = {
    "allowed_judgment_ids", "allowed_action_ids", "allowed_claim_ids",
    "forbidden_choices", "incompatible_claim_pairs",
}
FORBIDDEN_KEYS = {"judgment_ids", "action_ids", "claim_ids"}


def _object(value: object, name: str, keys: set[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise InvalidPair(f"{name} must be an object")
    if keys is not None and set(value) != keys:
        raise InvalidPair(f"{name} requires exactly {sorted(keys)}")
    return value


def _ids(value: object, name: str, *, unique: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise InvalidPair(f"{name} must be a list of nonempty IDs")
    if unique and len(value) != len(set(value)):
        raise InvalidPair(f"{name} contains duplicate IDs")
    return value


def _scenario(value: object) -> dict:
    scenario = _object(value, "scenario")
    missing = SCENARIO_KEYS - set(scenario)
    if missing:
        raise InvalidPair(f"scenario missing {sorted(missing)}")
    for key in ("allowed_judgment_ids", "allowed_action_ids", "allowed_claim_ids"):
        if not _ids(scenario[key], f"scenario.{key}"):
            raise InvalidPair(f"scenario.{key} must not be empty")
    forbidden = _object(scenario["forbidden_choices"], "scenario.forbidden_choices", FORBIDDEN_KEYS)
    for key, allowed in (
        ("judgment_ids", "allowed_judgment_ids"),
        ("action_ids", "allowed_action_ids"),
        ("claim_ids", "allowed_claim_ids"),
    ):
        if not set(_ids(forbidden[key], f"forbidden_choices.{key}")) <= set(scenario[allowed]):
            raise InvalidPair(f"forbidden_choices.{key} contains undefined IDs")
    pairs = scenario["incompatible_claim_pairs"]
    if not isinstance(pairs, list):
        raise InvalidPair("scenario.incompatible_claim_pairs must be a list")
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 2:
            raise InvalidPair("each incompatible claim pair needs two IDs")
        claims = _ids(pair, "incompatible claim pair")
        if not set(claims) <= set(scenario["allowed_claim_ids"]):
            raise InvalidPair("incompatible claim pair contains undefined IDs")
    return scenario


def _output(value: object, index: int, scenario: dict) -> dict:
    name = f"outputs[{index}]"
    output = _object(value, name, OUTPUT_KEYS)
    for key, allowed_key in (
        ("judgment_id", "allowed_judgment_ids"),
        ("action_id", "allowed_action_ids"),
    ):
        if not isinstance(output[key], str) or output[key] not in scenario[allowed_key]:
            raise InvalidPair(f"{name}.{key} is undefined")
    claims = _ids(output["claim_ids"], f"{name}.claim_ids")
    if not set(claims) <= set(scenario["allowed_claim_ids"]):
        raise InvalidPair(f"{name}.claim_ids contains undefined IDs")
    emotion = _object(output["emotion"], f"{name}.emotion", {"valence", "arousal"})
    for field, low, high in (("valence", -2, 2), ("arousal", 0, 2)):
        n = emotion[field]
        if type(n) is not int or not low <= n <= high:
            raise InvalidPair(f"{name}.emotion.{field} is out of range")
    if not isinstance(output["utterance"], str):
        raise InvalidPair(f"{name}.utterance must be a string")
    return output


def evaluate(pair: object) -> dict:
    """Return an independent receipt from scenario constraints and two outputs."""
    data = _object(pair, "pair")
    scenario = _scenario(data.get("scenario"))
    raw_outputs = data.get("outputs")
    if not isinstance(raw_outputs, list) or len(raw_outputs) != 2:
        raise InvalidPair("outputs must contain exactly two arms")
    outputs = [_output(raw, i, scenario) for i, raw in enumerate(raw_outputs)]
    forbidden = scenario["forbidden_choices"]
    arm_results = []
    for output in outputs:
        violations = []
        for field, key in (("judgment_id", "judgment_ids"), ("action_id", "action_ids")):
            if output[field] in forbidden[key]:
                violations.append({"field": field, "id": output[field]})
        violations.extend(
            {"field": "claim_ids", "id": claim}
            for claim in output["claim_ids"] if claim in forbidden["claim_ids"]
        )
        contradictions = [
            pair for pair in scenario["incompatible_claim_pairs"]
            if set(pair) <= set(output["claim_ids"])
        ]
        arm_results.append({
            "constraint_violations": violations,
            "self_contradictions": contradictions,
        })
    first, second = outputs
    return {
        "judgment_changed": first["judgment_id"] != second["judgment_id"],
        "emotion_changed": first["emotion"] != second["emotion"],
        "emotion_delta": {
            field: second["emotion"][field] - first["emotion"][field]
            for field in ("valence", "arousal")
        },
        "action_changed": first["action_id"] != second["action_id"],
        "utterance_expression_changed": first["utterance"] != second["utterance"],
        "arms": arm_results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        pair = json.loads(args.pair.read_text(encoding="utf-8"))
        receipt = evaluate(pair)
        args.out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (InvalidPair, OSError, json.JSONDecodeError) as exc:
        print(f"evaluation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
