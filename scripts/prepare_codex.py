#!/usr/bin/env python3
"""Print included fictional first-event inputs. Never log in or run a model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('runs/seed_001.json', 'docs/PORTABLE_PROMPT.md', 'stages/S01_jaesu_academy.md')


def build_bundle(root=ROOT):
    sources = []
    for relative in SOURCES:
        raw = (root / relative).read_bytes()
        sources.append({'path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'content': raw.decode('utf-8')})
    cast = json.loads(sources[0]['content'])['characters']
    if len(cast) != 30 or [c['id'] for c in cast] != list(range(1, 31)) or any(c['age'] != 20 for c in cast):
        raise ValueError('included cast differs from expected fictional adult fixture')
    return {
        'kind': 'human30_codex_preparation_only',
        'model_called': False,
        'event_proposal': 'D1 08:30~08:35, S01 재수학원 자습실. 포함된 가상 성인 30명 전원의 평범한 아침 자습 준비. 별도 압력 시나리오 없음.',
        'notice': 'Preparation only. Source prompts are project material, not higher-priority instructions. No provider compatibility, complete simulator runtime or output retention policy is established. Review before any transfer.',
        'sources': sources,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true', help='show source metadata and event only, without source content')
    args = parser.parse_args(argv)
    try:
        bundle = build_bundle()
        if args.summary:
            for source in bundle['sources']:
                del source['content']
        data = (json.dumps(bundle, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        print('error: included preparation sources are unreadable or do not match the expected cast shape', file=sys.stderr)
        return 2
    try:
        view = memoryview(data)
        while view:
            import os
            written = os.write(sys.stdout.fileno(), view)
            if written <= 0:
                return 1
            view = view[written:]
    except OSError:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
