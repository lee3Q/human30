"""Generate synthetic Human30 pairs with a pinned local model on CPU.

Install torch, transformers==4.51.3 and safetensors==0.5.3, then download the
model revision recorded below into runs/human30_repro/model. The verifier
checks every model file against the manifest before accepting a run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

from human30.paired import AXES
from scripts.build_public_pairs import BASELINE, CHANGED, SCENARIO

MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
MODEL_REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
MODEL_URL_TEMPLATE = "https://huggingface.co/{id}/resolve/{revision}/{file}"
MODEL_FILES = (
    "config.json", "generation_config.json", "model.safetensors",
    "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json",
)
PROMPT_VERSION = "human30-local-v1"
PROMPT_TEMPLATE = (
    "<|im_start|>user\nThis is a fictional scene. Write one short first-person "
    "sentence describing what the person does now.\n"
    "Scene: {scenario}\nPerson's condition: {condition}<|im_end|>\n"
    "<|im_start|>assistant\n"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_axis(axis: str, destination: Path, model, tokenizer, torch, seed: int, max_new_tokens: int, common: dict) -> None:
    folder = destination / axis
    folder.mkdir(parents=True, exist_ok=True)
    conditions = [BASELINE, {**BASELINE, axis: CHANGED[axis]}]
    receipt = {"axis": axis, "invocation": [sys.executable, *sys.argv],
               "runs": [], "status": "INCOMPLETE"}
    for arm, condition in enumerate(conditions):
        prompt = PROMPT_TEMPLATE.format(
            scenario=SCENARIO["stimulus"],
            condition=json.dumps(condition, ensure_ascii=False, sort_keys=True),
        )
        prompt_path = folder / f"arm_{arm}.prompt.txt"
        prompt_path.write_bytes(prompt.encode("utf-8"))
        inputs = tokenizer(prompt, return_tensors="pt")
        for repetition in range(2):
            # CPU generation consumes PyTorch's global RNG. Reset it for each
            # independent call and record its actual state around generation.
            torch.manual_seed(seed)
            before = sha(torch.get_rng_state().numpy().tobytes())
            with torch.inference_mode():
                tokens = model.generate(
                    **inputs, do_sample=True, temperature=0.7, top_p=0.9,
                    max_new_tokens=max_new_tokens,
                    pad_token_id=tokenizer.eos_token_id,
                )[0][inputs["input_ids"].shape[1]:].tolist()
            after = sha(torch.get_rng_state().numpy().tobytes())
            raw = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False).encode("utf-8")
            raw_path = folder / f"arm_{arm}.repeat_{repetition}.raw.txt"
            raw_path.write_bytes(raw)
            receipt["runs"].append({
                "arm": arm, "repetition": repetition, "raw_response": raw_path.name,
                "raw_sha256": sha(raw), "generated_token_ids": tokens,
                "effective_seed": seed, "rng_state_before_sha256": before,
                "rng_state_after_sha256": after,
                "prompt_sha256": sha(prompt.encode("utf-8")),
            })
            if not raw.strip():
                receipt["status"] = "FAIL"
                write_json(folder / "receipt.json", receipt)
                raise RuntimeError(f"{axis} arm {arm} repeat {repetition}: empty raw response")
        matching = receipt["runs"][-2]["raw_sha256"] == receipt["runs"][-1]["raw_sha256"]
        if not matching:
            receipt["status"] = "FAIL"
            write_json(folder / "receipt.json", receipt)
            raise RuntimeError(f"{axis} arm {arm}: repeated raw UTF-8 bytes differ")
    receipt["status"] = "PASS"
    receipt["actual_output"] = f"{axis}: PASS, both arms repeated identical raw UTF-8 bytes"
    write_json(folder / "receipt.json", receipt)
    manifest = {
        **common, "axis": axis, "scenario": SCENARIO,
        "scenario_sha256": sha(canonical(SCENARIO)),
        "condition_vectors": conditions,
        "condition_sha256": [sha(canonical(c)) for c in conditions],
        "prompt_version": PROMPT_VERSION,
        "prompt_template_sha256": sha(PROMPT_TEMPLATE.encode("utf-8")),
        "prompt_sha256": [sha((folder / f"arm_{a}.prompt.txt").read_bytes()) for a in range(2)],
    }
    write_json(folder / "manifest.json", manifest)
    print(receipt["actual_output"], flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("runs/human30_repro/model"))
    parser.add_argument("--out", type=Path, default=Path("runs/human30_repro"))
    parser.add_argument("--axes", nargs="+", choices=AXES, default=list(AXES))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-new-tokens", type=int, default=24)
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error("max-new-tokens must be positive")
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model_files = {name: sha((args.model_dir / name).read_bytes()) for name in MODEL_FILES}
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_dir, local_files_only=True, attn_implementation="eager"
    ).to("cpu").eval()
    common = {
        "model_provenance": {"id": MODEL_ID, "revision": MODEL_REVISION,
                             "files": model_files, "directory": "model",
                             "acquisition": {
                                 "method": "HTTPS GET from immutable Hugging Face revision; verify every SHA-256 before use",
                                 "url_template": MODEL_URL_TEMPLATE,
                                 "command": "uv run --group dev python scripts/acquire_human30_model.py",
                             }},
        "execution_provenance": {
            "runner": "scripts/run_local_human30_pairs.py",
            "runner_sha256": sha(Path(__file__).read_bytes()),
            "python": platform.python_version(), "platform": platform.platform(),
            "torch": torch.__version__, "transformers": transformers.__version__,
            "device": "cpu", "threads": torch.get_num_threads(),
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "effective_seed": args.seed,
            "rng": "torch.manual_seed(seed) per independent CPU run; torch.get_rng_state before/after",
            "sampling": {"do_sample": True, "temperature": 0.7, "top_p": 0.9,
                         "max_new_tokens": args.max_new_tokens},
        },
    }
    for axis in args.axes:
        run_axis(axis, args.out, model, tokenizer, torch, args.seed, args.max_new_tokens, common)
    return 0


if __name__ == "__main__":
    sys.exit(main())
