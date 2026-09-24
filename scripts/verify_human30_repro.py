"""Read-only verification of pinned local Human30 paired runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Direct execution (`python scripts/verify_human30_repro.py`) otherwise places
# only scripts/ on sys.path, hiding the repository's packages.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from human30.paired import AXES
from scripts.build_public_pairs import BASELINE, CHANGED, SCENARIO
from scripts.run_local_human30_pairs import MODEL_FILES, MODEL_ID, MODEL_REVISION, PROMPT_TEMPLATE, PROMPT_VERSION, canonical, sha

# SHA-256 of torch 2.10.0 CPU get_rng_state() immediately after manual_seed(42).
# Pinning this independently computed value prevents two equally fabricated
# receipt hashes from being mistaken for evidence that the seed was applied.
PINNED_RNG_START_SHA256 = "5feb54a46230d321d888e9b43cf5a57492665f199e4377408d79ee460e36679c"
PINNED_MODEL_SHA256 = "5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c"
PINNED_MODEL_FILES = {
    "config.json": "8eb740e8bbe4cff95ea7b4588d17a2432deb16e8075bc5828ff7ba9be94d982a",
    "generation_config.json": "87b916edaaab66b3899b9d0dd0752727dff6666686da0504d89ae0a6e055a013",
    "model.safetensors": PINNED_MODEL_SHA256,
    "special_tokens_map.json": "2b7379f3ae813529281a5c602bc5a11c1d4e0a99107aaa597fe936c1e813ca52",
    "tokenizer.json": "9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c",
    "tokenizer_config.json": "4ec77d44f62efeb38d7e044a1db318f6a939438425312dfa333b8382dbad98df",
}
PINNED_RUNNER_SHA256 = "4051fe87760de456e5b801b1b1f320036f01e5f7247b3ec104653651342f9184"
PINNED_SCENARIO_SOURCE_SHA256 = "4e3aa4959c8cf958889cc4b03c3c152853061afcfeba8fed1a3eb540bc80dad9"
PINNED_COMMON_RAW_SHA256 = "8953f2e796caf282fe298995cd1e9ce83871265ea1f606312e0ae5ef7cf89b11"
PINNED_WORLD_CHANGED_RAW_SHA256 = "e673cc53e111766d1b47ab74a5eabf90d5004cd73bdb0ea9a948482b2ff31db3"
PINNED_COMMON_TOKENS_SHA256 = "9c92daef27287836468d53be3c28971f9a4b978ae42c722ea22f78c1fdb253c9"
PINNED_WORLD_CHANGED_TOKENS_SHA256 = "b5c7783120daa7079026717c8bcdf630c1377f3301880acd711d99323b4e48d5"
PINNED_COMMON_RNG_END_SHA256 = "bfa9ba76fab5dbb67cb77c96a1f0b1e92e452e7ea59d51af453ad5cc0b07d8d0"
PINNED_WORLD_CHANGED_RNG_END_SHA256 = "9e343f87be3751b4c93b6d6b66de2e0eca45dd8358e5b24fd0495519c5725d84"
MODEL_URL_TEMPLATE = "https://huggingface.co/{id}/resolve/{revision}/{file}"


class RepeatMismatch(AssertionError):
    """An arm's independently generated raw UTF-8 responses differ."""


def require(condition: bool, message: str) -> None:
    """Keep evidence checks active when Python runs with optimization enabled."""
    if not condition:
        raise AssertionError(message)


