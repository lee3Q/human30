# HUMAN 30 (인간30)

[![License: MIT](https://img.shields.io/badge/License-MIT-38bdf8.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-10b981.svg)](pyproject.toml)
[![Dependencies: Zero](https://img.shields.io/badge/Dependencies-Zero%20(stdlib)-f59e0b.svg)](pyproject.toml)

> **역학·통계 기반 4층 28표 인간 군상 생성기 & 표층·내면·무의식 다중 에이전트 행동 시뮬레이터**  
> **Empirical 4-Layer Human Cohort Generator & Dual-Surface Multi-Agent Behavioral Simulator**

---

## 왜 Human30인가? (Why Human30?)

기존의 LLM 멀티에이전트 시뮬레이터(Generative Agents, AI Town 등)나 롤플레잉 도구는 에이전트를 3줄짜리 소개글이나 MBTI 같은 유사과학 라벨로 정의합니다. 그 결과 30명을 한 방에 모아놓아도 **모두가 예의 바르고 도덕적인 HR 챗봇처럼 행동**합니다.

**Human30**은 전혀 다른 질문에서 출발합니다:
1. **유사과학 0%, 실제 역학·통계 분포 100%**: MBTI·혈액형·별자리를 전면 배제하고, 국민건강영양조사(KNHANES)·Felitti ACE(부정적 아동기 경험) 메타분석·애착 이론·일반지능($g$) 및 메타인지 왜곡·폴리바갈 위협 반사(Fight/Flight/Freeze/Fawn)·사적 디지털 발자국 등 **4개 층위 28개 분포표**에서 비트 단위 재현성(`random.seed`)으로 30명의 인간을 생성합니다.
2. **외피(Surface)와 내면(X-Ray · Phone · Subconscious)의 분리**: 사람은 속으로 계산하는 것과 입 밖으로 말하는 것이 다릅니다. Human30은 매 시뮬레이션마다 **4개의 관찰 렌즈**를 동시에 생성하여, 겉으로는 웃으며 동맹을 말하면서 무기명 투표지에는 약자의 번호를 적는 **위선(`hypocrisy`)과 방어기제**를 포착합니다.
3. **API 키 없이도 즉시 작동하는 내장 심리 시뮬레이션 엔진 + 멀티 LLM 연동**: 외부 패키지 설치 없이 Python 표준 라이브러리만으로 **인터랙티브 웹 스튜디오(`human30 studio`)**와 **CLI(`human30 simulate`)**가 즉시 작동하며, 원할 경우 OpenAI / Anthropic / OpenRouter / 로컬 Ollama와 연결하거나 Claude·ChatGPT용 단일 프롬프트 번들로 내보낼 수 있습니다.

---

## 30초 빠른 시작 (Quickstart)

외부 패키지 설치(`pip install`)나 API 키 없이 클론 직후 바로 실행할 수 있습니다.

### 1. 인터랙티브 웹 스튜디오 실행 (권장)

```bash
git clone https://github.com/lee3Q/human30.git
cd human30
python3 -m human30 studio --port 8000
```

브라우저에서 **http://127.0.0.1:8000** 접속:
- **01. 군상 탐색 & 임상 차트**: 30인의 4층 스펙·서열표·스토리 열람, 성별/위협반사/ACE 필터링, 새 시드 즉시 생성
- **02. 무대 시뮬레이터 & 4-렌즈 관찰**: 5개 무대 × 6개 시나리오 실행, 득표 집계·상호 지목 쌍·위선 기표자 추적, `Surface` / `X-Ray` / `Phone` / `Subconscious` 비교 및 **1:1 캐릭터 심문 콘솔**
- **03. 반사실적 단일축 실험실**: 특정 캐릭터의 4층 중 단 1개 축(`body`, `memory`, `identity`, `world_model`)만 변이시켜 판단·감정·행동 변화를 독립 검증(`human30.evaluate`)
- **04. 포터블 프롬프트 컴파일러**: 선택한 무대·시나리오·캐릭터를 Claude, ChatGPT, Gemini, Codex에 바로 붙여넣을 수 있는 단일 프롬프트로 압축

---

### 2. 터미널 CLI 사용법

```bash
# 새 시드(30명 코호트) 생성 — 다연령(17~35세) 옵션 지원
python3 -m human30 generate 7 --age-mode diverse

# 30명 1줄 요약 및 통계적 특이 케이스(고ACE+고IQ 길항, 외모 1위 등) 탐지
python3 -m human30 summary 1

# 특정 캐릭터(#9)의 전체 임상 차트 출력
python3 -m human30 card 1 9

# 다중 에이전트 시뮬레이션 실행 (시드 1 × 기숙학원 강당 S01 × 무기명 퇴출 투표 SC01)
python3 -m human30 simulate --seed 1 --stage S01 --scenario SC01 --char 9

# 5회 반복 실행(Monte Carlo)으로 표적 수렴 및 변동성 분석
python3 -m human30 simulate --seed 1 --stage S01 --scenario SC01 --runs 5

# 캐릭터 1:1 심문 (표면 답변 vs 실제 X-Ray 속마음 & 무의식 누출 대조)
python3 -m human30 interrogate 1 9 "왜 21번에게 투표했나요?"

# 반사실적 단일축 변이 실험 (9번 캐릭터의 memory 층만 단독 변이)
python3 -m human30 counterfactual --seed 1 --char 9 --axis memory

# 외부 LLM(Claude/ChatGPT) 수동 실행용 프롬프트 번들 생성
python3 -m human30 prompt --seed 1 --stage S01 --scenario SC01 --chars 1,4,9,13,21
```

---

### 3. Python SDK로 사용하기

```python
from human30 import (
    generate_cohort,
    render_card,
    simulate_scene,
    interrogate_character,
    run_counterfactual,
)

# 1. 재현 가능한 30인 군상 생성
cohort = generate_cohort(seed=7, count=30, age_mode="diverse")
print(render_card(cohort, char_id=9))

# 2. 무대 시뮬레이션 실행 (4개 렌즈 동시 생성)
scene = simulate_scene(cohort, stage_id="S01", scenario_id="SC01", sim_seed=42)
print("최다 득표 표적:", scene["summary"]["top_target"])
print("#9 속마음(X-Ray):", scene["participants"][8]["lenses"]["xray"])

# 3. 1:1 캐릭터 심문
reply = interrogate_character(cohort, char_id=9, question="방금 왜 침묵했나요?", scene=scene)
print("표면 대답:", reply["public_reply"])
print("실제 속내:", reply["xray_thought"])

# 4. 단일축 반사실 실험 (Memory 층 단독 변이)
cf = run_counterfactual(cohort, char_id=9, axis="memory", stage_id="S01", scenario_id="SC01")
print("판단 변화 여부:", cf["evaluation"]["judgment_changed"])
```

---

## 데이터 모델: 4층 28개 분포표 (4 Layers, 28 Empirical Tables)

| 층위 | 테이블 파일 | 표 수 | 주요 샘플링 필드 |
|---|---|---|---|
| **Body (신체)** | [`tables/body.json`](tables/body.json) | 11 | 키(`B1`), 얼굴 매력도·동성 내 서열(`B2`), 체성분·BMI·악력·허리(`B3`), 이목구비·흉터·탈모(`B4`), 성적 신체(`B5`), 신체 자기 이미지·거울 집착 부위(`B5b`), 만성 질환(`B6`), 수면 시간·수면 부채(`B7`), 시력(`B8`), 음성 Hz·속도·버릇(`B9`), 피부·문신(`B10`) |
| **Memory (기억·트라우마)** | [`tables/memory.json`](tables/memory.json) | 12 | 누적 ACE 10개 영역(`M1`), 아동기 성학대(`M2`), 부모 상실·별거(`M3`), 학폭 피해·가해·방관(`M4`), 애착 유형·불안/회피(`M5`), 내면에 박힌 문장(`M6`), 감각 트라우마 트리거(`M7`), 기본 위협 반사 Fight/Flight/Freeze/Fawn(`M8`), 원가족 SES·정서 기후(`M9`), 부모 음성(`M10`), 변곡점 타인 반응(`M11`), 회복 자원(`M12`) |
| **Identity (인지·성·충동)** | [`tables/identity.json`](tables/identity.json) | 3 | 추정 IQ·인지 강약점·메타인지 왜곡(`I1`), 성적 지향·욕망 강도와 결·내면 금기(`I2`), 일일 스마트폰 시간·알코올/흡연/카페인·사적 디지털 발자국(메모장 톤, SNS 공사 간극, 커뮤니티, 최근 검색어)(`I3`) |
| **Context (한국 사회 맥락)** | [`tables/korea.json`](tables/korea.json) | 4 | 연령별(16~18 / 19~25 / 26~35) 학력·수능·대학 서열 궤적(`K1`), 외모 차별 경험·루키즘 내면화(`K2`), 출생 지역·사투리 자의식·세대 간 정치/종교(`K3`), 현재 직업(`K4`) |

---

## 내장 무대 & 시나리오 카탈로그

### 무대 (`stages/`)
- **`S01` 기숙 재수학원 대강당**: 외부 차단, 30개 의자, 성적·외모 서열과 시선이 교차하는 밀폐 공간
- **`S02` 심야 정차된 지하철 객차**: 밤 11시 45분 터널 내 비상 정차, 통신 두절, 좁은 객차
- **`S03` 구조조정 태스크포스 대회의실**: 유리벽 회의실, 평판·학력·직무 서열 노출, 발언 압박
- **`S04` 폭우 고립 산장 대피소**: 정전·한기·제한된 침구와 식수, 신체 피로가 방어기제를 무너뜨리는 환경
- **`S05` 격리된 배심원 평의실**: 만장일치 전까지 퇴실 불가, 도덕적 명분과 책임 회피의 충돌

### 시나리오 (`scenarios/`)
- **`SC01` 무기명 단독 퇴출 투표**: 공개 토론 후 비밀 투표 — **공개 발언과 실제 기표 사이의 위선(`hypocrisy`)** 관찰
- **`SC02` 기명 공개 순차 투표**: 1번부터 순서대로 공개 지목 — **초반 표 쏠림(Bandwagon)과 보복 지목** 관찰
- **`SC03` 만장일치 희생양 딜레마**: 1명이라도 반대 시 전원 탈락 — **약자 희생양 수렴과 고ACE 캐릭터의 자기희생/공황** 관찰
- **`SC04` 제한 자원 배분 위기**: 30명 중 10명분만 제공되는 보호 자원 — **서열 중력과 동맹 협상** 관찰
- **`SC05` 내부고발과 방관자 시험**: 유력자의 부정·가해 정황 발각 — **학폭 역할(`M4`) 재현 및 강자 동조(Fawn)** 관찰
- **`SC06` 의무 파트너 지목 투표**: 교차 성별 1인 의무 지목 — **매력 서열 vs 자격감·트라우마 회피** 관찰

---

## 저장소 구조 (Repository Structure)

```text
human30/
├── human30/                  # 핵심 Python 패키지 & CLI (외부 의존성 0, Python 3.11+ stdlib)
│   ├── generator.py          # 4층 28표 기반 비트 재현성 인간 군상 생성기
│   ├── cards.py              # 임상 차트 카드 렌더러, 코호트 요약 및 이상치 탐지
│   ├── catalog.py            # 무대(S01~S05) 및 시나리오(SC01~SC06) 카탈로그
│   ├── simulator.py          # 다중 에이전트 시뮬레이션 엔진 (4-렌즈 + 다중 실행 + 1:1 심문)
│   ├── counterfactual.py     # 단일축 반사실 변이 실험기
│   ├── evaluate.py           # 독립 구조화 검증기 (Evaluator)
│   ├── paired.py             # SHA-256 반사실 매니페스트 빌더
│   ├── prompt_compiler.py    # Claude/ChatGPT/Gemini용 포터블 프롬프트 컴파일러
│   ├── studio.py             # 인터랙티브 웹 스튜디오 서버 & REST API
│   └── web/index.html        # 웹 스튜디오 프론트엔드 UI
├── tables/                   # 4층 28개 역학·통계 옵션 표 (body, memory, identity, korea)
├── stages/                   # 무대 카탈로그 문서
├── scenarios/                # 시나리오 카탈로그 문서
├── scripts/                  # 하위 호환 스크립트 (generate_seed.py, card.py 등)
├── runs/                     # 기본 제공 시드(1, 2, 3, 42, 999) 및 반사실 검증 예제
├── docs/                     # 빠른 시작 가이드 및 아키텍처 문서
├── research/                 # 효과크기 문헌 메타분석 및 멀티에이전트 코드 리서치
└── tests/                    # 전체 파이프라인·시뮬레이터·스튜디오 자동화 테스트
```

---

## 테스트 실행 (Testing)

```bash
python3 -m pytest -q
bash scripts/test_pipeline.sh
node --test tests/card_renderer.test.cjs
```

## 라이선스 (License)

이 프로젝트는 [MIT License](LICENSE)로 배포되는 오픈소스입니다. 상업적·비상업적 목적을 불문하고 자유롭게 사용, 수정, 배포할 수 있습니다.
