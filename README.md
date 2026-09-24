# 30p — 인간30 시뮬레이터

> 사회화 벗긴 30명의 인간이 한 무대에서 어떻게 움직이는가를 실시간으로 관찰하는 사고실험 도구.
> 학술도 제품도 아닌 **사적 컨텐츠 + 작가의 노트북**.

## 30초 요약

30명 캐릭터가 각자의 동기/두려움/신체/성격/기억을 가지고 무대에 들어간다. 도덕·예의·체면은 제외 — 진심을 본다. 사용자는 **무명의 절대자**. 관찰 명령 3종: `x-ray` (속마음) / `phone` (디지털 발자국) / `subconscious` (본인도 모르는 부분).

## 빠른 시작

**1분 안에 실행**: [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

```bash
python3 scripts/generate_seed.py 1    # 시드 생성 → runs/seed_001.json
python3 scripts/card.py 1 all          # 30명 카드 출력
```

시뮬레이션 실행: [`docs/PORTABLE_PROMPT.md`](docs/PORTABLE_PROMPT.md)를 아무 LLM에 붙여넣기. Claude·GPT-4o·Gemini 어디든 동작.

## 무엇이 아닌가

- **글이 아니다.** 책처럼 읽히는 출력은 의도적 거부. 흐름·tick 단위
- **Generative Agents가 아니다.** 사회화된 일상이 아니라 사회화 벗긴 본성
- **뇌 시뮬레이션이 아니다.** 일상에서 하는 사람 예측을 30명분 외부화한 장치

## 데이터 모델 4층 (28 옵션 표)

| 층 | 파일 | 표 수 | 내용 |
|---|---|---|---|
| Body | `tables/body.json` | 11 | 신체·건강·외모 |
| Memory | `tables/memory.json` | 11 | 과거 흔적·트라우마·향수 |
| Identity | `tables/identity.json` | 3 | 인지·성·충동 |
| Korea | `tables/korea.json` | 3 | 한국 특화 (이름·직업·교육) |

## 파일맵

```
30p/
├── CLAUDE.md                ← Claude Code 세션 루틴·절대 원칙
├── README.md                ← 이 파일 (프로젝트 진입)
├── docs/
│   ├── QUICKSTART.md        ← 1분 실행 가이드
│   ├── PORTABLE_PROMPT.md   ← LLM 불문 시스템 프롬프트 (독립 실행 핵심)
│   ├── session_flow.md      ← 시뮬 모드 명세 (명령·시간·포맷)
│   ├── observation_commands.md  ← x-ray/phone/subconscious 상세
│   ├── generation_protocol.md   ← 시드 생성 규칙
│   └── operating.md         ← 운영 매뉴얼
├── scripts/
│   ├── generate_seed.py     ← 시드 생성 (stdlib, 비트 재현)
│   ├── card.py              ← 캐릭터 카드 터미널 출력
│   ├── card_renderer.html   ← 브라우저 카드 렌더링
│   ├── summarize_seed.py    ← 30명 1줄 요약
│   ├── verify_seed.py       ← 분포 검증
│   ├── inspect_char.py      ← 개별 캐릭터 상세
│   ├── check_sex_consistency.py  ← 성 분포 일관성 체크
│   └── test_pipeline.sh     ← 전체 파이프라인 테스트
├── tables/                  ← 옵션 표 4층 28개 (body/memory/identity/korea)
├── runs/                    ← 시드별 30명 결과물 (seed_001.json 등)
├── .state/                  ← 세션 간 상태 (current/queue/log/handoffs)
├── play/                    ← Claude Code 시뮬 모드 진입점
├── stages/                  ← 무대 카탈로그
├── scenarios/               ← 시나리오
├── data/                    ← 시드 0 보존 (참고용)
├── research/                ← 1차 리서치
└── runs/self/               ← 자기 분석 (Shadow 16개·프라이머·싸움 프로토콜)
```

## 현재 상태 (2026-04-24)

| 항목 | 상태 |
|---|---|
| 시드 생성 | 완료. `generate_seed.py` 안정 동작 |
| 카드 출력 | 완료. 터미널(card.py) + 브라우저(card_renderer.html) |
| PORTABLE_PROMPT | 완료. Claude/GPT/Gemini 독립 실행 가능 |
| 파이프라인 테스트 | 완료. `test_pipeline.sh` 전체 동작 검증 |
| identity v0.3 | 완료. 성소수자 분포 정상화 + IQ 하위 꼬리 축소 |
| region 버그 | 수정. roll_korea가 slot region override |

### 다음 마일스톤

1. **실전 검증** (4/30 데드라인) — 이상규가 직접 PORTABLE_PROMPT로 시뮬 돌려보기
2. **스킬 패키징** — Claude Code 스킬로 변환 (큐 2순위)
3. **나다움 공식 적용** — 기존 나 × 새로움 관점에서 30p 정체 재확인

## 의존성 정책

**외부 패키지 0** (공급망 공격 방어). stdlib만 사용. 언어 무관.

## 미학적 좌표

Ari Aster · Gaspar Noé · 다자이 오사무 · 카뮈. 정화 없는 관찰. 구원 없는 결말. 외부자의 냉정한 시선.
# Paired counterfactual experiment

The public, one-condition-at-a-time experiment and its independent evaluation are documented in [runs/public_counterfactual/README.md](runs/public_counterfactual/README.md). The example set distinguishes hand-authored fixtures from five recorded actual-model pairs and states the seed-control and repeatability limits explicitly.

## Local CPU model reproduction

The four-axis [local run evidence](runs/human30_repro/README.md) uses the exact
SmolLM2-135M-Instruct model commit `12fd25f77366fa6b3b4b768ec3050bf629380bac`
and checks the SHA-256 of every downloaded model file. From the repository root:

```sh
uv run --group dev python scripts/acquire_human30_model.py
uv run --no-project --python 3.10 --with torch==2.10.0 --with transformers==4.51.3 --with safetensors==0.5.3 python -m scripts.run_local_human30_pairs --axes body memory identity world_model
uv run --group dev python scripts/build_human30_report.py
uv run --group dev python scripts/verify_human30_repro.py
uv run --group dev python scripts/verify_human30_report.py
uv run --group dev python -m pytest -q
```

The runner applies seed 42 to each independent CPU generation and stores two
raw responses for each arm. The model weight is downloaded at the pinned commit
and excluded from Git. This local result does not establish provider seed
application, personal prediction, or a causal effect on people.
