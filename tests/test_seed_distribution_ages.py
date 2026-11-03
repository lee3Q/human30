"""Distribution display supports the generator's school/current/past age fields."""
from collections import Counter
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest
from scripts import verify_seed

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('seed', [1, 2])
def test_public_seed_distribution_completes_without_modifying_input(seed, tmp_path):
    source = ROOT / 'runs' / f'seed_{seed:03d}.json'
    before = hashlib.sha256(source.read_bytes()).digest()
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'verify_seed.py'), str(seed)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not result.stderr
    assert '키: 평균=' in result.stdout
    if seed == 2:
        assert '학교 유형 (18세 이하):' in result.stdout
        assert '대학 tier (19~25세):' in result.stdout
        assert '과거 대학 tier (26세 이상):' in result.stdout
    assert hashlib.sha256(source.read_bytes()).digest() == before


def test_education_distribution_uses_each_age_boundary_and_legacy_field():
    def char(age, field):
        result = {'korea': {'education': {field: field}}}
        if age is not None:
            result['age'] = age
        return result
    chars = [char(18, 'school_type'), char(19, 'university_tier'),
             char(25, 'university_tier'), char(26, 'university_tier_past'),
             char(None, 'university_tier')]
    groups = verify_seed.education_distributions(chars)
    assert groups == {
        '학교 유형 (18세 이하)': Counter({'school_type': 1}),
        '대학 tier (19~25세)': Counter({'university_tier': 2}),
        '대학 tier (나이 미기록)': Counter({'university_tier': 1}),
        '과거 대학 tier (26세 이상)': Counter({'university_tier_past': 1}),
    }
    assert sum(sum(counts.values()) for counts in groups.values()) == len(chars)


def test_missing_age_specific_education_is_not_silently_invented():
    with pytest.raises(KeyError, match='school_type'):
        verify_seed.education_distributions([{'age': 17, 'korea': {'education': {'university_tier': 'wrong age field'}}}])
