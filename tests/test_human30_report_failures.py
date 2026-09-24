"""Reject resume verdicts that exceed or misstate the local evidence."""

import json
import sys
from pathlib import Path

import pytest

from scripts import verify_human30_report as report


VERDICT = report.ROOT / report.VERDICT_PATH


@pytest.fixture
def verdict():
    return json.loads(VERDICT.read_text(encoding="utf-8"))


@pytest.mark.parametrize("claim", [
    "provider_reproducibility",
    "personal_prediction",
    "causal_effect",
])
def test_rejects_promoted_unsupported_claim(verdict, claim):
    verdict["claims"][claim]["status"] = "verified"
    with pytest.raises(AssertionError, match=f"unsupported claim: {claim}"):
        report.verify_verdict(verdict)


def test_rejects_changed_evidence_hash(verdict):
    path = next(iter(verdict["evidence_sha256"]))
    verdict["evidence_sha256"][path] = "0" * 64
    with pytest.raises(AssertionError, match="evidence hash mismatch"):
        report.verify_verdict(verdict)


def test_cli_rejects_invalid_verdict(tmp_path, verdict, monkeypatch, capsys):
    verdict["claims"]["provider_reproducibility"]["status"] = "verified"
    path = tmp_path / "invalid_verdict.json"
    path.write_text(json.dumps(verdict), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["verify_human30_report.py", "--verdict", str(path)])

    assert report.main() == 1
    assert "FAIL: unsupported claim: provider_reproducibility" in capsys.readouterr().err
