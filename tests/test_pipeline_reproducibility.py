"""Exercise the shell pipeline in an isolated synthetic project, never real runs."""
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_pipeline(tmp_path, *, changed):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (tmp_path / "runs").mkdir()
    tables = tmp_path / "tables"
    tables.mkdir()
    for name in ("body", "memory", "identity", "korea"):
        (tables / f"{name}.json").write_text("{}", encoding="utf-8")
    shutil.copyfile(ROOT / "scripts" / "test_pipeline.sh", scripts / "test_pipeline.sh")
    for name in ("verify_seed.py", "summarize_seed.py", "inspect_char.py"):
        (scripts / name).write_text("pass\n", encoding="utf-8")
    (scripts / "card_renderer.html").write_text(
        'loadSeed renderCard <input type="file">', encoding="utf-8")
    (scripts / "generate_seed.py").write_text('''
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
count = root / "counter"
n = int(count.read_text()) + 1 if count.exists() else 1
count.write_text(str(n))
character = dict(sex="M", age=20, body={}, memory={}, identity={}, korea={})
characters = [{**character, "id": i} for i in range(30)]
if CHANGED:
    characters[0]["age"] += n
payload = {"seed": int(sys.argv[1]), "generated_at": str(n), "characters": characters}
(root / "runs" / f"seed_{int(sys.argv[1]):03d}.json").write_text(json.dumps(payload))
'''.replace("CHANGED", repr(changed)), encoding="utf-8")
    # The shell calls python3. Pin that name to this test interpreter.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys.executable)
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]}
    env.pop("PYTHONOPTIMIZE", None)
    result = subprocess.run(["bash", str(scripts / "test_pipeline.sh")],
                            cwd=tmp_path, env=env, text=True, capture_output=True)
    assert (tmp_path / "counter").read_text() == "2"
    assert not (tmp_path / "runs" / "seed_099.json").exists()
    return result


def test_pipeline_rejects_changed_sampled_content(tmp_path):
    result = run_pipeline(tmp_path, changed=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "재현성 실패 (본문 불일치)" in result.stdout
    assert "전체 통과" not in result.stdout


def test_pipeline_accepts_only_timestamp_difference(tmp_path):
    result = run_pipeline(tmp_path, changed=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "재현성 확인 (generated_at 제외 후 동일)" in result.stdout
    assert "FAIL=0" in result.stdout
