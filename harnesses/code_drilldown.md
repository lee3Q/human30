# Code Drilldown Harness

**용도**: 리서치에 나온 5개 LLM 에이전트 시뮬레이션 오픈소스를 *실제 소스 코드* 수준으로 훑고, 30p에 훔칠 가치 있는 코드·프롬프트·알고리즘이 있는지 **판정**한다.

**실행 방법**:
- 새 Claude Code 세션을 `~/pp/30p` 에서 시작
- 첫 메시지로 이 파일 내용 전체 붙여넣기 (또는 `@harnesses/code_drilldown.md` 로 참조)
- 세션 끝에 `git commit` 수행

---

## 배경 (세션 시작 시 먼저 읽을 것)

- 프로젝트 정체: `~/pp/30p/CLAUDE.md`, `~/pp/30p/.state/current.md`
- 이미 수행된 리서치 합성: `~/pp/30p/research/인간30에이전트2/synthesis.md`
  - Stanford retrieve.py, associative_memory.py, persona.py, reverie.py, scratch.py, reflect.py, requirements.txt 는 **일부** 확인됨 (WebFetch 요약)
  - 나머지 repo는 README만 봤음
- **중복 조회 금지**: 이미 합성문에 나온 내용은 재확인 X. 새 파일·새 관점에만 집중

---

## 30p 철학 (훔칠 가치 판정 기준)

1. **자동 tick 시뮬 아님** — 사용자 호출 기반 이벤트 체인. 사용자는 세계를 멈춤·재개할 수 있는 감독
2. **외피(드러난 행동) + 내면(생각·감각·기억) 동시 생성** — 한 번의 play 호출에서 Claude가 전원의 내면과 외피를 동시에 생성해 파일로 박음. 내면은 외피의 *근거*. 사용자 x-ray 호출 시 *재생성 없이* 파일 읽기만
3. **의존성 0** — stdlib Python만. 외부 패키지 도입 절대 금지
4. **Claude가 tick 수행자** — 파이썬은 분할·append·조립 역할만
5. **검열 0** — 수사기록 톤. 동정·미화·해석 금지
6. **단일 출력 금지** — 복수성이 본질. 같은 조건 재굴림 허용
7. **30인 복수성** — 요약·근사·필터링으로 캐릭터 차이 희석 금지

---

## 대상 repo (우선순위 순)

### 1. joonspk-research/generative_agents (Stanford) — 최우선
이미 일부 확인됨. **새로 훑을 파일**:

- `reverie/backend_server/persona/prompt_template/run_gpt_prompt.py`
  - 수십 개 LLM 프롬프트 템플릿 모음
  - 특히 볼 것:
    - `run_gpt_prompt_event_poignancy` — 이벤트 중요도 0~10 뽑기
    - `run_gpt_prompt_focal_pt` — 최근 기억에서 3개 초점 추출
    - `run_gpt_prompt_insight_and_guidance` — 누적 기억에서 통찰 뽑기
    - `run_gpt_prompt_decide_to_talk` / `run_gpt_prompt_decide_to_react` — 반응 결정
    - `run_gpt_prompt_task_decomp` — 계획 분해
    - `run_gpt_prompt_summarize_conversation` — 대화 요약
- `reverie/backend_server/persona/cognitive_modules/perceive.py` — 시야·주의 bandwidth
- `reverie/backend_server/persona/cognitive_modules/plan.py` — 계획 수립
- `reverie/backend_server/persona/cognitive_modules/execute.py` — 실행
- `reverie/backend_server/persona/cognitive_modules/converse.py` (있으면) — 대화 생성
- `reverie/backend_server/persona/memory_structures/spatial_memory.py` — 공간 메모리

**훔칠 가치 포인트**: 구조(tick 루프·벡터 DB)는 안 훔치지만 **프롬프트 기법·내면 생성 기법**은 철학과 무관해서 훔칠 수 있음.

### 2. a16z-infra/ai-town
README만 봤음. 핵심 파일:
- `convex/agent/memory.ts` — 메모리 저장·retrieve·reflection (Perplexity 리서치에 코드 일부 인용됨)
- `convex/aiTown/agent.ts` — 에이전트 tick
- `convex/aiTown/game.ts` — 메인 루프
- `convex/agent/conversation.ts` (있으면) — 대화 orchestration

**훔칠 가치 포인트**: Convex 구조는 전부 버릴 것. 하지만 *대화 상태 전이*·*말 걸기 결정 로직*은 볼 가치.

### 3. tsinghua-fib-lab/agentsociety
코드 미확인. 목표:
- `packages/agentsociety/` 하위 핵심 모듈 (정확한 경로는 repo 탐색 후 확정)
- memory 모듈 (Perplexity: `agentsociety/memory/memory.py` 언급)
- Reason Block / Route Block / Action Block 구현
- Maslow / Theory of Planned Behavior 코드화

**훔칠 가치 포인트**: Maslow·계획된 행동 이론의 *수치화*가 만약 실제 코드에 있다면 30p 옵션표 재검증용 참고 자료.

