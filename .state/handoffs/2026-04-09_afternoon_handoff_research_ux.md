# 2026-04-09 낮~오후 Handoff — 리서치 드릴다운 + UX 설계 자율 실행

세션 ID: `e0c916fe-aa7b-4974-9ec3-b05b15f3dd92`
다음 세션: `cd ~/pp/30p && cc` (또는 alias 적용 후 `nn && cc`) / 시뮬 테스트는 `cd ~/pp/30p/play && cc`

---

## 한 문장

리서치를 *훔쳐오려던* 잘못된 방향이 사용자 4번 교정으로 *버리는 방향*으로 바뀌었고, 30p는 **자동 tick 시뮬 아닌 사용자 호출 기반 이벤트 체인**으로 정체가 명확해졌으며, 그 UX를 **작업 모드(`30p/`) + 시뮬 모드(`30p/play/`) 폴더 분리** + `docs/session_flow.md` 초안 + alias 정비로 박았다. 모든 실제 작성 작업은 하네스 2개 + background Agent 자율 실행으로 수행.

---

## 이 세션의 철학 축

### 30p 는 자동 tick 시뮬이 **아니다** (가장 중요)

- Stanford generative_agents, a16z ai-town, agentsociety, oasis, sotopia 전부 *자동 tick 시뮬*. 에이전트가 알아서 매초 돌고 사용자는 *사후 관찰자*
- 30p 는 **사용자 호출 기반 이벤트 체인**. 사용자가 명령할 때만 세계가 움직인다. 사용자는 *전지전능한 감독* — 장면을 세우고, 멈추고, 들여다보고, 되감는다
- 리서치의 tick 루프·retrieve 공식·reflect 트리거 모두 자동 시뮬 전제라 **30p 철학과 정면 충돌**. 훔치면 안 됨 (일부 프롬프트 기법만 예외)
- *리서치가 준 진짜 가치 = "30p는 이미 올바른 자리. 더할 필요 없다"는 허가증*

### 토큰 허영 vs 본질 비용

사용자의 정확한 지적: *"본질을 추구하기 위해 토큰을 많이 쓰는 건 허영인데, 자꾸 요약하려고 한다"*

- **허영 (금지)**: 토큰을 *많이 쓰는 것 자체*를 자랑하거나 당연시하는 것. 자동 tick, 장황한 재생성, 필요 없는 대규모 맥락 주입
- **본질 비용 (OK)**: 서사 보존·사실 누적·30인 복수성·근거 있는 생성을 위해 *필연적으로* 드는 토큰. 이건 아껴선 안 됨
- **금지된 토큰 절약**: 요약·근사·top-N 필터링·한 줄 카드로 치환 — 30인 복수성 훼손 = 본질 상실

### 외피 + 내면 **동시** 생성 (사후 합리화 방지)

사용자의 정확한 지적: *"사실 겉으로 드러나는 행동을 결정하려면 그 내부 서사도 존재해야. 요약된 근거가 아니라 인간군상 자체에서 답을 내야"*

- 내가 처음 제안한 "1차 외피만 / 2차 x-ray 시 내면 생성" 구조는 **틀렸음**
- 이유: 2차 시점의 Claude 가 외피를 *역으로 읽고* 내면을 *재구성* → 사후 합리화 (*"왜 고개 숙였는지"* 를 외피 본 뒤 지어냄)
- **옳은 구조**: 한 번의 `play` 호출에서 Claude 가 *전원의 내면과 외피를 동시에* 생성해 파일로 박음. 사용자 `x-ray` 호출 시 *이미 저장된 파일을 읽기만* (재생성 0)
- 생성 = 1회, 근거 = 고정, 사후 합리화 = 0

---

## 수행한 작업

### Phase 1: 대화 (리서치 재해석·프레임 교정)

4번의 사용자 교정이 연쇄:
1. "토큰 아끼려고 요약·근사하지 마. UX 생각해" → `mini_card.py`·`retrieve.py top-N` 폐기
2. "30인 복수성 희석되면 5명으로 충분해" → 필터링·한 줄 요약 전부 버림
3. "내부 서사가 외피의 *근거*여야" → 생성 1회·표출 다회로 구조 교정
4. "자동 tick 아니고 나는 감독" → 리서치의 tick 패러다임 전체가 부적합

