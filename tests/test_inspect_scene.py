"""Synthetic stored-file tests. No model or actual scene fixture."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/inspect_scene.py'


def run(scene, *args):
    return subprocess.run([sys.executable, str(SCRIPT), str(scene), *args], capture_output=True)


@pytest.fixture
def scene(tmp_path):
    root = tmp_path / 'scene'
    root.mkdir()
    (root / 'surface.md').write_text('가상 장면\n', encoding='utf-8')
    for channel in ('interior', 'phone', 'subconscious'):
        (root / channel).mkdir()
        (root / channel / '09.md').write_text(f'합성 {channel}\n', encoding='utf-8')
    return root


@pytest.mark.parametrize('channel', ['surface', 'interior', 'phone', 'subconscious'])
def test_exact_read_no_application_writes(scene, channel):
    before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in scene.rglob('*') if p.is_file()}
    args = [] if channel == 'surface' else ['09']
    result = run(scene, channel, *args)
    target = scene / 'surface.md' if channel == 'surface' else scene / channel / '09.md'
    assert result.returncode == 0 and result.stdout == target.read_bytes() and not result.stderr
    assert before == {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in scene.rglob('*') if p.is_file()}


@pytest.mark.parametrize('identifier', ['0', '31', '-1', 'x', '../9', '９', '', '9' * 5000, '009'])
def test_invalid_ids(scene, identifier):
    result = run(scene, 'interior', identifier)
    assert result.returncode == 2 and not result.stdout


@pytest.mark.parametrize('data', [b'bad\xff', b'escape\x1b[31m', b'carriage\rreturn', b'del\x7f', 'direction\u202e'.encode()])
def test_invalid_content_no_partial_stdout(scene, data):
    (scene / 'surface.md').write_bytes(data)
    result = run(scene, 'surface')
    assert result.returncode == 2 and not result.stdout
    assert data not in result.stderr


def test_missing_conditional_is_not_no_activity(scene):
    (scene / 'phone/09.md').unlink()
    result = run(scene, 'phone', '9')
    assert result.returncode == 2 and not result.stdout
    assert b'no saved observation' in result.stderr and b'does not establish' in result.stderr


@pytest.mark.parametrize('kind', ['scene', 'channel', 'leaf', 'parent'])
def test_symlinks_and_parent_components_refused(scene, tmp_path, kind):
    if kind == 'scene':
        alias = tmp_path / 'alias'; alias.symlink_to(scene, target_is_directory=True); scene = alias
    elif kind == 'channel':
        (scene / 'interior').rename(scene / 'original'); (scene / 'interior').symlink_to(scene / 'original', target_is_directory=True)
    elif kind == 'leaf':
        (scene / 'interior/09.md').unlink(); (scene / 'interior/09.md').symlink_to(scene / 'surface.md')
    else:
        scene = scene / '..' / 'scene'
    result = run(scene, 'interior', '9')
    assert result.returncode == 2 and not result.stdout


def test_fifo_rejected_without_blocking(scene):
    (scene / 'surface.md').unlink(); os.mkfifo(scene / 'surface.md')
    result = run(scene, 'surface')
    assert result.returncode == 2 and not result.stdout


def test_size_cap(scene):
    with (scene / 'surface.md').open('wb') as f:
        f.truncate(8 * 1024 * 1024 + 1)
    result = run(scene, 'surface')
    assert result.returncode == 2 and not result.stdout


def test_help_and_surface_reject_id(scene):
    assert run(scene, 'surface', '9').returncode == 2
    assert subprocess.run([sys.executable, str(SCRIPT), '--help'], capture_output=True).returncode == 0


def test_intermediate_scene_symlink(scene, tmp_path):
    parent_alias = tmp_path / 'parent-alias'
    parent_alias.symlink_to(scene.parent, target_is_directory=True)
    result = run(parent_alias / scene.name, 'surface')
    assert result.returncode == 2 and not result.stdout


def test_permission_error(scene):
    if os.geteuid() == 0:
        pytest.skip('permission test requires unprivileged process')
    target = scene / 'surface.md'
    target.chmod(0)
    try:
        result = run(scene, 'surface')
        assert result.returncode == 2 and not result.stdout and b'Traceback' not in result.stderr
    finally:
        target.chmod(0o600)


def test_directory_leaf(scene):
    (scene / 'surface.md').unlink(); (scene / 'surface.md').mkdir()
    result = run(scene, 'surface')
    assert result.returncode == 2 and not result.stdout


def test_import_has_no_model_dependency():
    import importlib.util
    spec = importlib.util.spec_from_file_location('inspect_scene', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.MAX_BYTES == 8 * 1024 * 1024


def test_unsupported_platform_refuses(monkeypatch, scene):
    import importlib.util
    spec = importlib.util.spec_from_file_location('inspect_scene', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    monkeypatch.setattr(module.os, 'name', 'unsupported')
    with pytest.raises(ValueError, match='unsupported'):
        module.read_saved(str(scene), 'surface', None)


def test_argument_errors_do_not_echo_controls(scene):
    result = run(scene, 'surface', '--unknown\x1b[31m')
    assert result.returncode == 2 and not result.stdout and b'\x1b' not in result.stderr


def test_small_closed_pipe_exits_one_without_shutdown_reflush(scene):
    reader, writer = os.pipe()
    os.close(reader)
    try:
        result = subprocess.run([sys.executable, str(SCRIPT), str(scene), 'surface'], stdout=writer, stderr=subprocess.PIPE)
    finally:
        os.close(writer)
    assert result.returncode == 1 and result.stderr == b''


def test_dev_full_exits_one_without_shutdown_reflush(scene):
    if not Path('/dev/full').exists():
        pytest.skip('/dev/full unavailable')
    with open('/dev/full', 'wb') as sink:
        result = subprocess.run([sys.executable, str(SCRIPT), str(scene), 'surface'], stdout=sink, stderr=subprocess.PIPE)
    assert result.returncode == 1 and result.stderr == b''


def test_short_writes_are_completed(monkeypatch, scene):
    import importlib.util
    spec = importlib.util.spec_from_file_location('inspect_scene', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    captured = bytearray()
    def short_write(fd, data):
        captured.extend(data[:2])
        return min(2, len(data))
    monkeypatch.setattr(module.os, 'write', short_write)
    assert module.main([str(scene), 'surface']) == 0
    assert captured == (scene / 'surface.md').read_bytes()


def test_zero_write_fails_without_loop(monkeypatch, scene):
    import importlib.util
    spec = importlib.util.spec_from_file_location('inspect_scene', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    monkeypatch.setattr(module.os, 'write', lambda fd, data: 0)
    assert module.main([str(scene), 'surface']) == 1


def test_empty_scene_refused_but_explicit_dot_allowed(scene):
    empty = subprocess.run([sys.executable, str(SCRIPT), '', 'surface'], cwd=scene, capture_output=True)
    assert empty.returncode == 2 and not empty.stdout and b'Traceback' not in empty.stderr
    explicit = subprocess.run([sys.executable, str(SCRIPT), '.', 'surface'], cwd=scene, capture_output=True)
    assert explicit.returncode == 0 and explicit.stdout == (scene / 'surface.md').read_bytes()
