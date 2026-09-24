"""Refresh the bounded claim verdict after generating local Human30 evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_human30_report import CLAIMS, VERDICT_PATH, evidence_files
from scripts.verify_human30_repro import verify_axis
from human30.paired import AXES


def main() -> int:
    for axis in AXES:
        verify_axis(ROOT / "runs" / "human30_repro", axis)
    verdict = {
        "schema_version": 1,
        "claims": {
            key: {"status": status, "scope": scope}
            for key, (status, scope) in CLAIMS.items()
        },
        "evidence_sha256": {
            path.as_posix(): hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in evidence_files()
        },
    }
    target = ROOT / VERDICT_PATH
    target.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {VERDICT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
