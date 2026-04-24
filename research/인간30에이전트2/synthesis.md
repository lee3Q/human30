# 인간30에이전트2: LLM 멀티에이전트 시뮬레이터 실전 코드 참조

**날짜**: 2026-04-09
**목적**: 30p (인간30) 시뮬레이터가 직접 훔쳐올 수 있는 코드 패턴. 추상 개념 X, 실행 코드 O.
**소스**: Claude 자체 리서치 + Gemini Deep Research + Perplexity (3자 합성)
**범위**: joonspk-research/generative_agents (Stanford), a16z-infra/ai-town, tsinghua-fib-lab/agentsociety, camel-ai/oasis, sotopia-lab/sotopia

---

## 3자 만장일치 결론

### 가장 가치 있는 2개 레포
1. **Stanford generative_agents** — 30p와 아키텍처가 가장 가까움. 순차 tick, 파일 기반 직렬화, Python, 인스펙션 CLI
2. **a16z ai-town** — 동일한 retrieve+reflect 공식을 재구현한 TypeScript 버전. 가중치 균형이 달라 비교 가치 높음

### 공통 피해야 할 것 (3자 동의)
- **순차 for loop 이상의 스케줄링 불필요** — Stanford도 ai-town도 기본은 순차. 30명 스케일엔 async/subprocess 과도
- **벡터 DB 제거 가능** — Stanford는 `numpy` cos_sim으로 자체 구현, ai-town의 Convex+hnsw는 프로덕션용
- **LLM seed 재현성 환상 버려라** — API 비결정성 때문에 불가능. Stanford/ai-town 모두 포기. 30p의 "캐릭터 생성만 bit-reproducible, tick은 서사 복수성" 전략이 맞다
- **Django/Convex/PixiJS/Next.js/Clerk** — 전부 시각화·배포용. 30p는 버림

---

## 1. Stanford generative_agents (핵심 참고)

### 1.1 Retrieval 스코어 (가장 직접 훔칠 것)

**파일**: `reverie/backend_server/persona/cognitive_modules/retrieve.py`
**함수**: `new_retrieve(persona, focal_points, n_count=30)`

```python
# 3항 계산
recency_vals = [persona.scratch.recency_decay ** i for i in range(1, len(nodes)+1)]
recency_out[node.node_id] = recency_vals[count]

importance_out[node.node_id] = node.poignancy   # 0~10 (LLM이 생성시 매김)

focal_embedding = get_embedding(focal_pt)
relevance_out[node.node_id] = cos_sim(node_embedding, focal_embedding)

# 정규화 후 가중 합산
gw = [0.5, 3, 2]   # [recency, relevance, importance]
master_out[key] = (persona.scratch.recency_w   * recency_out[key]   * gw[0]
                 + persona.scratch.relevance_w * relevance_out[key] * gw[1]
                 + persona.scratch.importance_w* importance_out[key]* gw[2])
```

**핵심**: relevance(3) > importance(2) > recency(0.5). *무엇과 닮았나*가 *언제였나*의 6배.

**Scratch 기본값 (실제 `scratch.json` 예시)**:
```json
{
  "vision_r": 8, "att_bandwidth": 8, "retention": 8,
  "recency_w": 1, "relevance_w": 1, "importance_w": 1,
  "recency_decay": 0.995,
  "importance_trigger_max": 150,
  "importance_trigger_curr": 142,
  "importance_ele_n": 8
}
```

### 1.2 AssociativeMemory 구조

**파일**: `reverie/backend_server/persona/memory_structures/associative_memory.py`

각 `ConceptNode`:
- `node_id`, `type` ∈ {event, thought, chat}, `depth`
- `created`, `expiration`, `last_accessed` (timestamps)
- `subject` — `predicate` — `object` (SPO 트리플)
- `description`, `embedding_key`, `poignancy` (0~10), `keywords`, `filling`

