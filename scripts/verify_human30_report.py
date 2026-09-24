"""Verify the bounded Human30 resume verdict against local CPU run evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from human30.paired import AXES
from scripts.verify_human30_repro import verify_axis

EVIDENCE_ROOT = Path("runs/human30_repro")
VERDICT_PATH = EVIDENCE_ROOT / "claim_verdict.json"
CLAIMS = {
    "local_cpu_four_axis_pairs": (
        "verified",
        "Four fictional-scenario axes have locally generated baseline and condition responses, each repeated with identical UTF-8 bytes under the recorded CPU model and applied seed.",
    ),
    "local_manifest_integrity": (
        "verified",
        "The local model, scenario, prompts, runner, seed receipts, and raw response hashes pass the reproducibility verifier.",
    ),
    "provider_reproducibility": (
        "unverified",
        "The local CPU runs do not establish OpenRouter or provider seed application or model snapshot control.",
    ),
    "personal_prediction": (
        "unverified",
        "The fictional shelter scenario contains no observed personal choices against which to test predictive accuracy.",
    ),
    "causal_effect": (
        "unverified",
        "Paired generated responses alone do not establish a causal effect beyond this local setup.",
    ),
}


def evidence_files() -> list[Path]:
    return [EVIDENCE_ROOT / axis / name for axis in AXES for name in ("manifest.json", "receipt.json")]


def verify_verdict(verdict: dict, root: Path = ROOT) -> None:
    """Reject unsupported statuses, wording, evidence paths, or changed evidence."""
    assert type(verdict) is dict and set(verdict) == {"schema_version", "claims", "evidence_sha256"}, "verdict schema mismatch"
    assert verdict["schema_version"] == 1, "verdict schema version mismatch"
    claims = verdict["claims"]
    assert type(claims) is dict and set(claims) == set(CLAIMS), "unsupported or missing claim"
    for key, (status, scope) in CLAIMS.items():
        assert claims[key] == {"status": status, "scope": scope}, f"unsupported claim: {key}"

    expected_paths = {path.as_posix() for path in evidence_files()}
    hashes = verdict["evidence_sha256"]
    assert type(hashes) is dict and set(hashes) == expected_paths, "evidence path mismatch"
    for axis in AXES:
        verify_axis(root / EVIDENCE_ROOT, axis)
    for path in evidence_files():
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        assert hashes[path.as_posix()] == actual, f"evidence hash mismatch: {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verdict", type=Path, default=VERDICT_PATH)
    args = parser.parse_args()
    try:
        verdict = json.loads(args.verdict.read_text(encoding="utf-8"))
        verify_verdict(verdict)
    except (AssertionError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("Human30 resume verdict: PASS (2 verified local claims; 3 broader claims unverified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
