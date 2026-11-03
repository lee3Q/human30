"""generate_seed.py must not silently overwrite or write through an existing seed path."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _make_tree(tmp_path):
    for d in ("scripts", "tables", "data", "runs"):
        (tmp_path / d).mkdir()
    shutil.copyfile(ROOT / "scripts" / "generate_seed.py", tmp_path / "scripts" / "generate_seed.py")
    for layer in ("body", "memory", "identity", "korea"):
        shutil.copyfile(ROOT / "tables" / f"{layer}.json", tmp_path / "tables" / f"{layer}.json")
    shutil.copyfile(ROOT / "data" / "personas.json", tmp_path / "data" / "personas.json")
    return tmp_path / "scripts" / "generate_seed.py"


def _run(script, *args):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)


def _seed_file(tmp_path):
    return tmp_path / "runs" / "seed_042.json"


def _place(tmp_path, kind, outside):
    seed_file = _seed_file(tmp_path)
    if kind == "file":
        seed_file.write_bytes(b"original seed bytes\n")
    elif kind == "directory":
        seed_file.mkdir()
    elif kind == "symlink":
        outside.write_bytes(b"outside target bytes\n")
        seed_file.symlink_to(outside)
    elif kind == "dangling":
        seed_file.symlink_to(outside)  # outside is never created
    return seed_file


@pytest.mark.parametrize("kind", ["file", "symlink", "dangling", "directory"])
def test_generate_seed_refuses_existing_seed_path(tmp_path, kind):
    script = _make_tree(tmp_path)
    outside = tmp_path / "outside.json"
    seed_file = _place(tmp_path, kind, outside)

    result = _run(script, "42")
    assert result.returncode == 2
    assert "--force" in result.stdout
    if kind == "file":
        assert seed_file.read_bytes() == b"original seed bytes\n"
    elif kind == "directory":
        assert seed_file.is_dir()
    else:
        assert seed_file.is_symlink()
        assert not outside.exists() or outside.read_bytes() == b"outside target bytes\n"
    if kind == "dangling":
        assert not outside.exists()


def test_generate_seed_force_replaces_file_and_never_writes_through_symlink(tmp_path):
    script = _make_tree(tmp_path)
    outside = tmp_path / "outside.json"
    seed_file = _place(tmp_path, "symlink", outside)

    forced = _run(script, "42", "--force")
    assert forced.returncode == 0, forced.stderr
    assert not seed_file.is_symlink()
    assert json.loads(seed_file.read_text(encoding="utf-8"))["seed"] == 42
    assert outside.read_bytes() == b"outside target bytes\n"

    again = _run(script, "42", "--force")
    assert again.returncode == 0, again.stderr
    assert json.loads(seed_file.read_text(encoding="utf-8"))["seed"] == 42


def test_generate_seed_force_refuses_directory(tmp_path):
    script = _make_tree(tmp_path)
    seed_file = _place(tmp_path, "directory", tmp_path / "outside.json")

    result = _run(script, "42", "--force")
    assert result.returncode == 2
    assert seed_file.is_dir()


def test_generate_seed_rejects_unknown_options(tmp_path):
    script = _make_tree(tmp_path)
    result = _run(script, "42", "--focre")
    assert result.returncode == 1
    assert "--focre" in result.stderr
    assert not _seed_file(tmp_path).exists()