**실제 저장 예시** (`nodes.json`):
```json
"node_912": {
  "type": "thought", "depth": 1,
  "created": "2023-02-14 00:00:00",
  "expiration": "2023-03-16 00:00:00",
  "subject": "Isabella Rodriguez",
  "predicate": "plan",
  "object": "Tuesday February 14",
  "description": "This is Isabella Rodriguez's plan for ...",
  "poignancy": 5,
  "keywords": ["plan"]
}
```

**직렬화 구조**:
```
environment/frontend_server/storage/<sim_code>/personas/<Name>/bootstrap_memory/
├── spatial_memory.json         # 세계→섹터→아레나→오브젝트 트리
├── scratch.json                # 단기 상태 + 하이퍼파라미터
└── associative_memory/
    ├── nodes.json              # ConceptNode 딕셔너리
    ├── embeddings.json         # embedding_key → 벡터
    └── kw_strength.json        # 키워드 카운트
```

*전부 JSON. pickle 없음.*

### 1.3 Tick 루프 (순차 for-loop)

**파일**: `reverie/backend_server/reverie.py` → `ReverieServer.start_server(int_counter)`

```
매 step:
1. environment/{step}.json 대기 (프론트 → 백)
2. for persona in personas.items():  # 위치 업데이트
3. for persona in personas.items():  # move() 호출
     perceived = persona.perceive(maze)          # LLM 0회
     retrieved = persona.retrieve(perceived)     # 임베딩 검색
     plan = persona.plan(maze, ..., retrieved)   # LLM 다수 (action boundary일 때만)
     persona.reflect()                           # 트리거될 때만 LLM 다수
     return persona.execute(maze, ..., plan)
4. movement/{step}.json 기록 (백 → 프론트)
5. self.step += 1; self.curr_time += sec_per_step
```

**LLM 호출 패턴**:
- **대부분 tick**: 0회 (기존 action 계속 수행)
- **Action boundary**: 5~10회 (task decomp, sector/arena/object 선택, emoji, event triple 등)
- **Social reaction**: `run_gpt_prompt_decide_to_talk` + `decide_to_react` + `generate_convo` + `summarize_conversation`
- **Reflection 발동 시**: 또 5~10회 (focal points, insights, poignancy, triples)

→ **30p 맥락에서**: "고정 N회" 아님. 이벤트 경계 기반. *행동이 바뀔 때만* Claude 깊게 생각.

### 1.4 Reflection 트리거

**파일**: `reverie/backend_server/persona/cognitive_modules/reflect.py`

```
조건: importance_trigger_curr <= 0 AND (events or thoughts 누적)
발동 시:
  1. generate_focal_points → run_gpt_prompt_focal_pt (3개 뽑기)
  2. 각 focal point로 new_retrieve() (위 공식)
  3. generate_insights_and_evidence → run_gpt_prompt_insight_and_guidance
     → 증거 노드 번호를 인용한 통찰 생성
  4. 각 통찰에 event_triple + poignancy 매김
  5. 30일 만료로 associative_memory에 저장

대화 종료 후 10초: planning_thought_on_convo + memo_on_convo 자동 발동
```

**트리거 수치** (scratch.json 예시): `importance_trigger_max = 150`. 누적 poignancy가 150 쌓이면 reflect 1회 발동 후 카운터 리셋.

### 1.5 인스펙션 CLI (30p x-ray/phone/subconscious의 직계 조상)

**함수**: `ReverieServer.open_server()` 텍스트 기반 콘솔

```
print persona schedule <Full Name>              # 디컴포즈된 일일 스케줄
print all persona schedule                       # 전원
print hourly org persona schedule <Full Name>   # 시간 단위 원본
print persona current tile <Full Name>
print persona chatting with buffer <Full Name>
print persona associative memory (event|thought)
```

**30p 비교**:
- `print persona associative memory event` ≈ 30p `x-ray #N`의 Memory 층 덤프
- `print persona chatting with buffer` ≈ World Map "지금/방금"
- `print persona schedule` ≈ World Map "곧"
- **30p가 이미 앞서는 점**: `subconscious`(접근 불가 영역 전용), `phone`(I3-B 발자국 전용)은 Stanford에 없음. 30p의 고유 설계.

