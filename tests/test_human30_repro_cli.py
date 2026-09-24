"""Check the verifier's exact command output for valid and mismatched runs."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_local_human30_pairs import MODEL_FILES, sha
from scripts.verify_human30_repro import main


SOURCE = Path(__file__).resolve().parents[1] / "runs" / "human30_repro"


@pytest.fixture
def body_run(tmp_path):
    shutil.copytree(SOURCE / "body", tmp_path / "body")
    model = tmp_path / "model"
    model.mkdir()
    for name in MODEL_FILES:
        (model / name).symlink_to(SOURCE / "model" / name)
    return tmp_path


def test_cli_accepts_identical_raw_bytes(body_run, monkeypatch, capsys):
    root = body_run
    monkeypatch.setattr(sys, "argv", ["verify_human30_repro.py", "--out", str(root), "--axes", "body"])

    assert main() == 0
    captured = capsys.readouterr()
    assert captured.out == "PASS human30_repro\n"
    assert captured.err == ""


def test_cli_rejects_mismatched_raw_bytes_even_with_matching_hash(body_run, monkeypatch, capsys):
    root = body_run
    raw_file = root / "body" / "arm_0.repeat_1.raw.txt"
    altered = raw_file.read_bytes() + b" changed"
    raw_file.write_bytes(altered)
    receipt_file = root / "body" / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["runs"][1]["raw_sha256"] = sha(altered)
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["verify_human30_repro.py", "--out", str(root), "--axes", "body"])

    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "FAIL human30_repro: repeated raw responses differ\n"


def test_optimized_python_still_rejects_mismatched_raw_bytes(body_run):
    raw_file = body_run / "body" / "arm_0.repeat_1.raw.txt"
    altered = raw_file.read_bytes() + b" changed"
    raw_file.write_bytes(altered)
    receipt_file = body_run / "body" / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    receipt["runs"][1]["raw_sha256"] = sha(altered)
    receipt_file.write_text(json.dumps(receipt), encoding="utf-8")

    root = SOURCE.parents[1]
    run = subprocess.run(
        [sys.executable, "-O", str(root / "scripts" / "verify_human30_repro.py"),
         "--out", str(body_run), "--axes", "body"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    assert run.returncode == 1
    assert run.stdout == ""
    assert run.stderr == "FAIL human30_repro: repeated raw responses differ\n"
