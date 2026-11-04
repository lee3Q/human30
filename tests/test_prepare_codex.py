"""Preparation only: never invoke Codex, credentials or a model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/prepare_codex.py'
spec = importlib.util.spec_from_file_location('prepare_codex', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_exact_allowlist_content_and_hashes():
    bundle = module.build_bundle()
    assert bundle['model_called'] is False
    assert [s['path'] for s in bundle['sources']] == list(module.SOURCES)
    for source in bundle['sources']:
        raw = (ROOT / source['path']).read_bytes()
        assert source['content'].encode() == raw
        assert source['sha256'] == hashlib.sha256(raw).hexdigest()
        assert source['bytes'] == len(raw)
    cast = json.loads(bundle['sources'][0]['content'])['characters']
    assert len(cast) == 30


def test_summary_has_no_source_content():
    p = subprocess.run([sys.executable, str(SCRIPT), '--summary'], capture_output=True)
    assert p.returncode == 0 and not p.stderr
    x = json.loads(p.stdout)
    assert all('content' not in s for s in x['sources'])


def test_run_from_outside_checkout_without_output_files(tmp_path):
    before = list(tmp_path.iterdir())
    p = subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp_path, capture_output=True)
    assert p.returncode == 0 and json.loads(p.stdout)['model_called'] is False
    assert list(tmp_path.iterdir()) == before


def test_no_provider_or_process_calls(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError('provider/process must not be invoked')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    assert module.build_bundle()['model_called'] is False


@pytest.mark.parametrize('change', ['missing', 'utf8', 'json', 'underage', 'id', 'count'])
def test_bad_inputs_rejected(tmp_path, change):
    for relative in module.SOURCES:
        p = tmp_path / relative; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / relative).read_bytes())
    seed = tmp_path / module.SOURCES[0]
    if change == 'missing':
        seed.unlink()
    elif change == 'utf8':
        seed.write_bytes(b'\xff')
    elif change == 'json':
        seed.write_text('{')
    else:
        data = json.loads(seed.read_text())
        if change == 'underage': data['characters'][0]['age'] = 17
        elif change == 'id': data['characters'][0]['id'] = 2
        else: data['characters'].pop()
        seed.write_text(json.dumps(data))
    with pytest.raises((OSError, UnicodeError, ValueError)):
        module.build_bundle(tmp_path)
