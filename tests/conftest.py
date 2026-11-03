"""Run reproducibility-verifier tests without the multi-GB local model weights."""

import json
import shutil
from pathlib import Path

import pytest

from scripts import verify_human30_repro as repro
from scripts.run_local_human30_pairs import MODEL_FILES, sha

SOURCE = Path(__file__).resolve().parents[1] / "runs" / "human30_repro"

# git cannot host the real model.safetensors. The verifier only hashes model
# files, so small synthetic bytes exercise the same pin checks on any machine.
SYNTHETIC_WEIGHTS = b"human30 synthetic test weights\n"
PIN_FILE = "model_files_pin.json"


@pytest.fixture
def repro_root(tmp_path, monkeypatch):
    """Four-axis evidence tree with synthetic weights and matching model pins.

    Returns the tree root; the overridden pin JSON sits at root/PIN_FILE for
    subprocess verifier runs, which load it through a PINNED_MODEL_FILES
    override preamble (see test_human30_repro_cli.py). In-process callers
    are covered by the monkeypatched PINNED_MODEL_FILES.
    """
    root = tmp_path / "runs" / "human30_repro"
    model = root / "model"
    model.mkdir(parents=True)
    pin = dict(repro.PINNED_MODEL_FILES)
    for name in MODEL_FILES:
        if name == "model.safetensors":
            (model / name).write_bytes(SYNTHETIC_WEIGHTS)
            pin[name] = sha(SYNTHETIC_WEIGHTS)
        else:
            (model / name).symlink_to(SOURCE / "model" / name)
    for axis in repro.AXES:
        shutil.copytree(SOURCE / axis, root / axis)
        manifest_path = root / axis / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["model_provenance"]["files"] = pin
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (root / PIN_FILE).write_text(json.dumps(pin, indent=2), encoding="utf-8")
    monkeypatch.setattr(repro, "PINNED_MODEL_FILES", pin)
    return root