### 1.6 의존성 (77개, 대부분 불필요)

**핵심만** (30명 stdlib 어댑테이션):
- `numpy` — cos_sim + std (유일한 진짜 필요)
- `openai` (또는 교체)
- 파이썬 stdlib: datetime, json, math, random

**버릴 것**:
- Django 2.2 + dj-database-url + gunicorn + psycopg2-binary → 프론트+배포
- gensim, nltk, scikit-learn, scipy, pandas → 사전 임베딩·분석용
- matplotlib, seaborn, yellowbrick → 논문 플롯용
- selenium, boto, botocore → 테스트·AWS

→ **30p 교훈**: Stanford 엔진의 *핵심 로직*은 약 4개 파일 (`retrieve.py` + `reflect.py` + `associative_memory.py` + `scratch.py`)로 응축 가능. 나머지 73개는 주변 인프라. 의존성 0 정책 정당성 역증명.

### 1.7 재현성

- `random`에 seed 설정 없음. `random.choice` 사용
- OpenAI API 자체가 비결정적 (temperature 0여도)
- Stanford CS222 강의 슬라이드가 *"결정적인가?"*를 **열린 토론 주제**로 제시 — 공식적으로 지원 안 함
- → **30p의 "생성만 bit-reproducible, tick은 서사 비결정"** 이 옳은 방향

---

## 2. a16z ai-town (공식 비교용)

### 2.1 Retrieve 공식 — Stanford와 다른 변종

**파일**: `convex/agent/memory.ts` → `rankAndTouchMemories`

```typescript
// recency
const hoursSinceAccess = (ts - memory.lastAccess) / 1000 / 60 / 60;
const recencyScore = 0.99 ** Math.floor(hoursSinceAccess);

// 각 항 정규화 (min-max)
const relevanceRange  = makeRange(candidates.map(c => c._score));
const importanceRange = makeRange(relatedMemories.map(m => m.importance));
const recencyRange    = makeRange(recencyScore);

// 동등 가중 (1:1:1) 합산
overallScore = normalize(relevance, relevanceRange)
             + normalize(importance, importanceRange)
             + normalize(recency, recencyRange);
```

**Stanford와 차이**:
| 항목 | Stanford | ai-town |
|---|---|---|
| 가중치 | `[0.5, 3, 2]` 불균형 | `[1, 1, 1]` 균형 |
| 정규화 | hyperparameter w × gw 곱 | min-max normalize 후 합 |
| recency 단위 | tick 거리 | 실제 시간 시간 단위 |
| recency decay | `0.995 ** i` | `0.99 ** hours` |
| importance 범위 | 0~10 | 0~9 |

→ **30p 선택 근거**: Stanford 쪽이 더 서사적 편향 (*관련성과 중요도가 훨씬 무거움*). 30p의 "카페라떼 미학"과 맞음 — *방금 일어난 것보다 오래 묶어 온 것이 행동을 휜다*.

### 2.2 Reflection 트리거
- **조건**: `rememberConversation` 후 **sum(importance) > 500** 이면 `reflectOnMemories` 호출
- Stanford는 *감소 카운터* (`trigger_curr <= 0`), ai-town은 *누적 임계값 비교* — 본질적으로 동일

### 2.3 Tick 루프 — 2층 분리

**파일**: `convex/aiTown/game.ts` → `Game.tick(now)`

```typescript
Game.tick(now):
  for (player of players) player.tick(game, now)
  for (player of players) player.tickPathfinding(game, now)
  for (player of players) player.tickPosition(game, now)
  for (conv of conversations) conv.tick(game, now)
  for (agent of agents) agent.tick(game, now)
```

- **Physics tick**: 60Hz (`TICK = 16ms`)
- **Step** (DB 커밋): 1Hz (`STEP_INTERVAL = 1000`)
- **LLM 호출**: `ctx.scheduler.runAfter(0, ...)` 로 **비동기 fan-out** — tick 자체는 블로킹 안 됨

