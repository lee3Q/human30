"""Read-only text cards use actual ages and each stored education schema."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from scripts import card

ROOT = Path(__file__).resolve().parents[1]
CHARS = json.loads((ROOT / 'runs/seed_002.json').read_text(encoding='utf-8'))['characters']


@pytest.mark.parametrize('cid', [1, 4, 5, 15, 16, 30])
def test_each_age_branch_renders_without_invented_current_university(cid):
    c = CHARS[cid - 1]
    rk = card.compute_rankings(CHARS)
    output = card.make_card(c, rk)
    assert f"{c['age']}세" in card.render_header(c)
    assert f"{c['age']}세" in card.render_summary(c, rk)
    assert f"{c['age']}세" in card.render_narrative(c, rk)
    ed = c['korea']['education']
    if c['age'] <= 18:
        assert f"학교: {ed['current_status']} / {ed['school_type']}" in output
        assert '수능' not in card.render_korea(c)
        assert '현재 대학' not in output
    elif c['age'] >= 26:
        assert f"과거 대학: {ed['university_tier_past']} ({ed['major_past']})" in output
        assert f"현재 상태: {ed['current_status']}" in output
        assert f"현재 {ed['university_tier_past']}" not in output
    else:
        assert f"→ 수능 {ed['suneung_grade']} → {ed['university_tier']}" in output


def test_all_public_seed2_cards_finish_from_external_cwd_without_input_changes(tmp_path):
    source = ROOT / 'runs/seed_002.json'
    before = source.read_bytes()
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/card.py'), '2', 'all'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not result.stderr
    assert result.stdout.count('■ 종합 한 줄') == 30
    assert result.stdout.count('■ 스토리') == 30
    assert source.read_bytes() == before


def test_age_missing_is_not_reported_as_twenty():
    c = copy.deepcopy(CHARS[4])
    del c['age']
    rk = card.compute_rankings([c])
    for output in [card.render_header(c), card.render_summary(c, rk), card.render_narrative(c, rk)]:
        assert '나이 미기록' in output
        assert '20세' not in output


def test_seed1_twenty_year_old_output_is_byte_compatible(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/card.py'), '1', 'all'],
                            cwd=tmp_path, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert hashlib.sha256(result.stdout).hexdigest() == '9560e55bb8dfe8c4c82649201bf83a179bd83339162b42efd2ac9ebc18c2f48b'


@pytest.mark.parametrize('index,field', [(0, 'school_type'), (4, 'university_tier'), (15, 'university_tier_past')])
def test_missing_age_specific_fields_fail_without_fabricating_details(index, field):
    c = copy.deepcopy(CHARS[index])
    del c['korea']['education'][field]
    with pytest.raises(KeyError, match=field):
        card.education_context(c)


def test_past_top_tier_is_not_a_current_university_in_narrative():
    c = copy.deepcopy(CHARS[15])
    c['korea']['education']['university_tier_past'] = 'SKY (합성 과거 대학)'
    c['memory']['ace']['total'] = 4
    text = card.render_narrative(c, card.compute_rankings([c]))
    assert '과거 SKY' in text
    assert '현재 SKY' not in text