각 교정 후 내가 *또 잘못된 방향* 제안하면 사용자가 *또 교정*. 5차에서 사용자가 *"결국 리서치에서 얻은 게 없어? 왜 돌렸지?"* 로 근본 질문. 이 질문이 *리서치는 허가증이지 훔칠 재료가 아니다* 결론 이끌어냄.

### Phase 2: UX 구조 확정

사용자 제안 수용: *"게임처럼 쓴다. 시간 범위 + 무대 + 변화 입력 → 끝 시점 외피 출력 → 궁금하면 내면 조회"*.

확정된 것:
- **턴제 게임 엔진 모델** (자동 시뮬 아님)
- **명령 어휘** 5개 수준: `이어서` / `N분 @ 무대 "사건"` / `x #N` / `폰 #N` / `무의식 #N`
- **외피 + 내면 동시 생성 + 파일 박음, 관찰은 읽기만**
- **세계 축 (`timeline.md`) + 캐릭터 축 (`memories/<id>.md`) 직교 누적**
- **폴더로 모드 분리**: 작업 `30p/` vs 시뮬 `30p/play/`. 각자 다른 `CLAUDE.md`. 사용자 자기 워크플로에서 `cd` 만으로 모드가 정해짐
- **alias 정비 필요** (기존 `pp=작업실/ss=세계관/nn=노무사` → 30p 중심 재할당)

### Phase 3: 하네스 2개 작성

`~/pp/30p/harnesses/` 새 폴더에:

1. **`code_drilldown.md`** (8.5 KB) — 5개 repo 실제 소스 코드 드릴다운 지시서
   - 대상: joonspk-research, a16z-infra/ai-town, tsinghua-fib-lab/agentsociety, camel-ai/oasis, sotopia-lab/sotopia
   - 특히 Stanford `prompt_template/run_gpt_prompt.py` (프롬프트 템플릿 수십 개) 포커스
   - 5가지 판정 기준 (철학 양립·이식 가능·Claude tick 모델·프롬프트 설계·30p 이미 해결?)
   - 산출물: `research/인간30에이전트2/code_drilldown.md` + commit

2. **`ux_design.md`** (16 KB) — 폴더 분리 + `session_flow.md` + alias 정비 지시서
   - 원래 대화형 모드 (Claude 초안 → 사용자 섹션별 수정)
   - 자율 실행 시에는 **초안 작성형 + TODO 인라인** 모드로 변환 지시
   - 섹션 0~9 (폴더 분리 / alias / 명령 어휘 / 시간 / play 흐름 / 관찰 명령 / 세션 시작 반응 / 외피 포맷 / 내면 포맷)

### Phase 4: Background Agent 자율 실행 (A → B 순차)

**의존성**: A 결과가 B 의 섹션 7~8(외피·내면 포맷)과 섹션 2(명령 어휘)에 반영될 수 있어 순차.

**Agent A (`harness_a`)** — `oh-my-claudecode:deep-executor` Opus, ~15분:
- 훔친 **11개** 패턴: poignancy 프롬프트 실물, retrieve 3항 공식 전문, scratch 실제 default, reflection 카운터 감소, focal_pt+insight 프롬프트, task_decomp few-shot, agent_chat_v2 루프, load_history_via_whisper, perform_interview, perceive att_bandwidth 중복 방지, ConceptNode 포맷
- 버린 **21개** 패턴: pathfinding, spatial_memory, pygame/Django, Convex physics, agentsociety protobuf+KVMemory+embedding, oasis recsys/asyncio/SQLite/23-action enum, sotopia evaluators/termination, Stanford embedding_key/kw_strength/event_triple LLM 호출, ai-town calculateImportance 인물 컨텍스트 누락, reflection 자동 발동 (관찰자 철학 충돌)
- 검증 실패 **6건**: agentsociety Reason/Route/Action Block 파일 미확보, agentsociety Maslow/TPB 수치화, **sotopia `structured_social_verifier.py` 실존하지 않음 확인** (Gemini 오보), run_gpt_prompt 프롬프트 .txt 여러 개, oasis rec_sys 수식 본체, ai-town reflectOnMemories 후속
- **가장 가치 있는 발견**:
  1. Stanford `poignancy_event_v1.txt` + ai-town `calculateImportance` — "brushing teeth, break up" 동일 예시 = LLM 0~10 안정 반환 검증 공식. 30p 이식 시 한국어 + 카페라떼 미학으로 번역 필수
  2. Stanford `retrieve.py` 의 `last_accessed` 자동 갱신 = "상기가 상기를 부른다" 자기 강화 루프
  3. `scratch.py` 실제 class default = `recency_decay=0.99, att_bandwidth=3, retention=5` (synthesis.md 의 `0.995, 8` 은 예시 JSON override 일 뿐). **synthesis.md 수치 오류 교정됨**
