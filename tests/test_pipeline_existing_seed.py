"""A pipeline smoke test must not overwrite or delete an existing seed."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('seed', ['99', '1'])
@pytest.mark.parametrize('kind', ['file', 'symlink', 'dangling', 'directory'])
def test_pipeline_refuses_existing_seed_before_generation(tmp_path, seed, kind):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    runs = tmp_path / 'runs'
    runs.mkdir()
    shutil.copyfile(ROOT / 'scripts' / 'test_pipeline.sh', scripts / 'test_pipeline.sh')
    # If the preflight fails to stop, leave an observable generation marker.
    (scripts / 'generate_seed.py').write_text(
        "from pathlib import Path\nPath(__file__).resolve().parents[1].joinpath('generator-ran').touch()\n",
        encoding='utf-8',
    )
    destination = runs / f'seed_{int(seed):03d}.json'
    target = tmp_path / 'original.json'
    if kind == 'file':
        destination.write_bytes(b'original seed bytes\n')
    elif kind == 'directory':
        destination.mkdir()
    else:
        if kind == 'symlink': target.write_bytes(b'original target bytes\n')
        destination.symlink_to(target)
    result = subprocess.run(['bash', str(scripts / 'test_pipeline.sh'), seed],
                            cwd=tmp_path, text=True, capture_output=True)
    assert not (tmp_path / 'generator-ran').exists()
    assert result.returncode == 2
    assert '기존 시드 경로를 보호하기 위해 중단' in result.stderr
    assert '전체 통과' not in result.stdout
    if kind == 'file': assert destination.read_bytes() == b'original seed bytes\n'
    if kind == 'directory': assert destination.is_dir()
    if kind in ('symlink', 'dangling'): assert destination.is_symlink()
    if kind == 'symlink': assert target.read_bytes() == b'original target bytes\n'
    if kind == 'dangling': assert not target.exists()