→ **30p 맥락**: 30p는 real-time physics 필요 없음. ai-town의 2층 분리는 불필요. Stanford 방식(단일 순차 tick) 이 맞다.

### 2.4 재현성
- `Math.random()` + `crypto.randomUUID()` 무작위 사용. 전역 seed 없음
- LLM 호출도 스케줄링 순서 불확정
- → Stanford와 동일, 재현 불가

---

## 3. tsinghua-fib-lab/agentsociety

**코드 접근 못 함 (Perplexity는 못 봤다고 인정, Gemini는 파일 경로까지 답했으나 검증 불가)**

### 검증된 것만
- **Multi-Head Workflow**: `Reason Block` (LLM 결정) → `Route Block` (경로, 프로그래매틱) → `Action Block` (실행)
- **Memory 모듈 존재**: `agentsociety/memory/memory.py` (이슈 스레드에서 import 경로 확인)
- `StateMemory` + `DynamicMemory` + `Custom Data Pool` 분리 (정체 프로필 vs 작업 메모리)
- **Protobuf + cityproto** 사용 — 도시 규모 전용
- 심리 모델: Maslow 욕구 + Theory of Planned Behavior 명시적 구현

### 30p가 훔칠 것 (설계 아이디어만, 코드 X)
- **Reason vs Action 경계**: 30p의 현재 "Claude 직접 서사 생성"은 *Reason과 Action이 섞여 있음*. agentsociety처럼 분리할 필요는 없음 (스케일 달라서). 단, *"루틴 행동은 LLM 안 쓰고 스킵"* 아이디어는 참고 가치. 30p에서 "자는 캐릭터"는 tick 건너뛰기 등.
- **Custom Data Pool**: 전체 associative memory 대신 *이번 tick 관련 작업 메모리*만 작은 버퍼로 유지 → 프롬프트 토큰 절약. 30p에도 적용 가능.

### 피해야 할 것
- Protobuf/cityproto — 대규모 전용
- Multi-Head 워크플로 블록 분리 — 30p 규모엔 과잉
- Python 3.11+ + Docker

---

## 4. camel-ai/oasis

### 검증된 것
- **PettingZoo 스타일 env interface**: `await env.reset() → await env.step(actions) → await env.close()`
- **asyncio** 기반 — `asyncio.create_subprocess_exec` + `asyncio.Queue`
- **SQLite** 상태 저장 (`oasis/social_platform/database.py`)
- **23개 discrete actions**: LIKE_POST, DISLIKE_POST, CREATE_POST, CREATE_COMMENT, FOLLOW, MUTE, SEARCH_POSTS, TREND, REFRESH, DO_NOTHING, INTERVIEW, REPORT_POST 등
- **인스펙션**: `CAMEL_MODEL_LOG_ENABLED` 환경변수로 모든 LLM req/res 덤프 + SQLite 파일 직접 열기
- **Memory = 관계형 쿼리**로 대체 (`rec_sys_reddit`). 시맨틱 retrieval 없음. 타임스탬프+engagement 정렬만
- **1회 LLM 호출/step**: 제약된 action space라서 강제 파싱

### 30p가 훔칠 것 (2개)

1. **`INTERVIEW Action`**: 시뮬 외부에서 특정 에이전트에게 질문 던지고 답 받는 것. **30p `x-ray`(구조 덤프)에 없는 보완**. 4번째 관찰 명령 `interview #N "질문"` 후보.

2. **Constrained action enum 파싱 패턴**: Gemini 보고대로, *LLM 서사 출력에 태그 강제* 하면 이벤트 등록 자동화 가능. 예:
   ```
   #9가 카페라떼를 받아 든다. "감사합니다"라고 웃는다.
   <EVENT: #9 received coffee_from #supervisor; affect=+2; poignancy=4>
   ```
   - 30p의 "건조한 서술" 원칙과 충돌 여부는 사용자 판단
   - 장점: 메모리 기록·poignancy 매김 자동화
   - 단점: 내재적 서사의 오염 가능성

