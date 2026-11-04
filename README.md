# 30p — 인간30 시뮬레이터

> 사회화 벗긴 30명의 인간이 한 무대에서 어떻게 움직이는가를 실시간으로 관찰하는 사고실험 도구.
> 학술도 제품도 아닌 **사적 컨텐츠 + 작가의 노트북**.

## 30초 요약

30명 캐릭터가 각자의 동기/두려움/신체/성격/기억을 가지고 무대에 들어간다. 도덕·예의·체면은 제외 — 진심을 본다. 사용자는 **무명의 절대자**. 관찰 명령 3종: `x-ray` (속마음) / `phone` (디지털 발자국) / `subconscious` (본인도 모르는 부분).

## 별도 웹앱: 카톡 통계 → 발견 → 반박

이 저장소에는 아래 캐릭터 시뮬레이터와 별개로 `product/`의 대화 통계 웹앱이 있습니다.
개인 대화 없이 전체 흐름을 확인하려면 합성 데모로 시작하세요:

```bash
python3 product/server.py --demo --port 8000
```

http://localhost:8000 에서 "가상 대화로 시작"을 누릅니다. API 키가 있어도 데모에서는
외부 AI를 호출하지 않습니다. 고정 예시이며 사람·관계 분석 결과가 아닙니다.
일반 모드의 외부 전송·저장 경계와 실행법은 [웹앱 안내](product/README.md)를 보세요.
이 경로는 아래 30명 캐릭터 시뮬레이션을 실행하지 않습니다.

## 빠른 시작

**1분 안에 실행**: [`docs/QUICKSTART.md`](docs/QUICKSTART.md) · English: [`docs/QUICKSTART_EN.md`](docs/QUICKSTART_EN.md)

```bash
python3 scripts/card.py 1 all          # 포함된 시드 1의 30명 카드 바로 출력
python3 scripts/generate_seed.py 7     # 내 시드 생성 → runs/seed_007.json (포함된 번호 1·2·3·42·999는 거부, --force로 덮어쓰기)
```

시뮬레이션은 [`docs/PORTABLE_PROMPT.md`](docs/PORTABLE_PROMPT.md)와 가상 캐릭터 데이터를 사용자가 선택한 LLM에 수동으로 제공하는 경로입니다. 카드·시드 도구가 시뮬레이션을 실행하거나 LLM과 연결하는 것은 아닙니다. 제공자별 호환성·출력 품질은 보장하지 않으며 이 수동 경로는 CI에서 검증하지 않습니다. 계정 설정·외부 전송·비용을 먼저 확인하고 실제 사람의 개인정보 대신 가상 데이터만 사용하세요.

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
│   ├── generate_seed.py     ← 시드 생성 (stdlib, 고정 시드 샘플링)
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
| PORTABLE_PROMPT | 수동 실행용 문서 포함. 제공자별 호환성·실제 출력 품질은 별도 확인 필요 |
| 파이프라인 테스트 | 완료. `test_pipeline.sh` 전체 동작 검증 |
| identity v0.3 | 완료. 성소수자 분포 정상화 + IQ 하위 꼬리 축소 |
| region 버그 | 수정. roll_korea가 slot region override |

### 다음 마일스톤

1. **실전 검증** (4/30 데드라인) — 이상규가 직접 PORTABLE_PROMPT로 시뮬 돌려보기
2. **스킬 패키징** — Claude Code 스킬로 변환 (큐 2순위)
3. **나다움 공식 적용** — 기존 나 × 새로움 관점에서 30p 정체 재확인

## 의존성 정책

기본 시드·카드 파이프라인은 **외부 패키지 0**이며 stdlib만 사용한다. 아래의 선택적 로컬 모델 재현 경로는 `torch`, `transformers`, `safetensors`를 사용한다.

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
and excluded from Git. The verifier pins the model files, scenario source,
runner, and observed output hashes; it rejects coordinated edits to a run and
its manifest. The pinned outputs are a reproducibility check for this local
environment, not evidence of a general behavioral effect. This local result does not establish provider seed
application, personal prediction, or a causal effect on people.


## Seed reproducibility scope

For the same code, input tables and Python environment, a fixed seed repeats
the sampled character content and generation conditions. The `generated_at`
field records the actual generation time, so files generated at different
times are not byte-identical. Compare parsed content excluding that field when
checking sampling repeatability; keep the timestamp in the original records.
This does not promise identical sampling across Python versions or establish
that the fictional characters predict real people.
