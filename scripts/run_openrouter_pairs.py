"""Generate public Human30 pairs with one seed-capable model API.

Only synthetic scenario text is transmitted. Set OPENROUTER_API_KEY in the
environment; the key is never written to an artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import urllib.request
from pathlib import Path

from human30.evaluate import evaluate
from human30.paired import AXES, build_run, digest
from scripts.build_public_pairs import BASELINE, CHANGED, SCENARIO
from scripts.run_codex_pair import PROMPT_TEMPLATE, output_schema


API = "https://openrouter.ai/api/v1"
PROMPT_VERSION = "paired-seeded-api-v1"


def get_model(model_id: str) -> dict:
    with urllib.request.urlopen(f"{API}/models", timeout=30) as response:
        models = json.load(response)["data"]
    model = next((item for item in models if item["id"] == model_id), None)
    if not model or "seed" not in model.get("supported_parameters", []) or "response_format" not in model.get("supported_parameters", []):
        raise ValueError("model must advertise seed and response_format support")
    return model


def invoke(prompt: str, model_id: str, seed: int, temperature: float) -> tuple[dict, dict]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is required")
    request_body = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "seed": seed,
        "temperature": temperature,
        "max_tokens": 300,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "human30_arm", "strict": True, "schema": output_schema(SCENARIO),
        }},
    }
    request = urllib.request.Request(
        f"{API}/chat/completions", data=json.dumps(request_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = json.load(response)
    content = raw["choices"][0]["message"]["content"]
    output = json.loads(content)
    provenance = {
        "response_id": raw.get("id"), "returned_model": raw.get("model"),
        "provider": raw.get("provider"), "system_fingerprint": raw.get("system_fingerprint"),
        "usage": raw.get("usage"), "request_sha256": digest(request_body),
    }
    return output, provenance


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="openai/gpt-4.1-mini")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--axes", nargs="+", choices=AXES, default=list(AXES))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    catalog = get_model(args.model)
    for axis in args.axes:
        conditions = [BASELINE, {**BASELINE, axis: CHANGED[axis]}]
        prompts = [PROMPT_TEMPLATE.format(
            seed=args.seed, scenario=json.dumps(SCENARIO, sort_keys=True),
            condition=json.dumps(condition, sort_keys=True),
        ) for condition in conditions]
        outputs, provenance = [], []
        for prompt in prompts:
            output, source = invoke(prompt, args.model, args.seed, args.temperature)
            outputs.append(output)
            provenance.append(source)
        repeat_output, repeat_source = invoke(prompts[0], args.model, args.seed, args.temperature)
        pair, manifest = build_run(
            axis=axis, scenario=SCENARIO, conditions=conditions, outputs=outputs,
            prompt_version=PROMPT_VERSION,
            model={"id": args.model, "version": "exact_snapshot_not_exposed", "source": "openrouter_seeded_api_actual"},
            seed=args.seed,
            settings={"temperature": args.temperature, "max_tokens": 300, "response_format": "json_schema",
                      "sampling_seed_supported": True},
            environment={"python": platform.python_version(), "api": API,
                         "provider": provenance[0]["provider"]},
            retries=[0, 0],
        )
        receipt = evaluate(pair)
        manifest.update({
            "catalog_model_id": catalog["id"], "catalog_advertised_seed": True,
            "prompt_template_sha256": digest(PROMPT_TEMPLATE),
            "prompt_sha256": [digest(item) for item in prompts],
            "requested_model_seed": args.seed,
            "effective_seed_reported_by_provider": False,
            "same_seed_baseline_repeat_equal": repeat_output == outputs[0],
            "response_provenance": provenance,
            "repeat_provenance": repeat_source,
            "repeat_output_sha256": digest(repeat_output),
        })
        folder = args.out / axis
        write(folder / "pair.json", pair)
        write(folder / "manifest.json", manifest)
        write(folder / "receipt.json", receipt)
        for index, prompt in enumerate(prompts):
            (folder / f"arm_{index}.prompt.txt").write_text(prompt, encoding="utf-8")
        print(f"{axis}: same-seed repeat {'matched' if repeat_output == outputs[0] else 'differed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
