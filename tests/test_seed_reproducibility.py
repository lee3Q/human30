"""Sampling repeats for a fixed seed, while acquisition timestamps stay truthful."""

import json
from datetime import datetime

from scripts import generate_seed as generator


def test_same_seed_repeats_content_but_records_actual_generation_time(tmp_path, monkeypatch):
    class Clock:
        value = '2026-11-03T11:00:00+09:00'

        @classmethod
        def now(cls, tz):
            return datetime.fromisoformat(cls.value).astimezone(tz)

    monkeypatch.setattr(generator, 'datetime', Clock)
    monkeypatch.setattr(generator, 'RUNS_DIR', tmp_path)
    monkeypatch.setattr(generator.sys, 'argv', ['generate_seed.py', '99'])
    generator.main()
    path = tmp_path / 'seed_099.json'
    first_bytes = path.read_bytes()
    first = json.loads(first_bytes)
    Clock.value = '2026-11-03T11:00:01+09:00'
    generator.main()
    second_bytes = path.read_bytes()
    second = json.loads(second_bytes)
    assert first_bytes != second_bytes
    assert first.pop('generated_at') == '2026-11-03T11:00:00+09:00'
    assert second.pop('generated_at') == '2026-11-03T11:00:01+09:00'
    assert first == second
    assert len(first['characters']) == 30
