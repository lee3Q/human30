# Runs — 시드 및 시뮬레이션 산출물

이 폴더에는 기본 제공되는 30인 군상 시드 JSON과 시뮬레이션·반사실 실험 산출물이 저장됩니다.

## 기본 포함 시드

- `seed_001.json` — 시드 1 (20세 기준 30인, 남 15 / 여 15)
- `seed_002.json` — 시드 2 (17~35세 다연령 슬롯 기반 30인, 남 15 / 여 15)
- `seed_003.json` — 시드 3 (20세 기준 30인)
- `seed_042.json` — 시드 42 (20세 기준 30인)
- `seed_999.json` — 시드 999 (20세 기준 30인)

새 시드를 생성하려면:

```bash
python3 -m human30 generate 7
```

## 시뮬레이션 및 반사실 검증 기록

- `seed_001_S002_vote1.md` — 시드 1 × 의무 파트너 지목 투표(`SC06`/`S002`) 30인 전체 내면·선택 기록
- `public_counterfactual/` — 단일축(`body`, `memory`, `identity`, `world_model`) 반사실 실험 및 독립 검증(`human30.evaluate`) 예제