def verify_axis(root: Path, axis: str) -> None:
    require(sha((ROOT / "scripts/build_public_pairs.py").read_bytes()) == PINNED_SCENARIO_SOURCE_SHA256,
            "scenario source pin mismatch")
    folder = root / axis
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
    require(manifest["axis"] == receipt["axis"] == axis, f"{axis}: axis mismatch")
    require(manifest["scenario"] == SCENARIO, "evidence check failed")
    require(manifest["scenario_sha256"] == sha(canonical(SCENARIO)), "evidence check failed")
    conditions = [BASELINE, {**BASELINE, axis: CHANGED[axis]}]
    require(manifest["condition_vectors"] == conditions, "evidence check failed")
    require(manifest["condition_sha256"] == [sha(canonical(c)) for c in conditions], "evidence check failed")
    require(manifest["prompt_version"] == PROMPT_VERSION, "evidence check failed")
    require(manifest["prompt_template_sha256"] == sha(PROMPT_TEMPLATE.encode("utf-8")), "evidence check failed")

    model = manifest["model_provenance"]
    require(model["id"] == MODEL_ID and model["revision"] == MODEL_REVISION, "evidence check failed")
    require(model["files"] == PINNED_MODEL_FILES, f"{axis}: model file pin mismatch")
    require(set(model["files"]) == set(MODEL_FILES), "evidence check failed")
    require(model["directory"] == "model", "evidence check failed")
    require(model["acquisition"] == {
        "method": "HTTPS GET from immutable Hugging Face revision; verify every SHA-256 before use",
        "url_template": MODEL_URL_TEMPLATE,
        "command": "uv run --group dev python scripts/acquire_human30_model.py",
    }, f"{axis}: model acquisition mismatch")
    model_dir = root / model["directory"]
    for name in MODEL_FILES:
        require(sha((model_dir / name).read_bytes()) == model["files"][name], f"{axis}: model hash mismatch: {name}")

    execution = manifest["execution_provenance"]
    require(execution["runner"] == "scripts/run_local_human30_pairs.py", "evidence check failed")
    require(execution["runner_sha256"] == PINNED_RUNNER_SHA256, f"{axis}: runner pin mismatch")
    require(sha(Path(execution["runner"]).read_bytes()) == PINNED_RUNNER_SHA256, "evidence check failed")
    require(execution["device"] == "cpu", "evidence check failed")
    require(execution["threads"] == 1, "evidence check failed")
    require(execution["deterministic_algorithms"] is True, "evidence check failed")
    seed = execution["effective_seed"]
    require(type(seed) is int and execution["rng"] == (
        "torch.manual_seed(seed) per independent CPU run; torch.get_rng_state before/after"
    ), f"{axis}: effective seed not confirmed")
    require(seed == 42 and execution["torch"] == "2.10.0", f"{axis}: no independent CPU RNG reference for seed or torch version")
    require(execution["sampling"] == {
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_new_tokens": 24,
    }, f"{axis}: sampling settings mismatch")
    require(len(manifest["prompt_sha256"]) == 2, f"{axis}: prompt hash count mismatch")
    require(receipt["status"] == "PASS" and len(receipt["runs"]) == 4, "evidence check failed")
    require(receipt["invocation"] and receipt["actual_output"] == (
        f"{axis}: PASS, both arms repeated identical raw UTF-8 bytes"
    ), "evidence check failed")
    for arm, condition in enumerate(conditions):
        changed_world = axis == "world_model" and arm == 1
        expected_raw = PINNED_WORLD_CHANGED_RAW_SHA256 if changed_world else PINNED_COMMON_RAW_SHA256
        expected_tokens = PINNED_WORLD_CHANGED_TOKENS_SHA256 if changed_world else PINNED_COMMON_TOKENS_SHA256
        expected_rng_end = PINNED_WORLD_CHANGED_RNG_END_SHA256 if changed_world else PINNED_COMMON_RNG_END_SHA256
        prompt = PROMPT_TEMPLATE.format(
            scenario=SCENARIO["stimulus"],
            condition=json.dumps(condition, ensure_ascii=False, sort_keys=True),
        ).encode("utf-8")
        require((folder / f"arm_{arm}.prompt.txt").read_bytes() == prompt, "evidence check failed")
        require(manifest["prompt_sha256"][arm] == sha(prompt), "evidence check failed")
        raws = []
        starts = []
        for repetition in range(2):
            run = receipt["runs"][2 * arm + repetition]
            require(run["arm"] == arm and run["repetition"] == repetition, "evidence check failed")
            require(run["effective_seed"] == seed, f"{axis} arm {arm}: seed mismatch")
            require(run["prompt_sha256"] == sha(prompt), "evidence check failed")
            name = f"arm_{arm}.repeat_{repetition}.raw.txt"
            require(run["raw_response"] == name, "evidence check failed")
            raw = (folder / name).read_bytes()
            raw.decode("utf-8", errors="strict")
            require(raw.strip(), f"{axis} arm {arm} repeat {repetition}: empty raw response")
            require(run["raw_sha256"] == sha(raw), f"{axis} arm {arm} repeat {repetition}: raw hash mismatch")
            token_ids = run["generated_token_ids"]
            require(isinstance(token_ids, list) and 1 <= len(token_ids) <= 24
                    and all(type(token) is int and token >= 0 for token in token_ids),
                    f"{axis} arm {arm}: invalid generated token IDs")
            require(sha(canonical(token_ids)) == expected_tokens, f"{axis} arm {arm}: token pin mismatch")
            require(len(run["rng_state_before_sha256"]) == len(run["rng_state_after_sha256"]) == 64, "evidence check failed")
            require(run["rng_state_before_sha256"] == PINNED_RNG_START_SHA256, f"{axis} arm {arm} repeat {repetition}: seed not applied to CPU RNG")
            require(run["rng_state_after_sha256"] == expected_rng_end, f"{axis} arm {arm}: RNG end pin mismatch")
            raws.append(raw)
            starts.append(run["rng_state_before_sha256"])
        require(starts[0] == starts[1], f"{axis} arm {arm}: RNG start mismatch")
        if raws[0] != raws[1]:
            raise RepeatMismatch(f"{axis} arm {arm}: repeated raw UTF-8 bytes differ")
        require(sha(raws[0]) == expected_raw, f"{axis} arm {arm}: raw output pin mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("runs/human30_repro"))
    parser.add_argument("--axes", nargs="+", choices=AXES, default=list(AXES))
    args = parser.parse_args()
    try:
        for axis in args.axes:
            verify_axis(args.out, axis)
    except RepeatMismatch:
        print("FAIL human30_repro: repeated raw responses differ", file=sys.stderr)
        return 1
    except (AssertionError, OSError, KeyError, ValueError, TypeError) as exc:
        print(f"FAIL human30_repro: {exc}", file=sys.stderr)
        return 1
    print("PASS human30_repro")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
