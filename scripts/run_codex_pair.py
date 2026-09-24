"""Record one real-model paired example using the authenticated Codex CLI.

Codex CLI does not expose a sampling seed. The manifest says so explicitly:
the scenario seed is fixed in both prompts, but deterministic sampling is not
claimed. Use a seed-capable provider for stricter repeated experiments.
"""

from __future__ import annotations

import argparse
import json
import platform
import shlex
import subprocess
import tempfile
from pathlib import Path

from human30.evaluate import evaluate
from human30.paired import AXES, build_run, digest
from scripts.build_public_pairs import BASELINE, CHANGED, SCENARIO


PROMPT_VERSION = "paired-codex-v1"
PROMPT_TEMPLATE = """You are generating one simulated response for an exploratory Human30 comparison.
Return only a JSON object conforming to the supplied schema. Do not use tools.
This is fictional simulation, not a claim about a real person.
Scenario seed (a shared prompt condition, not an API sampling seed): {seed}
Scenario: {scenario}
Condition vector: {condition}
Pick judgment_id, action_id and claim_ids from the scenario's allowed IDs.
Express emotion as integer valence (-2..2) and arousal (0..2).
The two arms are independent responses; do not infer an unseen other arm.
"""


def output_schema(scenario: dict) -> dict:
    return {
        "type": "object",
        "properties": {
            "judgment_id": {"type": "string", "enum": scenario["allowed_judgment_ids"]},
            "emotion": {
                "type": "object",
                "properties": {
                    "valence": {"type": "integer", "minimum": -2, "maximum": 2},
                    "arousal": {"type": "integer", "minimum": 0, "maximum": 2},
                },
                "required": ["valence", "arousal"],
                "additionalProperties": False,
            },
            "action_id": {"type": "string", "enum": scenario["allowed_action_ids"]},
            "claim_ids": {
                "type": "array", "items": {"type": "string", "enum": scenario["allowed_claim_ids"]},
            },
            "utterance": {"type": "string"},
        },
        "required": ["judgment_id", "emotion", "action_id", "claim_ids", "utterance"],
        "additionalProperties": False,
    }


def invoke(prompt: str, schema: dict, model_id: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="human30-model-") as temporary:
        folder = Path(temporary)
        schema_path = folder / "schema.json"
        output_path = folder / "output.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        command = [
            "codex", "exec", "-m", model_id, "-s", "read-only", "-C", "/tmp",
            "--skip-git-repo-check", "--ephemeral", "-c", "model_reasoning_effort=low",
            "--output-schema", str(schema_path), "--output-last-message", str(output_path), "-",
        ]
        # The user's authenticated Codex environment is initialized by the
        # login shell; invoking the binary directly can omit that environment.
        result = subprocess.run(
            ["/bin/zsh", "-lc", shlex.join(command)],
            input=prompt, text=True, capture_output=True, timeout=240,
        )
        if result.returncode:
            raise RuntimeError(f"Codex CLI failed with exit {result.returncode}: {result.stderr[-1000:]}")
        return json.loads(output_path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--axis", choices=AXES, default="body")
    parser.add_argument("--model", default="gpt-6-sol")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    conditions = [BASELINE, {**BASELINE, args.axis: CHANGED[args.axis]}]
    schema = output_schema(SCENARIO)
    prompts = [
        PROMPT_TEMPLATE.format(
            seed=args.seed,
            scenario=json.dumps(SCENARIO, sort_keys=True),
            condition=json.dumps(condition, sort_keys=True),
        )
        for condition in conditions
    ]
    outputs = [invoke(prompt, schema, args.model) for prompt in prompts]
    cli_version = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    pair, manifest = build_run(
        axis=args.axis, scenario=SCENARIO, conditions=conditions, outputs=outputs,
        prompt_version=PROMPT_VERSION,
        model={"id": args.model, "version": "not_exposed_by_codex_cli", "source": "codex_cli_actual"},
        seed=args.seed,
        settings={"reasoning_effort": "low", "sampling_seed_supported": False},
        environment={"python": platform.python_version(), "platform": platform.platform(), "codex_cli_version": cli_version},
        retries=[0, 0],
    )
    receipt = evaluate(pair)
    manifest["prompt_template_sha256"] = digest(PROMPT_TEMPLATE)
    manifest["prompt_sha256"] = [digest(prompt) for prompt in prompts]
    manifest["effective_model_seed"] = None
    manifest["seed_scope"] = "scenario_prompt_only; Codex CLI has no sampling-seed option"
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (("pair.json", pair), ("manifest.json", manifest), ("receipt.json", receipt)):
        write_json(args.out / name, value)
    for index, prompt in enumerate(prompts):
        (args.out / f"arm_{index}.prompt.txt").write_text(prompt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