- commit: **`f70c2f3`** (`research: 인간30에이전트2 코드 드릴다운 — 5개 오픈소스 실제 코드 판정`)

**Agent B (`harness_b`)** — `oh-my-claudecode:deep-executor` Opus, ~15분:
- 대화형 → 초안 작성형 변환. TODO 17개 인라인 표시
- **5개 파일 생성/갱신** (833 insertions):
  - `30p/play/CLAUDE.md` (86줄) — 시뮬 모드 세션 규칙. Case A/B/C 시작 반응 + 금지 행위 감지 템플릿
  - `30p/CLAUDE.md` (106줄) — **최소 변경**. 기존 본문 보존. 상단 "작업 모드" 2줄 + "모드 분리 (2026-04-09 도입)" 섹션 + 폴더 구조 3줄 첨언만
  - `30p/docs/session_flow.md` (484줄) — 섹션 2~9 초안 전부 + 부록 A(건드리지 않은 것) + 부록 B(TODO 17개 일람) + 부록 C(수치 교정 메모)
  - `30p/harnesses/alias_proposal.md` (156줄) — `.zshrc` 진단 + Variant A/B/C + 추천 + 적용 방법. **`.zshrc` 직접 수정 X**
  - `30p/.state/queue.md` (+1줄) — "UX 설계 하네스 실행" [x] 추가
- A 의 11개 훔친 패턴 중 6개 반영 (poignancy·retrieve 메모·perform_interview·att_bandwidth·scratch 수치·load_history_via_whisper)
- A 가 버린 21개 중 *어느 것도* 반영 안 함 (특히 reflection 자동 발동·벡터 DB·프레임워크 의존)
- commit: **`259ec7e`** (`docs: 시뮬 모드 폴더 분리 + session_flow.md 초안 + alias 제안 (ux_design 하네스 자율 실행)`)

---

## 현재 상태

### 파일 지도 (이 세션 산출물)
```
~/pp/30p/
├── CLAUDE.md                                      ← 작업 모드 명시 (최소 갱신)
├── play/
│   └── CLAUDE.md                                  ← NEW 시뮬 모드 규칙
├── docs/
│   └── session_flow.md                            ← NEW 484줄 초안 + TODO 17개
├── harnesses/                                     ← NEW 폴더
│   ├── code_drilldown.md                          ← A 하네스
│   ├── ux_design.md                               ← B 하네스
│   └── alias_proposal.md                          ← alias 진단 + 제안 (미적용)
├── research/인간30에이전트2/
│   ├── synthesis.md                               ← 기존 (수치 교정 필요 주석)
│   └── code_drilldown.md                          ← NEW A 결과 (11/21/6)
└── .state/
    ├── current.md                                 ← 갱신 (진행 다음·미해결·주의)
    ├── queue.md                                   ← 갱신 (2건 [x] + 1줄)
    ├── log.md                                     ← 엔트리 추가
    └── handoffs/
        └── 2026-04-09_afternoon_handoff_research_ux.md  ← NEW 이 파일
```

### 큐 상태
- **1순위 완료 (이 세션)**: 리서치 훑기, UX 설계 하네스 실행
- **1순위 남음**: 시뮬 결과 사용자 검증, 관찰 명령 감 확인, 무대 선정, S001 검수 (이전 세션 미완)
- **새로 들어간 1순위**: `session_flow.md` TODO 17개 확정, `alias_proposal.md` 적용, `play/` 모드 첫 진입 테스트

### commit 히스토리 (최신 3개)
```
259ec7e docs: 시뮬 모드 폴더 분리 + session_flow.md 초안 + alias 제안 (ux_design 하네스 자율 실행)
f70c2f3 research: 인간30에이전트2 코드 드릴다운 — 5개 오픈소스 실제 코드 판정
780068c chore: pullim 서브모듈 갱신 — queue.md 정리
```

