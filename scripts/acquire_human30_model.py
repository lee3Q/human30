"""Acquire the pinned local CPU model files used by Human30 paired runs."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "runs" / "human30_repro"
MODEL = EVIDENCE / "model"


def main() -> int:
    provenance = json.loads((EVIDENCE / "body" / "manifest.json").read_text(encoding="utf-8"))["model_provenance"]
    if provenance["id"] != "HuggingFaceTB/SmolLM2-135M-Instruct" or provenance["revision"] != "12fd25f77366fa6b3b4b768ec3050bf629380bac":
        raise ValueError("unexpected model identity or revision")
    if provenance["files"]["model.safetensors"] != "5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c":
        raise ValueError("unexpected model weight SHA-256")
    MODEL.mkdir(parents=True, exist_ok=True)
    for name, expected in provenance["files"].items():
        if name != Path(name).name:
            raise ValueError(f"unsafe model filename: {name}")
        target = MODEL / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            print(f"{name}: SHA-256 verified (existing)")
            continue
        url = provenance["acquisition"]["url_template"].format(
            id=provenance["id"], revision=provenance["revision"], file=name
        )
        temporary = target.with_name(target.name + ".download")
        digest = hashlib.sha256()
        try:
            with urllib.request.urlopen(url, timeout=120) as source, temporary.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
            if digest.hexdigest() != expected:
                raise ValueError(f"{name}: downloaded SHA-256 mismatch")
            temporary.replace(target)
            print(f"{name}: SHA-256 verified (downloaded)")
        finally:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