### 피해야 할 것
- `asyncio.create_subprocess_exec` + queue — 30명 규모엔 과도. 순차 for loop이 디버깅·트레이싱 압도적 유리 (3자 동의)
- SQLite — JSON 파일이면 충분 (30명 규모). Stanford가 이미 증명
- 23개 고정 action space — 30p 도메인(자유 서술)과 충돌

---

## 5. sotopia-lab/sotopia

**코드 접근 제한 (Perplexity 못 봄, Gemini만 주장)**

### 확인된 것
- **에피소드 기반** (지속 시뮬 아님). 특정 사회 시나리오에 에이전트 2명 배치 → 대화 턴 교대 → 평가
- Memory는 LLM context window에만 존재 (대화 히스토리). 장기 메모리 없음
- 평가 대상: 협상, 자원 할당, 사회 지능
- `structured_social_verifier.py`로 raw 대화에서 상태 추출 (Gemini 보고)

### 30p가 훔칠 것 (1개)
- **`structured_social_verifier.py` 패턴** (만약 Gemini 주장이 맞다면): 서사 텍스트에서 regex/키워드로 "누가 누구에게 무엇을" 추출. Stanford `run_gpt_prompt_event_triple`과 기능적 등가지만 LLM 호출 없음. **30p에서 "카페라떼를 웃으며 마시고 화장실에서 토함" 같은 서사에서 `{subject:#9, pred:drank, obj:latte}` + `{subject:#9, pred:vomited, obj:bathroom}` 자동 추출**해서 SPO 트리플로 M11에 저장. 단, 정규식 패턴 유지가 부담.

### 피해야 할 것
- 에피소드 모델 — 30p는 지속 시뮬
- WandB 의존성
- RL 스캐폴드 (GRPO, LoRA)

---

## 🎯 30p 직접 적용 블루프린트

### 바로 구현 가능 (7개)

#### 1. Memory 엔트리 포맷 (`runs/seed_N/memories/{char_id}.jsonl`)
```jsonl
{"id":912,"type":"event","created":"2026-04-09 14:30","s":"#9","p":"listened","o":"classmate_rant","desc":"...","poignancy":7,"kw":["cafe","jealousy"],"last_accessed":"2026-04-09 14:30"}
```
- Stanford ConceptNode를 JSONL로 평탄화
- 한 줄 = 한 사건. append-only
- Claude가 tick 종료 시 새 이벤트를 poignancy 매겨서 추가

#### 2. Retrieve 규칙 (Claude가 tick 시작 시 수행)
Stanford 가중치 차용하되 임베딩 없이:
- `recency = 0.995 ** position` (역순 index)
- `relevance = Claude 판단 (0~1)` — "지금 이 자극과 이 기억이 얼마나 닮았나"
- `importance = poignancy / 10`
- `score = 0.5*recency + 3*relevance + 2*importance`
- top-N (기본 N=8, `att_bandwidth`) 선택해서 프롬프트에 주입

**구현 위치**: Claude가 tick 시작 전 해당 캐릭터의 `memories.jsonl` 읽고 계산. stdlib Python으로 전처리 스크립트 작성 가능 (`scripts/retrieve.py`) 또는 Claude 직접 읽기.

#### 3. Poignancy 매김 (Claude가 이벤트 저장 시)
새 이벤트 저장 직전 Claude가 0~10 정수로 자체 판단:
```
"#9가 상사의 카페라떼를 받음. 과거 구강성교 피해 기억 연쇄 작동 → poignancy=9"
"#9가 계단을 내려감. 특기할 것 없음 → poignancy=2"
```

#### 4. Reflection 트리거 (선택적, 사용자 합의 필요)
- `importance_trigger_max` = 100 (30p 디폴트 제안)
- 각 캐릭터마다 카운터 `trigger_curr = 100` 시작
- 새 이벤트 저장 시 `trigger_curr -= poignancy`
- 0 이하로 떨어지면 다음 tick에 "내부 독백 / 깨달음" 단계 강제 추가:
  1. 최근 100개 메모리에서 focal point 3개 뽑기
  2. 각 focal point로 retrieve → 관련 노드
  3. Claude가 증거 인용된 통찰 생성 → `type: thought` 로 저장, poignancy 높게
  4. 카운터 리셋
