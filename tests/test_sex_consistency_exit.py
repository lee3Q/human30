"""Existing consistency findings must fail the command, not silently exit zero."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def character(sex='M', concern=None, health=None):
    return {'id': 1, 'sex': sex, 'body': {'self_image': {'focused_concern': concern or []},
                                      'chronic_health': health or []}}


def run_isolated(tmp_path, chars):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copy2(ROOT / 'scripts/check_sex_consistency.py', scripts)
    runs = tmp_path / 'runs'
    runs.mkdir()
    source = runs / 'seed_099.json'
    source.write_text(json.dumps({'characters': chars}, ensure_ascii=False), encoding='utf-8')
    before = source.read_bytes()
    result = subprocess.run([sys.executable, str(scripts / 'check_sex_consistency.py'), '99'],
                            cwd=tmp_path, text=True, capture_output=True)
    assert source.read_bytes() == before
    assert not result.stderr
    return result


@pytest.mark.parametrize('record,expected', [
    (character('M', ['가슴 크기']), "M focused_concern에 '가슴 크기'"),
    (character('F', ['성기 크기']), "F focused_concern에 '성기 크기'"),
    (character('F', health=[{'condition': '여유증', 'severity': '합성'}]), 'F 여유증 보유'),
])
def test_existing_error_finding_has_nonzero_exit(tmp_path, record, expected):
    result = run_isolated(tmp_path, [record])
    assert result.returncode == 1
    assert '=== 오류 ===' in result.stdout
    assert expected in result.stdout
    assert '✓ 성별 교차 오류 없음' not in result.stdout
    assert 'focused_concern 샘플' in result.stdout


def test_clean_male_gyno_finding_is_information_not_failure(tmp_path):
    result = run_isolated(tmp_path, [character('M', health=[{'condition': '여유증', 'severity': '합성'}])])
    assert result.returncode == 0
    assert '✓ 성별 교차 오류 없음' in result.stdout
    assert '=== 여유증 1명 ===' in result.stdout


def test_multiple_findings_are_reported_before_failure(tmp_path):
    records = [character('M', ['가슴 크기']), character('F', ['성기 크기'])]
    records[1]['id'] = 2
    result = run_isolated(tmp_path, records)
    assert result.returncode == 1
    assert "#01 M focused_concern" in result.stdout
    assert "#02 F focused_concern" in result.stdout


@pytest.mark.parametrize('seed', [1, 2])
def test_stored_public_seed_clean_exit_and_input_bytes_unchanged(seed, tmp_path):
    source = ROOT / 'runs' / f'seed_{seed:03d}.json'
    before = hashlib.sha256(source.read_bytes()).digest()
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_sex_consistency.py'), str(seed)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert '✓ 성별 교차 오류 없음' in result.stdout
    assert not result.stderr
    assert hashlib.sha256(source.read_bytes()).digest() == before
