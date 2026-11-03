"""Check the verifier's exact command output for valid and mismatched runs."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_local_human30_pairs import sha
from scripts.verify_human30_repro import main


SOURCE = Path(__file__).resolve().parents[1] / "runs" / "human30_repro"


@pytest.fixture
def body_run(repro_root):
    return repro_root


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
    patch = (
        "import json, sys;"
        "from pathlib import Path;"
        f"sys.path.insert(0, {str(root)!r});"
        "import scripts.verify_human30_repro as repro;"
        "repro.PINNED_MODEL_FILES = json.loads(Path(sys.argv.pop(1)).read_text(encoding='utf-8'));"
        "sys.argv[0] = 'verify_human30_repro.py';"
        "raise SystemExit(repro.main())"
    )
    run = subprocess.run(
        [sys.executable, "-O", "-c", patch,
         str(body_run / "model_files_pin.json"), "--out", str(body_run), "--axes", "body"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    assert run.returncode == 1
    assert run.stdout == ""
    assert run.stderr == "FAIL human30_repro: repeated raw responses differ\n"


def test_verifier_accepts_absolute_evidence_from_another_working_directory(body_run, tmp_path):
    root = SOURCE.parents[1]
    patch = (
        "import json, sys;"
        "from pathlib import Path;"
        f"sys.path.insert(0, {str(root)!r});"
        "import scripts.verify_human30_repro as repro;"
        "repro.PINNED_MODEL_FILES = json.loads(Path(sys.argv.pop(1)).read_text(encoding='utf-8'));"
        "sys.argv[0] = 'verify_human30_repro.py';"
        "raise SystemExit(repro.main())"
    )
    run = subprocess.run(
        [sys.executable, "-c", patch,
         str(body_run / 'model_files_pin.json'), '--out', str(body_run), '--axes', 'body'],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout == 'PASS human30_repro\n'
    assert run.stderr == ''