### 4. camel-ai/oasis
코드 미확인. 목표:
- `oasis/social_platform/recsys.py` (Gemini 주장, 검증 필요)
- `oasis/social_platform/platform.py`
- `oasis/agent/` (있으면)
- INTERVIEW action 구현 위치

**훔칠 가치 포인트**: INTERVIEW 메커니즘 (사용자가 캐릭터에게 직접 질문 던지기)이 30p 관찰 명령 확장 후보.

### 5. sotopia-lab/sotopia
코드 미확인. 목표:
- `structured_social_verifier.py` (Gemini 주장, 실존 검증 필요)
- 에피소드 생성 로직
- 평가 rubric

**훔칠 가치 포인트**: 만약 structured verifier가 실존한다면 사용자의 "투표 발표 직후 기분" 같은 서사에서 *사실 인덱스*를 자동 추출하는 패턴 참고 가능.

---

## 판정 기준 (각 패턴마다 5개 모두 YES일 때만 훔침)

1. **30p 철학과 양립?** (자동 tick·외부 의존성·프레임워크·요약 로직은 전부 NO)
2. **stdlib Python으로 이식 가능?** (벡터 DB·Django·Convex 필요하면 NO)
3. **Claude tick 수행 모델에 직접 쓸 수 있나?** (자동화 에이전트 전제면 NO)
4. **프롬프트 설계인 경우 30p 관찰 명령·내면 생성에 참고 가치?** (프롬프트 기법은 구조와 독립)
5. **30p가 이미 해결했나?** (Yes면 훔치지 말 것. 역검증용으로만 기록)

하나라도 NO → 기록하고 버림 (왜 버리는지 한 줄 사유).

---

## 산출물

**파일**: `~/pp/30p/research/인간30에이전트2/code_drilldown.md`

**포맷**:

```markdown
# Code Drilldown 결과 — 2026-04-09

## 1. 훔친 것 (철학 양립 + 이식 가능)

### [pattern_name] — from [repo]/[file_path]

**무엇**: 한 줄 요약

**원본 코드/프롬프트**:
\`\`\`
[그대로 인용. 10~30줄 이하]
\`\`\`

**30p 이식 방법**:
- 들어갈 위치: `30p/docs/...` 또는 `30p/scripts/...` 또는 프롬프트 템플릿
- 수정 필요: [원본에서 바꿀 것]
- 의존성 체크: stdlib만 쓰는지 확인

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용 가능: ✓
- 30p 해결 못한 자리 채움: ✓

---

## 2. 버린 것 (철학 충돌 or 이미 해결)

### [pattern_name] — from [repo]/[file_path]
**버리는 이유**: 한 줄

---

## 3. 검증 못 한 것 (fetch 실패 / 경로 미존재)

### [주장된 파일 경로]
**상황**: Gemini/Perplexity가 주장했지만 실제 repo에서 못 찾음 (또는 fetch 실패)
**조치**: 없음. 기록만.

---

## 4. 총평

[한 문단: 5개 repo에서 가치 있었던 것 / 이미 30p가 앞서 있는 부분 / 사용자 주의할 것]
```

---

## 제약 (엄격히)

- **과잉 창작 금지**. 실제 원본 코드에 있는 것만 인용. "있을 수 있다" 추측 금지
- **fetch 실패** 시 "fetch 실패: 사유"라고 명시. 추측으로 채우지 말 것
- **동일 패턴 중복 기록 금지**. Stanford와 ai-town이 같은 retrieve 공식이면 한쪽만 상세, 다른 쪽은 "동일" 표시
- **주 작업 = WebFetch**. github raw URL 직접 접근:
  - 형식: `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>`
  - 예: `https://raw.githubusercontent.com/joonspk-research/generative_agents/main/reverie/backend_server/persona/prompt_template/run_gpt_prompt.py`
  - HTML github 페이지가 아니라 raw 파일을 직접 가져올 것 (요약 아닌 전문 필요)
- **WebFetch 요약 신뢰 금지**. 큰 파일이면 여러 번 나눠서 가져오거나, 전체 길이가 필요하면 그 사실을 기록
- **코드 수정 금지**. 이 세션은 읽고 판정만. 30p 코드 변경은 별도 세션
- **토큰 아끼지 말 것**. 필요하면 긴 코드도 인용. 단 중복·불필요한 부분은 생략

---

## 최종 작업

1. `code_drilldown.md` 저장
2. `30p/.state/queue.md` 에서 "리서치 훑기" 항목 [x] 처리 + 링크 추가
3. `git add + commit`:
   ```
   research: 인간30에이전트2 코드 드릴다운 — 5개 오픈소스 실제 코드 판정
   ```

---

## 금지 사항

- ❌ 새 파이썬 스크립트 작성
- ❌ 30p 기존 파일 수정
- ❌ `.state/current.md` / 옵션표 / 시드 / 시뮬 결과 건드리기
- ❌ 리서치 결과 해석에 자유도 높은 추측 섞기
- ❌ `docs/session_flow.md` 같은 UX 작업 건드리기 (그건 ux_design.md 하네스가 담당)