- **주의**: 30p는 관찰자(사용자) 중심. reflect는 캐릭터 자생 매커니즘이라 *방향이 다르다*. 사용자 검토 필요.

#### 5. Scratch 하이퍼파라미터 캐릭터 연동
Stanford의 `recency_w / relevance_w / importance_w / recency_decay / att_bandwidth` 를 30p 4층 데이터에서 파생:
- 높은 I1 cognitive_ability → `att_bandwidth` ↑ (더 많은 기억 참고)
- 낮은 M5 attachment 안정성 → `importance_w` ↑ (충격적 기억 가중)
- 높은 B7 수면 부족 → `recency_w` ↑ (먼 기억 접근 어려움)
- **즉**: 하이퍼파라미터 자체가 캐릭터의 *인지 결*을 반영. seed_001에서 자동 계산 가능.

#### 6. 관찰 명령 `interview #N "질문"` 신설 (4번째)
Oasis INTERVIEW + Sotopia verifier 합성:
- `x-ray #N` = 구조 덤프 (Memory + Identity + WorldMap 접근 가능 부분)
- `phone #N` = I3-B 발자국
- `subconscious #N` = 접근 불가 영역
- **`interview #N "질문"` = 캐릭터 본인이 입으로 답하는 것** (거짓말·회피·방어기제 포함)
- **차이**: `x-ray`는 사용자가 진실을 보는 것, `interview`는 *캐릭터의 자기 서사*를 받는 것. 둘의 괴리가 드러나는 것이 흥미.

#### 7. 파일 시스템 기반 tick 파이프
Stanford의 `environment/{step}.json` + `movement/{step}.json` 패턴을 30p로:
```
runs/seed_001/
├── tick_0000/
│   ├── world.json        # 세계 상태 (stage + event queue + curr_time)
│   ├── actions.json      # 30명 각각의 출력 (서사 + event triples)
│   └── observations/     # 사용자가 돌린 x-ray/phone/sub/interview 기록
├── tick_0001/
│   └── ...
└── memories/             # 전역 누적. tick마다 append
    └── {char_id}.jsonl
```
- DB 없음. stdlib json만
- tick n의 상태 = `tick_{n-1}/` + `memories/*.jsonl` 로 완전 복원 가능
- Claude 부재 시 (5월) 사용자가 파일 직접 읽으며 뭐가 있었는지 재구성 가능

### 피해야 할 것 (3자 일치)
- ❌ Django + 프론트 시각화 (Stanford)
- ❌ Convex DB + Next.js + PixiJS + Clerk (ai-town)
- ❌ Protobuf + cityproto (agentsociety)
- ❌ asyncio + SQLite + 23-action enum 강제 (oasis)
- ❌ WandB + RL 스캐폴드 (sotopia)
- ❌ 벡터 DB / 임베딩 API 전체 (30p는 Claude가 관련성 직접 판단)
- ❌ OpenAI seed로 재현성 시도 — 어차피 불가능 (3자 모두 확인)
- ❌ 고정 "N LLM calls per tick" 모델 — Stanford/ai-town 모두 이벤트 경계 기반

---

## 📝 30p 현재 설계 vs Stanford 비교 표

