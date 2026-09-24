"""Verify persisted public paired-run artifacts and write one receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from human30.evaluate import evaluate
from human30.paired import AXES, digest
from scripts.run_codex_pair import output_schema


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "runs" / "public_counterfactual"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(pair_path: Path, manifest_path: Path, receipt_path: Path, expected_axis: str) -> dict:
    pair, manifest = load(pair_path), load(manifest_path)
    conditions = manifest["condition_vectors"]
    assert len(conditions) == 2 and all(set(item) == set(AXES) for item in conditions)
    changed = [axis for axis in AXES if conditions[0][axis] != conditions[1][axis]]
    assert changed == [expected_axis] == [manifest["axis"]]
    assert manifest["scenario_sha256"] == digest(pair["scenario"])
    assert len(pair["outputs"]) == len(manifest["output_sha256"]) == 2
    assert manifest["output_sha256"] == [digest(item) for item in pair["outputs"]]
    assert manifest["retries"] and len(manifest["retries"]) == 2
    assert all(manifest.get(key) for key in ("prompt_version", "model", "settings", "environment"))
    calculated = evaluate(pair)
    if receipt_path.exists():
        assert load(receipt_path) == calculated
    return {
        "axis": expected_axis,
        "source": manifest["model"]["source"],
        "pair_sha256": hashlib.sha256(pair_path.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "evaluation": calculated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    verified = []
    for axis in AXES:
        verified.append(verify(
            PUBLIC / f"{axis}.pair.json",
            PUBLIC / f"{axis}.manifest.json",
            PUBLIC / f"{axis}.receipt.json",
            axis,
        ))
    actual = PUBLIC / "actual_codex_body"
    verified.append(verify(
        actual / "pair.json", actual / "manifest.json", actual / "receipt.json", "body",
    ))
    actual_manifest = load(actual / "manifest.json")
    assert actual_manifest["model"]["source"] == "codex_cli_actual"
    assert actual_manifest["settings"]["sampling_seed_supported"] is False
    assert actual_manifest["effective_model_seed"] is None
    prompts = [(actual / f"arm_{index}.prompt.txt").read_text(encoding="utf-8") for index in range(2)]
    assert actual_manifest["prompt_sha256"] == [digest(prompt) for prompt in prompts]
    seeded = PUBLIC / "actual_seeded"
    repeat_matches = 0
    for axis in AXES:
        folder = seeded / axis
        verified.append(verify(folder / "pair.json", folder / "manifest.json", folder / "receipt.json", axis))
        manifest = load(folder / "manifest.json")
        assert manifest["model"]["source"] == "openrouter_seeded_api_actual"
        assert manifest["catalog_advertised_seed"] is True
        assert manifest["requested_model_seed"] == manifest["seed"] == 42
        assert manifest["settings"]["sampling_seed_supported"] is True
        assert manifest["effective_seed_reported_by_provider"] is False
        assert manifest["model"]["version"] == "exact_snapshot_not_exposed"
        assert len(manifest["response_provenance"]) == 2
        pair = load(folder / "pair.json")
        for index in range(2):
            prompt = (folder / f"arm_{index}.prompt.txt").read_text(encoding="utf-8")
            assert digest(prompt) == manifest["prompt_sha256"][index]
            request = {
                "model": manifest["model"]["id"],
                "messages": [{"role": "user", "content": prompt}],
                "seed": manifest["seed"],
                "temperature": manifest["settings"]["temperature"],
                "max_tokens": manifest["settings"]["max_tokens"],
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "human30_arm", "strict": True, "schema": output_schema(pair["scenario"]),
                }},
            }
            source = manifest["response_provenance"][index]
            assert source["request_sha256"] == digest(request)
            assert source["returned_model"] == manifest["model"]["id"]
            assert source["response_id"] and source["provider"] == "OpenAI"
        repeated = manifest["repeat_output_sha256"] == manifest["output_sha256"][0]
        assert repeated == manifest["same_seed_baseline_repeat_equal"]
        repeat_matches += int(repeated)
    result = {
        "status": "PASS",
        "verified_runs": verified,
        "actual_model_pair_count": 5,
        "seed_requested_pair_count": 4,
        "same_seed_repeat_match_count": repeat_matches,
        "limitation": "The seeded API advertises seed support but does not report effective seed or exact model snapshot; equal-seed repeats can differ. Causal effect estimation is Stage 2 work.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(verified)} paired artifacts, including five actual model pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