---

## 다음 세션이 할 일 (순서)

### 작업 모드 (`cd ~/pp/30p && cc`)

1. **`docs/session_flow.md` 부록 B (TODO 17개) 훑기** — 이견이 갈 지점부터 확정
   - 가장 중요: 폴더 이름 `play` 확정? / 외피 "긴장한 공기" 경계선 해석 허용 범위 / 내면 `본인은 X / 실제는 Y` 병기 유용한지 / `인터뷰 #N` 도입 여부
2. **`harnesses/alias_proposal.md` 검토 후 `~/.zshrc` 직접 수정** — Variant A 추천. 기존 `pp/ss/nn` 재할당
3. **새 터미널 여러 `source ~/.zshrc`** — 또는 새 터미널 열기

### 시뮬 모드 (`cd ~/pp/30p/play && cc`)

4. **첫 진입 테스트** — `시뮬 시작` 한 마디로 어감 확인. Claude 가 세계 상태 요약 + 다음 장면 후보 제시하는지
5. **만족스러우면 실제 play 호출** — 예: `5분 @ 강당 "투표 발표"`
6. **관찰 명령 감 확인** — `x #9` / `폰 #9` / `무의식 #9` (`seed_001_S002_vote1` 직후 맥락에서)

### 주의할 것

- **session_flow.md 는 *초안***. 돌려보기 전엔 어디가 불편한지 안 드러남. 첫 play 몇 번 돌려본 뒤 실제 불편한 지점 정정
- **reflection 트리거·retrieve 공식·att_bandwidth 엄격 적용 — 의도적 미도입**. 사용자가 진짜 필요하다고 느끼면 그때 별도 세션에서 도입. 지금은 단순 append-only
- **synthesis.md 수치 오류** (`0.995/8/8` → `0.99/3/5`). 부록 C 에 기록됨. 필요 시 synthesis.md 에도 주석
- **sotopia `structured_social_verifier.py` 인용 금지** (실존 X, Gemini 오보)
- **자동 tick 시뮬 유혹 경계**. 앞으로 리서치·확장 논의에서 *자동 시뮬*로 끌어당기는 방향 나오면 이 handoff 의 철학 축 재확인

---

## 사용자 상태 (세션 중 관찰)

- 사용자가 피곤한 상태로 자리 비움 (한 시간 반 다른 작업). 그 동안 자율 실행 결정
- 대화 초반 내가 *리서치를 훔쳐오려는 방향*으로 밀고 갔고 사용자가 4번 연속 교정. 피로 누적. *"내가 자꾸 본질을 잃는 것 같아"* 문장이 전환점
- 정확한 언어로 UX 를 설명했음: *문학의 탄생 / 건조한 수사기록 / 추측 대신 근거 있는 정답 접근 / 극단적 사건 실험실 / 세계는 멈춰있고 사용자가 감독*
- 사용자가 자리 비우면서 *"승인 없이 에이전트로 돌리고, 결과 받자마자 브리핑 + 세션 마무리"* 라는 명확한 위임. 이 위임을 본문에 그대로 수행

---

## 이 세션이 하지 **않은** 것

- ❌ 코드 (파이썬/쉘/TS) 작성 — 문서만
- ❌ 시드·옵션표·시뮬 결과·scripts/ 수정
- ❌ `~/.zshrc` 직접 수정 (제안만)
- ❌ `research/인간30에이전트2/synthesis.md` 수정 (수치 교정 기록은 session_flow.md 부록 C 에만)
- ❌ 실제 `play/` 모드 호출 테스트 (다음 세션 과제)
- ❌ 리서치 결과 해석 재작성 (A 드릴다운이 *새 발견*만 기록, synthesis.md 보존)
- ❌ 스킬 변환 (여전히 2순위)
- ❌ 아산두어스 지원서 (4월 18~19일 예정)

---

**세션 종료 시각**: 2026-04-09 오후 (사용자 부재 중 Agent 자율 실행 포함)
**전체 commit**: 2건 (`f70c2f3` + `259ec7e`)
**다음 세션 시작 진입점**: `cd ~/pp/30p && cc` → 이 handoff 읽기 → `current.md` → `queue.md`
