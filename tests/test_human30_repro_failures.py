"""Reject tampered local generation evidence without altering the source run."""

import json
import shutil
from pathlib import Path

import pytest

from scripts.run_local_human30_pairs import MODEL_FILES, sha
from scripts.verify_human30_repro import verify_axis


SOURCE = Path(__file__).resolve().parents[1] / "runs" / "human30_repro"


@pytest.fixture
def body_run(tmp_path):
    shutil.copytree(SOURCE / "body", tmp_path / "body")
    model = tmp_path / "model"
    model.mkdir()
    for name in MODEL_FILES:
        (model / name).symlink_to(SOURCE / "model" / name)
    verify_axis(tmp_path, "body")
    return tmp_path


def rewrite_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_rejects_model_file_hash_mismatch(body_run):
    model_file = body_run / "model" / "config.json"
    model_file.unlink()
    shutil.copyfile(SOURCE / "model" / "config.json", model_file)
    model_file.write_bytes(model_file.read_bytes() + b"\n")
    with pytest.raises(AssertionError, match="model hash mismatch: config.json"):
        verify_axis(body_run, "body")


def test_rejects_coordinated_model_file_and_manifest_change(body_run):
    model_file = body_run / "model" / "config.json"
    model_file.unlink()
    shutil.copyfile(SOURCE / "model" / "config.json", model_file)
    model_file.write_bytes(model_file.read_bytes() + b"\n")
    manifest_file = body_run / "body" / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["model_provenance"]["files"]["config.json"] = sha(model_file.read_bytes())
    rewrite_json(manifest_file, manifest)
    with pytest.raises(AssertionError, match="model file pin mismatch"):
        verify_axis(body_run, "body")


def test_rejects_coordinated_runner_manifest_hash_change(body_run):
    manifest_file = body_run / "body" / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["execution_provenance"]["runner_sha256"] = "0" * 64
    rewrite_json(manifest_file, manifest)
    with pytest.raises(AssertionError, match="runner pin mismatch"):
        verify_axis(body_run, "body")


def test_rejects_truncated_prompt_hashes(body_run):
    manifest_file = body_run / "body" / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["prompt_sha256"] = manifest["prompt_sha256"][:1]
    rewrite_json(manifest_file, manifest)
    with pytest.raises(AssertionError, match="prompt hash count mismatch"):
        verify_axis(body_run, "body")


def test_rejects_coordinated_raw_and_receipt_change(body_run):
    folder = body_run / "body"
    receipt_file = folder / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    for repetition in range(2):
        raw_file = folder / f"arm_0.repeat_{repetition}.raw.txt"
        raw_file.write_bytes(b"forged but repeated")
        receipt["runs"][repetition]["raw_sha256"] = sha(raw_file.read_bytes())
    rewrite_json(receipt_file, receipt)
    with pytest.raises(AssertionError, match="raw output pin mismatch"):
        verify_axis(body_run, "body")


@pytest.mark.parametrize("token_ids", [["bad"], [True], [1.5], []])
def test_rejects_malformed_token_ids(body_run, token_ids):
    receipt_file = body_run / "body" / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["runs"][0]["generated_token_ids"] = token_ids
    rewrite_json(receipt_file, receipt)
    with pytest.raises(AssertionError, match="invalid generated token IDs"):
        verify_axis(body_run, "body")


def test_rejects_unpinned_rng_end(body_run):
    receipt_file = body_run / "body" / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["runs"][0]["rng_state_after_sha256"] = "0" * 64
    rewrite_json(receipt_file, receipt)
    with pytest.raises(AssertionError, match="RNG end pin mismatch"):
        verify_axis(body_run, "body")


def test_rejects_repeated_raw_byte_mismatch_even_with_updated_receipt_hash(body_run):
    folder = body_run / "body"
    raw_file = folder / "arm_0.repeat_1.raw.txt"
    changed = raw_file.read_bytes() + b" changed"
    raw_file.write_bytes(changed)
    receipt_file = folder / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["runs"][1]["raw_sha256"] = sha(changed)
    rewrite_json(receipt_file, receipt)
    with pytest.raises(AssertionError, match="body arm 0: repeated raw UTF-8 bytes differ"):
        verify_axis(body_run, "body")


@pytest.mark.parametrize("unconfirmed_seed", [None, "unconfirmed"])
def test_rejects_unconfirmed_seed(body_run, unconfirmed_seed):
    manifest_file = body_run / "body" / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["execution_provenance"]["effective_seed"] = unconfirmed_seed
    rewrite_json(manifest_file, manifest)
    with pytest.raises(AssertionError, match="effective seed not confirmed"):
        verify_axis(body_run, "body")


def test_rejects_seed_not_applied_despite_matching_repeat_rng_hashes(body_run):
    receipt_file = body_run / "body" / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    for run in receipt["runs"]:
        run["rng_state_before_sha256"] = "0" * 64
    rewrite_json(receipt_file, receipt)
    with pytest.raises(AssertionError, match="seed not applied to CPU RNG"):
        verify_axis(body_run, "body")


def test_rejects_run_with_unconfirmed_seed(body_run):
    receipt_file = body_run / "body" / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["runs"][0]["effective_seed"] = None
    rewrite_json(receipt_file, receipt)
    with pytest.raises(AssertionError, match="body arm 0: seed mismatch"):
        verify_axis(body_run, "body")
