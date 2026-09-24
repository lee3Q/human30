"""Build auditable, single-axis Human30 paired counterfactual records."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from human30.evaluate import evaluate


AXES = ("body", "memory", "identity", "world_model")


def digest(value: Any) -> str:
    """Hash a JSON value independently of whitespace and key order."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_run(
    *,
    axis: str,
    scenario: dict,
    conditions: list[dict],
    outputs: list[dict],
    prompt_version: str,
    model: dict,
    seed: int,
    settings: dict,
    environment: dict,
    retries: list[int],
) -> tuple[dict, dict]:
    """Return an evaluator input and its provenance manifest.

    The caller supplies recorded outputs and truthful model metadata. This
    function does not infer how the outputs were generated.
    """
    if axis not in AXES:
        raise ValueError(f"unknown axis: {axis}")
    if len(conditions) != 2 or any(set(c) != set(AXES) for c in conditions):
        raise ValueError("conditions must be two complete four-axis vectors")
    changed = [key for key in AXES if conditions[0][key] != conditions[1][key]]
    if changed != [axis]:
        raise ValueError(f"only {axis} may differ between conditions")
    if len(retries) != 2 or any(type(n) is not int or n < 0 for n in retries):
        raise ValueError("retries must be two nonnegative counts")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if not prompt_version or not all(model.get(key) for key in ("id", "version", "source")):
        raise ValueError("prompt version and actual model identity, version, source are required")
    if not isinstance(settings, dict) or not settings or not isinstance(environment, dict) or not environment:
        raise ValueError("settings and environment must be recorded objects")
    # Keep the receipt inputs and manifest tied to the values we validated,
    # even if a caller later reuses or mutates its input dictionaries.
    scenario = deepcopy(scenario)
    conditions = deepcopy(conditions)
    outputs = deepcopy(outputs)
    model = deepcopy(model)
    settings = deepcopy(settings)
    environment = deepcopy(environment)
    retries = retries.copy()
    pair = {"scenario": scenario, "outputs": outputs}
    evaluate(pair)  # Reject malformed or undefined structured outputs.
    manifest = {
        "axis": axis,
        "prompt_version": prompt_version,
        "model": model,
        "seed": seed,
        "settings": settings,
        "environment": environment,
        "scenario_sha256": digest(scenario),
        "condition_vectors": conditions,
        "output_sha256": [digest(output) for output in outputs],
        "retries": retries,
    }
    return pair, manifest
