"""Existing card CLI rejects ordinary input errors without mutating seeds."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / 'scripts/card.py'), *args],
                          cwd=ROOT, capture_output=True, text=True)


def test_missing_seed_is_actionable_not_traceback():
    result = run('999999', '1')
    assert result.returncode == 2
    assert '먼저 생성' in result.stderr
    assert 'Traceback' not in result.stderr
    assert result.stdout == ''


def test_bad_seed_and_character_arguments_are_input_errors():
    for args in [('bad', '1'), ('-1', '1'), ('1', 'bad'), ('1', 'all', '1')]:
        result = run(*args)
        assert result.returncode == 2
        assert 'Traceback' not in result.stderr
        assert result.stdout == ''


def test_missing_id_refuses_whole_request_before_partial_output():
    result = run('1', '1', '999')
    assert result.returncode == 2
    assert '999' in result.stderr
    assert 'all' in result.stderr
    assert result.stdout == ''


def test_input_error_then_valid_retry_leaves_seed_unchanged():
    path = ROOT / 'runs/seed_001.json'
    before = path.read_bytes()
    assert run('1', '999').returncode == 2
    result = run('1', '5')
    assert result.returncode == 0
    assert result.stdout.strip()
    assert path.read_bytes() == before


def test_help_does_not_try_to_read_seed():
    result = run('--help')
    assert result.returncode == 0
    assert result.stderr == ''
    assert '시드' in result.stdout


def test_unreadable_json_errors_do_not_change_file(tmp_path):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    (scripts / 'card.py').write_bytes((ROOT / 'scripts/card.py').read_bytes())
    runs = tmp_path / 'runs'
    runs.mkdir()
    for payload in [b'{partial', b'\xff']:
        path = runs / 'seed_001.json'
        path.write_bytes(payload)
        result = subprocess.run([sys.executable, str(scripts / 'card.py'), '1', '1'],
                                capture_output=True, text=True)
        assert result.returncode == 2
        assert 'JSON' in result.stderr
        assert 'Traceback' not in result.stderr
        assert path.read_bytes() == payload
