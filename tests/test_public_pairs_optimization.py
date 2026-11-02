"""Evidence checks must not disappear when Python optimization is enabled."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'runs' / 'public_counterfactual'


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('mutation', ['axis', 'scenario_hash', 'output_hash', 'conditions', 'receipt', None])
def test_public_pair_checks_survive_optimization(tmp_path, optimized, mutation):
    pair = PUBLIC / 'body.pair.json'
    manifest = json.loads((PUBLIC / 'body.manifest.json').read_text(encoding='utf-8'))
    receipt = tmp_path / 'receipt.json'
    if mutation == 'axis':
        manifest['axis'] = 'memory'
    elif mutation == 'scenario_hash':
        manifest['scenario_sha256'] = '0' * 64
    elif mutation == 'output_hash':
        manifest['output_sha256'][0] = '0' * 64
    elif mutation == 'conditions':
        manifest['condition_vectors'][1] = manifest['condition_vectors'][0]
    elif mutation == 'receipt':
        receipt.write_text('{}', encoding='utf-8')
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    code = (
        'from pathlib import Path; from scripts.verify_public_pairs import verify; '
        f'verify(Path({str(pair)!r}), Path({str(path)!r}), Path({str(receipt)!r}), "body")'
    )
    run = subprocess.run([sys.executable, *(['-O'] if optimized else []), '-c', code],
                         cwd=ROOT, capture_output=True, text=True, check=False)
    assert run.returncode == (0 if mutation is None else 1), run.stderr
    if mutation is not None:
        assert 'public pair evidence check failed' in run.stderr


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('mutation', ['provider', 'seed', 'request_hash', 'response_id', 'codex_seed', None])
def test_full_cli_rejects_bad_provenance_without_writing_receipt(tmp_path, optimized, mutation):
    import os
    import shutil

    # A private fixture checkout: never modify the committed evidence in place.
    repo = tmp_path / 'repo'
    for directory in ['human30', 'scripts']:
        shutil.copytree(ROOT / directory, repo / directory,
                        ignore=shutil.ignore_patterns('__pycache__'))
    public = repo / 'runs' / 'public_counterfactual'
    shutil.copytree(PUBLIC, public)
    codex = mutation == 'codex_seed'
    path = public / ('actual_codex_body/manifest.json' if codex else 'actual_seeded/body/manifest.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    if mutation == 'provider':
        data['response_provenance'][0]['provider'] = 'wrong'
    elif mutation == 'seed':
        data['requested_model_seed'] = data['seed'] = 41
    elif mutation == 'request_hash':
        data['response_provenance'][0]['request_sha256'] = '0' * 64
    elif mutation == 'response_id':
        data['response_provenance'][0]['response_id'] = ''
    elif codex:
        data['settings']['sampling_seed_supported'] = True
    if mutation is not None:
        path.write_text(json.dumps(data), encoding='utf-8')
    output = tmp_path / 'new-receipt.json'
    env = {key: value for key, value in os.environ.items()
           if key not in ('PYTHONPATH', 'PYTHONOPTIMIZE')}
    run = subprocess.run([sys.executable, *(['-O'] if optimized else []),
                          '-m', 'scripts.verify_public_pairs', '--out', str(output)],
                         cwd=repo, capture_output=True, text=True, check=False, env=env)
    if mutation is None:
        assert run.returncode == 0, run.stderr
        assert output.read_bytes() == (PUBLIC / 'verification_receipt.json').read_bytes()
        assert len(json.loads(output.read_text())['verified_runs']) == 9
    else:
        assert run.returncode != 0
        assert run.stdout == ''
        assert 'public pair evidence check failed' in run.stderr
        assert not output.exists()