| 축 | Stanford | 30p 현재 | 비고 |
|---|---|---|---|
| 에이전트 프로필 층 | 3층 (innate/learned/currently) | **4층** (Body/Memory/Identity/WorldMap) | 30p가 더 정교 |
| Body 층 | 없음 | 있음 (11표) | 30p 고유 |
| Memory 층 | ConceptNode (이벤트 누적만) | 11표 + 누적 (사전 굴림 + 누적 혼합) | 30p가 풍부 |
| Identity | `innate`+`learned` (단순 텍스트) | I1+I2+I3 (3필드 상세) | 30p가 정교 |
| WorldMap | `curr_tile`+`vision_r`+`att_bandwidth`+`daily_schedule` | 4 하위 (지금/방금/곧/배경) | 유사 |
| Tick 실행자 | Python + LLM 호출 | **Claude 직접** (코드 없음) | 30p 고유 |
| Retrieve 공식 | 3항 가중합 | 없음 (사용자 판단) | 30p는 도입 필요 |
| Reflection 트리거 | 누적 중요도 카운터 | 없음 | 30p는 선택 도입 |
| 관찰 명령 | 6개 `print ...` CLI | 3개 (`x-ray`, `phone`, `subconscious`) | 30p가 서사적 진화 |
| 의존성 | 77개 | **0개** (stdlib만) | 30p가 극단 |
| 재현성 | 없음 | 캐릭터 생성만 bit-reproducible | 30p가 현실적 |

→ **결론**: 30p는 Stanford보다 *데이터 모델 정교함*과 *의존성 최소화*에서 앞섬. *Retrieve 공식*과 *Reflection 트리거*가 현재 비어 있는 자리 — Stanford에서 훔쳐올 첫 자리.

---

## 📌 즉시 큐 추가 제안

30p `.state/queue.md`의 3순위 또는 2순위에 추가할 후보:

- [ ] **Retrieve 규칙 도입** (Stanford 가중치 차용): 각 tick 시작 시 해당 캐릭터의 `memories.jsonl`에서 score top-N만 프롬프트에 주입. 첫 시뮬 돌려 납득 수준 판단 후 도입 여부 결정
- [ ] **Poignancy 필드 추가**: 새 이벤트 저장 시 Claude가 0~10 매김. `memories.jsonl` 엔트리 포맷 확장
- [ ] **`interview #N "질문"` 4번째 관찰 명령 검토**: oasis INTERVIEW 영감. `docs/observation_commands.md`에 추가 여부 사용자 확정
- [ ] **Reflection 트리거 도입 여부 결정**: 30p 관찰자 철학과 맞는지 사용자 판단. 맞으면 `trigger_max`/`trigger_curr` 필드 scratch 구조에 추가
- [ ] **Scratch 하이퍼파라미터 캐릭터 연동**: I1 → att_bandwidth, B7 → recency_w 등 자동 계산 규칙. seed_001에서 테스트

---

## 소스별 불일치·신뢰도 주석

- **Stanford retrieve 공식**: Claude + Perplexity **완전 일치** (코드 직인용). Gemini도 맞음. 🟢 확실
- **ai-town retrieve 공식**: Perplexity만 실제 TS 코드 인용. Gemini는 구조만 언급. 🟢 Perplexity 근거 신뢰
- **AgentSociety**: Perplexity는 "못 봤다"고 정직 인정. Gemini는 파일 경로 주장하나 `packages/agentsociety/ (Agent Layer)` 수준이라 실제 파일명 아님. 🟡 개념만 차용, 코드 이식 금지
- **Oasis 파일 경로**: Gemini가 `oasis/social_platform/platform.py` 등 구체 경로 제시. Perplexity 미확인. 🟡 검증 필요. 이식 시 원본 확인
- **Sotopia `structured_social_verifier.py`**: Gemini만 주장. Perplexity 미확인. 🟡 개념만 가치 있음, 파일은 존재 여부 불명
- **OpenAI seed 재현성 불가**: 3자 만장일치 🟢

---

## 한 줄 결론

**Stanford `retrieve.py` + `reflect.py` + ConceptNode 구조**를 30p에 서사적 형태로 이식하고, ai-town의 `0.99 ** hours` 시간 감쇠와 oasis의 `INTERVIEW` 명령을 옵션으로 고려. 나머지 인프라(DB, 프레임워크, async, 벡터)는 전부 무시. 30p는 이미 *데이터 모델*과 *의존성 정책*에서 Stanford를 앞서고 있으므로, *인지 메커니즘* 쪽만 훔쳐오면 된다.
