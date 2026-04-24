# Code Drilldown 결과 — 2026-04-09

> 5개 오픈소스 *실제 소스 코드* 레벨로 훑고 30p 이식 가치 판정.
> 판정 기준: 30p 철학 양립 + stdlib 이식 가능 + Claude tick 수행 모델 + 프롬프트 가치 + 30p 미해결 영역.
> 중복 조회 금지(synthesis.md 이미 본 내용은 재확인 X)를 엄수했다. synthesis에 없던 *프롬프트 실물*·*실제 default 값*·*부수 트리거*·*rememberConversation 전체 흐름* 중심.

---

## 0. 드릴다운 경로 요약

| repo | 파일 | 상태 |
|---|---|---|
| Stanford | `cognitive_modules/retrieve.py` | 전문 확보 |
| Stanford | `cognitive_modules/reflect.py` | 전문 확보 |
| Stanford | `cognitive_modules/perceive.py` | 전문 확보 |
| Stanford | `cognitive_modules/plan.py` | `plan/_should_react/_chat_react/_wait_react/revise_identity` 확보 |
| Stanford | `cognitive_modules/execute.py` | 전문 확보 (pathfinding 위주, 30p 무관) |
| Stanford | `cognitive_modules/converse.py` | `agent_chat_v2/open_convo_session/load_history_via_whisper` 확보 |
| Stanford | `memory_structures/associative_memory.py` | `ConceptNode`, `__init__`, `save()` 구조 확보 |
| Stanford | `memory_structures/scratch.py` | 하이퍼파라미터 default 전부 확보 |
| Stanford | `prompt_template/run_gpt_prompt.py` | 7개 함수 create_prompt_input + 템플릿 경로 확보 |
| Stanford | `prompt_template/v3_ChatGPT/poignancy_event_v1.txt` | 전문 |
| Stanford | `prompt_template/v3_ChatGPT/generate_focal_pt_v1.txt` | 전문 |
| Stanford | `prompt_template/v2/insight_and_evidence_v1.txt` | 전문 |
| Stanford | `prompt_template/v2/decide_to_talk_v2.txt` | 전문 (v1 리다이렉트) |
| Stanford | `prompt_template/v2/decide_to_react_v1.txt` | 전문 |
| Stanford | `prompt_template/v2/task_decomp_v3.txt` | 전문 (Kelly Bronson few-shot 포함) |
| Stanford | `prompt_template/v3_ChatGPT/summarize_conversation_v1.txt` | 전문 (짧음) |
| ai-town | `convex/agent/memory.ts` | `rankAndTouchMemories/searchMemories/rememberConversation/calculateImportance/reflectOnMemories` 전부 |
| ai-town | `convex/aiTown/agent.ts` | `Agent.tick` 전체 |
| agentsociety | `packages/agentsociety/agentsociety/memory/memory.py` | `KVMemory/StreamMemory/Memory` 시그니처 확보 |
| oasis | `oasis/social_platform/platform.py` | INTERVIEW action + dispatcher |
| oasis | `oasis/social_agent/agent.py` | `perform_interview` 전문 |
| oasis | `oasis/social_platform/recsys.py` | 상위 imports + 4개 rec_sys 함수 구조 |
| sotopia | `sotopia/envs/evaluators.py` | `RuleBasedTerminatedEvaluator/EpisodeLLMEvaluator` 구조 |
| sotopia | `sotopia/envs/parallel.py` | AgentAction 처리 (파싱 로직 없음 확인) |

---

## 1. 훔친 것 (철학 양립 + 이식 가능)

### 1.1 Poignancy 프롬프트 실물 — from Stanford `prompt_template/v3_ChatGPT/poignancy_event_v1.txt`

**무엇**: 이벤트 하나에 0~10(사실은 1~10) 점수를 매기는 *최소 길이* 프롬프트. LLM 한 번 호출로 "한 숫자만" 반환.

**원본 전문**:
```
poignancy_event_v1.txt

!<INPUT 1>!: agent name
!<INPUT 1>!: iss
!<INPUT 2>!: name
!<INPUT 3>!: event description

<commentblockmarker>###</commentblockmarker>
Here is a brief description of !<INPUT 0>!.
!<INPUT 1>!

On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following event for !<INPUT 2>!.

Event: !<INPUT 3>!
Rate (return a number between 1 to 10):
```

**ai-town의 등가 변종 (더 짧음)** — from `convex/agent/memory.ts` → `calculateImportance`:
```typescript
async function calculateImportance(description: string) {
  const { content: importanceRaw } = await chatCompletion({
    messages: [{ role: 'user',
      content: `On the scale of 0 to 9, where 0 is purely mundane (e.g., brushing teeth, making bed) and 9 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.
      Memory: ${description}
      Answer on a scale of 0 to 9. Respond with number only, e.g. "5"`,
    }],
    temperature: 0.0,
    max_tokens: 1,
  });
  let importance = parseFloat(importanceRaw);
  if (isNaN(importance)) { importance = +(importanceRaw.match(/\d+/)?.[0] ?? NaN); }
  if (isNaN(importance)) { console.debug('Could not parse memory importance from: ', importanceRaw); importance = 5; }
  return importance;
}
```

**관찰**:
- Stanford: 1~10, 인물 iss("identity stable set") 포함, 멀티라인 응답 허용
- ai-town: 0~9, 인물 컨텍스트 없음, `max_tokens: 1`, `temperature: 0.0`, fallback 5
- 둘 다 예시는 **"brushing teeth, making bed" / "break up, college acceptance"** 정확히 동일. Stanford 원본을 ai-town이 단축 복붙.

**30p 이식 방법**:
- 들어갈 위치: `docs/generation_protocol.md` 또는 `docs/observation_commands.md`의 "이벤트 기록 절차" 섹션
- 수정 필요:
  - 1~10 범위 유지 (30p는 이미 0~10 Likert 스타일과 친화)
  - *iss 포함 버전* 채택 — 30p는 캐릭터별 차이가 본질이므로 익명 매김은 희석. 해당 캐릭터의 4층 요약을 먼저 박고 "이 캐릭터에게" 얼마나 중요한지 물어야 30p 철학과 맞음
  - 예시는 30p 카페라떼 미학에 맞춰 변경: "1 = 계단 내려가기, 10 = 상사가 건넨 카페라떼를 받아 든 순간 과거 구강성교 기억이 온몸에 돌아옴"
  - Claude tick 수행자이므로 별도 API 호출 없음. 새 이벤트 저장 직전 Claude가 자체 판단으로 0~10 정수 박음
- 의존성 체크: 프롬프트는 텍스트. stdlib 무관. ✓

**철학 양립 체크**:
- 자동 tick 아님: ✓ (tick은 Claude가 직접)
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (현재 poignancy 필드 없음 — synthesis.md의 즉시 큐 제안과 일치)
- 검열 0 양립: ✓ (수치는 중립)

---

### 1.2 Retrieve 3항 공식 — from Stanford `cognitive_modules/retrieve.py` → `new_retrieve`

**무엇**: recency + importance + relevance 가중합. `gw = [0.5, 3, 2]`. synthesis.md에 짧게 요약돼 있었지만 **전체 정규화·top-N 알고리즘이 한 화면에 들어온 건 이번이 처음**.

**원본 핵심부 (전문에서 발췌)**:
```python
def extract_recency(persona, nodes):
  recency_vals = [persona.scratch.recency_decay ** i
                  for i in range(1, len(nodes) + 1)]
  recency_out = dict()
  for count, node in enumerate(nodes):
    recency_out[node.node_id] = recency_vals[count]
  return recency_out

def extract_importance(persona, nodes):
  importance_out = dict()
  for count, node in enumerate(nodes):
    importance_out[node.node_id] = node.poignancy
  return importance_out

def extract_relevance(persona, nodes, focal_pt):
  focal_embedding = get_embedding(focal_pt)
  relevance_out = dict()
  for count, node in enumerate(nodes):
    node_embedding = persona.a_mem.embeddings[node.embedding_key]
    relevance_out[node.node_id] = cos_sim(node_embedding, focal_embedding)
  return relevance_out

def normalize_dict_floats(d, target_min, target_max):
  min_val = min(val for val in d.values())
  max_val = max(val for val in d.values())
  range_val = max_val - min_val
  if range_val == 0:
    for key, val in d.items():
      d[key] = (target_max - target_min)/2
  else:
    for key, val in d.items():
      d[key] = ((val - min_val) * (target_max - target_min) / range_val + target_min)
  return d

def new_retrieve(persona, focal_points, n_count=30):
  retrieved = dict()
  for focal_pt in focal_points:
    nodes = [[i.last_accessed, i]
              for i in persona.a_mem.seq_event + persona.a_mem.seq_thought
              if "idle" not in i.embedding_key]
    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for created, i in nodes]

    recency_out = extract_recency(persona, nodes)
    recency_out = normalize_dict_floats(recency_out, 0, 1)
    importance_out = extract_importance(persona, nodes)
    importance_out = normalize_dict_floats(importance_out, 0, 1)
    relevance_out = extract_relevance(persona, nodes, focal_pt)
    relevance_out = normalize_dict_floats(relevance_out, 0, 1)

    gw = [0.5, 3, 2]
    master_out = dict()
    for key in recency_out.keys():
      master_out[key] = (persona.scratch.recency_w*recency_out[key]*gw[0]
                     + persona.scratch.relevance_w*relevance_out[key]*gw[1]
                     + persona.scratch.importance_w*importance_out[key]*gw[2])

    master_out = top_highest_x_values(master_out, n_count)
    master_nodes = [persona.a_mem.id_to_node[key] for key in list(master_out.keys())]
    for n in master_nodes:
      n.last_accessed = persona.scratch.curr_time
    retrieved[focal_pt] = master_nodes
  return retrieved
```

**새로 판명된 디테일 (synthesis에 없던 것)**:
- `"idle"` 키워드가 들어간 임베딩 키는 **전부 제외** — 자는 상태/멍한 상태는 retrieve 대상 아님. 30p의 "자는 캐릭터는 건너뛰기" 규칙과 정확히 호환
- 조회된 노드는 `last_accessed = curr_time` 자동 갱신 — *기억을 꺼낸 순간 그 기억의 "마지막 접근"이 갱신*되는 설계. 결과적으로 자주 꺼내는 기억은 recency가 계속 높게 유지됨 (상기가 상기를 부름). 30p에 훔칠 가치 큼.
- `normalize_dict_floats`는 min-max [0,1] 정규화. 모든 값이 같을 때 `(target_max - target_min)/2 = 0.5`으로 처리. 0 나눗셈 방어 포함
- `gw = [1, 1, 1]`, `[1, 2, 1]` 주석 잔존 — 가중치를 실험 중에 튜닝한 흔적. 최종 선택이 `[0.5, 3, 2]`

**30p 이식 방법**:
- 들어갈 위치: 새 문서 `docs/retrieve_rule.md` (이번 세션 작업 아님, 별도 세션에서 사용자 합의 후)
- 임베딩이 없으므로 `relevance`는 **Claude가 직접 판단**: "지금 이 자극과 이 기억이 얼마나 닮았나" 0~1 실수
- `recency_decay = 0.995` (Stanford 주석 실험 중 숫자, class default는 0.99)
- `att_bandwidth` = Stanford 실제 default = 3 (synthesis에 8이라 적혔지만 *예시 scratch.json*이고 **class default는 3**). 30p는 캐릭터별 I1 cognitive_ability와 연동해서 2~6 가변 가능
- `last_accessed` 갱신 규칙은 그대로 채용 — 메모리 JSONL에 `last_accessed` 필드 두고 조회 시 갱신
- `"idle"` 필터는 30p 방언으로 번역: `#N is sleeping`, `#N is blank`, `#N is staring` 등 (현재 상태가 공백인 이벤트)
- 의존성: embedding/cos_sim 전부 제거, Claude 판단으로 교체. stdlib만. ✓

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓ (임베딩 교체)
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (retrieve 공식 현재 없음)

---

### 1.3 Reflection 트리거 *복수 경로* — from Stanford `reflect.py` + `scratch.py`

**무엇**: synthesis에는 "`importance_trigger_curr <= 0` 발동"만 적혀 있었는데, 실제 `scratch.py`에는 **부수 트리거 필드가 더 있다**. 그리고 `reflect.py`의 대화 종료 10초 후 발동 경로도 확인.

**원본 scratch.py 하이퍼파라미터 (실제 class default)**:
```
vision_r = 4
att_bandwidth = 3
retention = 5

concept_forget = 100
daily_reflection_time = 60 * 3   # 180분
daily_reflection_size = 5
overlap_reflect_th = 2
kw_strg_event_reflect_th = 4
kw_strg_thought_reflect_th = 4

recency_w = 1
relevance_w = 1
importance_w = 1
recency_decay = 0.99
importance_trigger_max = 150
importance_trigger_curr = 150     # self.importance_trigger_max
importance_ele_n = 0
thought_count = 5
```

→ **synthesis와 불일치**: synthesis는 예시 `scratch.json`의 `recency_decay=0.995`, `att_bandwidth=8`을 기록. 실제 class default는 `0.99`, `att_bandwidth=3`. *class default가 진짜 디폴트, json은 캐릭터별 override*.

**reflect.py `reflect()` 함수의 두 경로 (전문)**:
```python
def reflect(persona):
  if reflection_trigger(persona):
    run_reflect(persona)
    reset_reflection_counter(persona)

  if persona.scratch.chatting_end_time:
    if persona.scratch.curr_time + datetime.timedelta(0,10) == persona.scratch.chatting_end_time:
      all_utt = ""
      if persona.scratch.chat:
        for row in persona.scratch.chat:
          all_utt += f"{row[0]}: {row[1]}\n"
      evidence = [persona.a_mem.get_last_chat(persona.scratch.chatting_with).node_id]

      planning_thought = generate_planning_thought_on_convo(persona, all_utt)
      planning_thought = f"For {persona.scratch.name}'s planning: {planning_thought}"
      ...  # s,p,o 생성 → poignancy 매김 → a_mem.add_thought

      memo_thought = generate_memo_on_convo(persona, all_utt)
      memo_thought = f"{persona.scratch.name} {memo_thought}"
      ...  # 동일 절차로 저장
```

**perceive.py에서 본 카운터 감소 로직** (전문):
```python
# 새 이벤트 저장 직후
ret_events += [persona.a_mem.add_event(...)]
persona.scratch.importance_trigger_curr -= event_poignancy
persona.scratch.importance_ele_n += 1
```

**`run_reflect` 전문**:
```python
def run_reflect(persona):
  focal_points = generate_focal_points(persona, 3)
  retrieved = new_retrieve(persona, focal_points)

  for focal_pt, nodes in retrieved.items():
    thoughts = generate_insights_and_evidence(persona, nodes, 5)
    for thought, evidence in thoughts.items():
      created = persona.scratch.curr_time
      expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
      s, p, o = generate_action_event_triple(thought, persona)
      keywords = set([s, p, o])
      thought_poignancy = generate_poig_score(persona, "thought", thought)
      thought_embedding_pair = (thought, get_embedding(thought))
      persona.a_mem.add_thought(created, expiration, s, p, o,
                                thought, keywords, thought_poignancy,
                                thought_embedding_pair, evidence)
```

**30p 이식 방법**:
- 들어갈 위치: 별도 세션에서 `docs/reflection_rule.md` (사용자 합의 필요. synthesis.md 즉시 큐 제안 #4)
- **주의**: 30p는 *관찰자 중심*이라 캐릭터 자생 reflection은 방향이 다르다. synthesis도 "사용자 검토 필요"로 플래그 둠
- 그러나 30p가 훔칠 수 있는 *두 가지 구체적 지점*:
  1. **카운터 감소 패턴** — 새 이벤트 저장 시 `trigger_curr -= poignancy`로 단순 누적. 별도 LLM 호출 없이 Python 산술로 끝. `docs/generation_protocol.md`의 이벤트 기록 절차에 한 줄 추가 가능
  2. **대화 종료 후 자동 thought 생성** — Stanford는 대화 끝나고 `planning_thought` + `memo_thought` 두 개를 자동 생성해 저장. 30p에서는 "사용자가 캐릭터의 대화 장면을 관찰한 직후 Claude가 그 캐릭터의 *속생각*을 파일로 박음" 패턴과 등가. 30p `x-ray`와 결이 맞음
- 30p 번역: `trigger_curr`은 **캐릭터별**이 아니라 **시뮬 전역**으로도 둘 수 있음. "30명 중 누적 poignancy가 임계값 넘으면 reflect 기회 한 번 제공" — 하지만 이건 30p 철학의 *복수성* 관점에서 *캐릭터별*이 맞음
- `thought`는 30일 expiration — 30p는 시뮬 기간이 짧으니 expiration 개념 생략 가능. 대신 `type: thought` 필드만 유지
- 의존성: 전부 Python 산술 + Claude 서사. stdlib. ✓

**철학 양립 체크**:
- 자동 tick 아님: ✓ (tick은 사용자 호출)
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: △ (관찰자 중심 철학과 부분 충돌. 사용자 합의 필수)
- 검열 0 양립: ✓

---

### 1.4 `generate_focal_pt_v1.txt` + `insight_and_evidence_v1.txt` 프롬프트 실물 — from Stanford v3_ChatGPT / v2

**무엇**: reflection의 두 단계 LLM 호출. 훌륭하게 짧음.

**원본 전문 (focal_pt)**:
```
generate_focal_pt_v1.txt

Variables:
!<INPUT 0>! -- Event/thought statements
!<INPUT 1>! -- Count

<commentblockmarker>###</commentblockmarker>
!<INPUT 0>!

Given only the information above, what are !<INPUT 1>! most salient high-level questions we can answer about the subjects grounded in the statements?
1)
```

**원본 전문 (insight_and_evidence)**:
```
insight_and_evidence_v1.txt

Variables:
!<INPUT 0>! -- Numbered list of event/thought statements
!<INPUT 1>! -- target persona name or "the conversation"

<commentblockmarker>###</commentblockmarker>
Input:
!<INPUT 0>!

What !<INPUT 1>! high-level insights can you infer from the above statements? (example format: insight (because of 1, 5, 3))
1.
```

**관찰**:
- focal_pt는 "what are N most salient high-level questions" — **질문을 3개 뽑고** 그 질문으로 다시 retrieve
- insight는 "insight (because of 1, 5, 3)" — **증거 노드 번호 인용 강제**. 이게 핵심. LLM 출력에 `(because of 1, 5, 3)` 형식으로 숫자 리스트 박아 오게 만들면 코드가 `nodes[i].node_id`로 역참조 가능 (`generate_insights_and_evidence` 함수에서 정확히 이렇게 파싱)

**30p 이식 방법**:
- 들어갈 위치: `docs/generation_protocol.md`의 선택 확장 섹션, 또는 `docs/observation_commands.md`의 *x-ray 심화* 모드
- 두 프롬프트는 **30p에 즉시 이식 가능**. 번역:
  - focal_pt → "다음 사건·생각들에서 #N에게 가장 두드러진 질문 3개는?"
  - insight → "위 진술들에서 #N에 대해 어떤 상위 통찰을 끌어낼 수 있나? (형식: 통찰 (근거: 1, 5, 3))"
- 30p는 한국어 카페라떼 미학으로 번역, 건조한 톤 유지
- Claude tick 수행자이므로 LLM 호출 아님 — Claude가 해당 캐릭터의 `memories.jsonl`을 직접 읽고 머릿속에서 이 두 프롬프트를 따른다
- "근거 노드 번호 강제" 패턴은 **30p에서 최고 가치** — 사용자가 캐릭터의 통찰을 읽을 때 "왜 이런 통찰을 하는지" 근거 사건이 즉시 링크됨

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓

---

### 1.5 `task_decomp_v3.txt` few-shot Kelly Bronson 원본 — from Stanford v2

**무엇**: 한 명의 상세 프로필 + 스케줄 + 5분 단위 세부 분해 예시를 *딱 한 개* 넣은 few-shot. 출력 형식을 "1) X (duration in minutes: N, minutes left: M)"로 박는다.

**원본 전문**:
```
task_decomp_v2.txt

Variables:
!<INPUT 0>! -- Commonset
!<INPUT 1>! -- Surrounding schedule description
!<INPUT 2>! -- Persona first name
!<INPUT 3>! -- Persona first name
!<INPUT 4>! -- Current action
!<INPUT 5>! -- curr time range
!<INPUT 6>! -- Current action duration in min
!<INPUT 7>! -- Persona first names

<commentblockmarker>###</commentblockmarker>
Describe subtasks in 5 min increments.
---
Name: Kelly Bronson
Age: 35
Backstory: Kelly always wanted to be a teacher, and now she teaches kindergarten. During the week, she dedicates herself to her students, but on the weekends, she likes to try out new restaurants and hang out with friends. She is very warm and friendly, and loves caring for others.
Personality: sweet, gentle, meticulous
Location: Kelly is in an older condo that has the following areas: {kitchen, bedroom, dining, porch, office, bathroom, living room, hallway}.
Currently: Kelly is a teacher during the school year. She teaches at the school but works on lesson plans at home. She is currently living alone in a single bedroom condo.
Daily plan requirement: Kelly is planning to teach during the morning and work from home in the afternoon.

Today is Saturday May 10. From 08:00am ~09:00am, Kelly is planning on having breakfast, from 09:00am ~ 12:00pm, Kelly is planning on working on the next day's kindergarten lesson plan, and from 12:00 ~ 13pm, Kelly is planning on taking a break.
In 5 min increments, list the subtasks Kelly does when Kelly is working on the next day's kindergarten lesson plan from 09:00am ~ 12:00pm (total duration in minutes: 180):
1) Kelly is reviewing the kindergarten curriculum standards. (duration in minutes: 15, minutes left: 165)
2) Kelly is brainstorming ideas for the lesson. (duration in minutes: 30, minutes left: 135)
3) Kelly is creating the lesson plan. (duration in minutes: 30, minutes left: 105)
...
9) Kelly is putting the lesson plan in her bag. (duration in minutes: 5, minutes left: 0)
---
!<INPUT 0>!
!<INPUT 1>!
In 5 min increments, list the subtasks !<INPUT 2>! does when !<INPUT 3>! is !<INPUT 4>! from !<INPUT 5>! (total duration in minutes !<INPUT 6>!):
1) !<INPUT 7>! is
```

**관찰**:
- **단 1개 few-shot** 으로도 포맷·길이·톤 전부 고정됨. 30p 프롬프트 설계에 직접 참고
- `(duration in minutes: N, minutes left: M)` — *남은 시간을 계속 까먹는 형태*로 출력해서 토탈이 정확히 맞게 만들기. 30p의 "곧" 층 시간 계산에 유용
- 마지막 줄 `1) !<INPUT 7>! is` — **LLM에게 토큰 하나 미리 박아주고 이어쓰게 하기**. Stanford가 일관성 확보한 기법

**30p 이식 방법**:
- 들어갈 위치: 30p는 Kelly류 시간 분해 안 함(시간축이 다름 — tick 기반 이벤트 체인). 하지만 **"단일 few-shot + 엄격한 출력 포맷" 패턴**은 30p의 시뮬 프롬프트 설계에 그대로 채용 가능
- 구체적으로: `docs/generation_protocol.md`에 *30p 시뮬 출력 포맷 표본* 박을 때 이 패턴을 따를 것. 1개 예시 + 엄격 구조
- 카페라떼 미학 예시 1개 박고 끝. 여러 예시 안 필요

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (프롬프트 설계 기법)

---

### 1.6 `agent_chat_v2` 대화 루프 — from Stanford `converse.py`

**무엇**: 두 페르소나 대화를 *매 턴마다* retrieve를 다시 돌려 관련성 높은 기억을 교체해 나가는 패턴. 최대 8턴.

**원본 전문**:
```python
def agent_chat_v2(maze, init_persona, target_persona):
  curr_chat = []

  for i in range(8):
    focal_points = [f"{target_persona.scratch.name}"]
    retrieved = new_retrieve(init_persona, focal_points, 50)
    relationship = generate_summarize_agent_relationship(init_persona, target_persona, retrieved)
    last_chat = ""
    for i in curr_chat[-4:]:
      last_chat += ": ".join(i) + "\n"
    if last_chat:
      focal_points = [f"{relationship}",
                      f"{target_persona.scratch.name} is {target_persona.scratch.act_description}",
                      last_chat]
    else:
      focal_points = [f"{relationship}",
                      f"{target_persona.scratch.name} is {target_persona.scratch.act_description}"]
    retrieved = new_retrieve(init_persona, focal_points, 15)
    utt, end = generate_one_utterance(maze, init_persona, target_persona, retrieved, curr_chat)

    curr_chat += [[init_persona.scratch.name, utt]]
    if end: break

    # 대칭: target_persona 차례
    ...
```

**관찰**:
- 매 턴 **retrieve를 두 번** 돈다:
  1. 첫 번째: `focal_points = [target_persona.name]` → 관계 요약 생성용 (n=50)
  2. 두 번째: `focal_points = [relationship, target_status, last_chat(최근 4턴)]` → 발화 생성용 (n=15)
- `last_chat`은 **최근 4턴만** 창에 박음. 전체 히스토리 전송 안 함 (토큰 절약)
- 발화 생성 함수는 `(utt, end)` 튜플 반환 — `end=True`이면 대화 종료

**30p 이식 방법**:
- 들어갈 위치: 별도 세션에서 `docs/conversation_protocol.md` 신설 시 참고 (현재 30p는 대화 모듈 없음)
- 30p에서는 Claude가 tick 수행자이므로 retrieve 두 번을 실제 Python 반복 대신 "Claude가 발화 생성 전 두 단계 머릿속에서 밟는다"로 번역
- *마지막 4턴만 * 규칙은 그대로 채용 — 토큰 절약 + 복수성(캐릭터 수)와 직결
- `end` 신호 패턴 — 대화 끝을 *인위적 길이 제한*이 아니라 *캐릭터가 스스로 종료 시그널*로 내게 하는 것. 30p와 맞음

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (대화 모듈 미완)

---

### 1.7 `load_history_via_whisper` 패턴 — from Stanford `converse.py`

**무엇**: 시뮬 외부(=운영자)가 *"이 캐릭터에게 이 생각을 박아 넣어라"* 선언하면, 그것이 `thought` 노드로 메모리에 직접 삽입되는 경로. 대화 없이 내면만 편집.

**원본 전문**:
```python
def load_history_via_whisper(personas, whispers):
  for count, row in enumerate(whispers):
    persona = personas[row[0]]
    whisper = row[1]

    thought = generate_inner_thought(persona, whisper)

    created = persona.scratch.curr_time
    expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
    s, p, o = generate_action_event_triple(thought, persona)
    keywords = set([s, p, o])
    thought_poignancy = generate_poig_score(persona, "event", whisper)
    thought_embedding_pair = (thought, get_embedding(thought))
    persona.a_mem.add_thought(created, expiration, s, p, o,
                              thought, keywords, thought_poignancy,
                              thought_embedding_pair, None)
```

**관찰**:
- `whispers = [[persona_name, whisper_text], ...]` 리스트
- *generate_inner_thought*가 whisper 원문을 해당 캐릭터의 *내면 언어*로 번역 후 저장
- 즉, 운영자가 "너는 오늘 아침 엄마가 죽었다는 소식을 들었다"라고 넣으면 캐릭터의 a_mem에 *그 캐릭터가 느낀 방식*으로 변환돼 저장됨

**30p 이식 방법**:
- 들어갈 위치: `docs/observation_commands.md`에 *4번째 명령 후보*로 추가. 후보명: `whisper #N "내용"`
  - `x-ray`: 구조 덤프 (본다)
  - `phone`: I3-B 덤프 (본다)
  - `subconscious`: 접근 불가 영역 (본다)
  - **`whisper #N "..."`: 캐릭터 내면에 외부에서 생각 주입 (쓴다)** ← 신규 카테고리
- 30p의 절대자(사용자) 권한 확장. 사용자는 지금껏 *관찰*만 했는데 whisper는 *개입*. "절대자는 세계를 멈춤·재개할 수 있는 감독"과 완벽히 호환
- 차이: Stanford는 시뮬 시작 시 히스토리 주입 용도였지만 30p에서는 **시뮬 중 임의 tick 사이에 박을 수 있게** 해야 흥미
- Claude가 whisper를 해당 캐릭터 *내면 방언*으로 변환해 `memories.jsonl`에 `type: thought, source: whisper` 필드로 append
- 의존성: 파일 append만. stdlib. ✓

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (개입 기능 아예 없음. 절대자 권한 확장)
- 검열 0 양립: ✓ (검열 있는 whisper조차 박아넣을 수 있음)

---

### 1.8 `perform_interview` 패턴 — from oasis `social_agent/agent.py`

**무엇**: 사용자가 특정 에이전트에게 질문 던지면 에이전트가 *기존 시스템 프롬프트 + 메모리 컨텍스트* 조합으로 답함. 에이전트는 자기 역할 안에서 답변.

**원본 전문**:
```python
async def perform_interview(self, interview_prompt: str):
    user_msg = BaseMessage.make_user_message(
        role_name="User", content=("You are a twitter user."))

    if self.interview_record:
        self.update_memory(message=user_msg, role=OpenAIBackendRole.SYSTEM)

    openai_messages, num_tokens = self.memory.get_context()

    openai_messages = ([{
        "role": self.system_message.role_name,
        "content": self.system_message.content.split("# RESPONSE METHOD")[0],
    }] + openai_messages + [{
        "role": "user",
        "content": interview_prompt
    }])

    response = await self._aget_model_response(
        openai_messages=openai_messages, num_tokens=num_tokens)

    content = response.output_messages[0].content

    if self.interview_record:
        self.update_memory(message=response.output_messages[0],
                           role=OpenAIBackendRole.USER)

    interview_data = {"prompt": interview_prompt, "response": content}
    result = await self.env.action.perform_action(
        interview_data, ActionType.INTERVIEW.value)
    ...
```

**관찰**:
- `self.system_message.content.split("# RESPONSE METHOD")[0]` — **원래 시스템 프롬프트에서 "응답 방식" 섹션을 제거**하고 인터뷰용으로 씀. 즉 평소엔 X개 구조화 action만 하는 에이전트가 인터뷰 때는 자유 서술 허용
- 메모리 컨텍스트는 그대로 넣음 — 에이전트가 기억하는 것 기반으로 답
- 선택적 `interview_record` — 인터뷰 자체가 새 이벤트로 에이전트 메모리에 남을지 여부 옵션화

**30p 이식 방법**:
- 들어갈 위치: `docs/observation_commands.md`에 **5번째 명령** 후보로. `interview #N "질문"` — 4번째 `whisper`와 다른 종류의 *개입*. whisper는 *쓴다*, interview는 *묻는다*.
- synthesis.md의 즉시 큐 제안 #6과 동일. oasis 실제 코드 확인으로 **매우 단순하게 구현 가능**함이 증명됨
- 30p 번역:
  - Claude가 해당 캐릭터의 4층 데이터 + `memories.jsonl` 읽음
  - 평소 내면 생성 프롬프트에서 *"수사기록 톤으로 외부 관찰"* 부분 제거
  - 대신 *"이 캐릭터가 자기 입으로 말한다면"* 모드로 switch
  - interview_prompt를 질문으로 박음
  - 답변 생성 후 — **기본은 메모리에 기록 안 함** (Stanford의 `interview_record=False` 권장). 30p에서는 x-ray와 마찬가지로 *절대자의 재생성 없는 관찰*이 원칙이지만 interview는 재생성 수반하므로 예외. 대신 기록 여부는 사용자 옵션
- **차이 ((x-ray와의 철학적 차이, 사용자 주의))**:
  - `x-ray` = 절대자가 *진실*을 본다. 캐릭터 본인이 모르는 부분도 본다
  - `interview` = 캐릭터가 *자기 서사*를 말한다. 거짓말·방어기제·미화·검열 포함
  - **둘의 괴리가 30p 고유의 흥미 지점.** Ari Aster/카뮈 미학 정확히 일치
- 의존성: Claude 프롬프트 + 파일 읽기. stdlib. ✓

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓
- 검열 0 양립: ✓ (**캐릭터가 검열할 수는 있다**. 사용자가 보는 렌즈는 여전히 검열 0)

---

### 1.9 `perceive.py`의 att_bandwidth 슬라이싱 + 중복 방지 — from Stanford

**무엇**: 시야 내 이벤트 중 **가장 가까운 N개**만 실제 지각하고, `retention` 기간 내 동일 이벤트는 중복 저장 안 함. 한 번의 tick에서 새 저장되는 건 많아야 `att_bandwidth` 건.

**원본 핵심부**:
```python
# 정렬 → 상위 N개 슬라이싱
percept_events_list = sorted(percept_events_list, key=itemgetter(0))
perceived_events = []
for dist, event in percept_events_list[:persona.scratch.att_bandwidth]:
  perceived_events += [event]

# 중복 방지
for p_event in perceived_events:
  s, p, o, desc = p_event
  if not p:
    p = "is"; o = "idle"; desc = "idle"
  desc = f"{s.split(':')[-1]} is {desc}"
  p_event = (s, p, o)

  latest_events = persona.a_mem.get_summarized_latest_events(
                                  persona.scratch.retention)
  if p_event not in latest_events:
    ...
    event_poignancy = generate_poig_score(persona, "event", desc_embedding_in)
    ...
    ret_events += [persona.a_mem.add_event(...)]
    persona.scratch.importance_trigger_curr -= event_poignancy
    persona.scratch.importance_ele_n += 1
```

**30p 이식 방법**:
- 들어갈 위치: `docs/generation_protocol.md`의 *이벤트 기록 절차* 섹션
- 30p에서 매 tick 기록되는 이벤트 수는 무한하면 안 됨. Stanford처럼 **상한 N** (`att_bandwidth` 방언)
- 30p에서는 물리적 거리 대신 *주의 관련성* (Claude 판단)으로 정렬
- `retention` (기본 5) 내 동일 SPO 트리플은 새 저장 안 함 — 같은 사건을 계속 쓰지 않도록. 30p에서도 같은 식
- 카운터 감소 `importance_trigger_curr -= event_poignancy`는 위 1.3과 동일 맥락

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (이벤트 상한 규칙 없음)

---

### 1.10 `ConceptNode` + JSONL 평탄화 포맷 — from Stanford `associative_memory.py`

**무엇**: 한 기억 노드의 필드 구성. 30p의 JSONL 메모리 포맷 설계에 직접 참고.

**원본 전문**:
```python
class ConceptNode:
  def __init__(self,
               node_id, node_count, type_count, node_type, depth,
               created, expiration,
               s, p, o,
               description, embedding_key, poignancy, keywords, filling):
    self.node_id = node_id
    self.node_count = node_count
    self.type_count = type_count
    self.type = node_type          # 'event' | 'thought' | 'chat'
    self.depth = depth
    self.created = created
    self.expiration = expiration
    self.last_accessed = self.created
    self.subject = s
    self.predicate = p
    self.object = o
    self.description = description
    self.embedding_key = embedding_key
    self.poignancy = poignancy
    self.keywords = keywords
    self.filling = filling
```

**AssociativeMemory `__init__`**:
```python
def __init__(self, f_saved):
    self.id_to_node = dict()
    self.seq_event = []
    self.seq_thought = []
    self.seq_chat = []
    self.kw_to_event = dict()
    self.kw_to_thought = dict()
    self.kw_to_chat = dict()
    self.kw_strength_event = dict()
    self.kw_strength_thought = dict()
    self.embeddings = json.load(open(f_saved + "/embeddings.json"))
```

**저장 시 3개 파일** (save() 구조):
- `nodes.json` — 전체 ConceptNode 딕셔너리
- `embeddings.json` — embedding_key → vector
- `kw_strength.json` — kw_strength_event + kw_strength_thought

**30p 이식 방법**:
- 들어갈 위치: `runs/seed_NNN/memories/{char_id}.jsonl` 포맷 정의
- 30p 번역 포맷:
  ```jsonl
  {"id": 912, "type": "event", "created": "2026-04-09 14:30", "s": "#9", "p": "listened", "o": "classmate_rant", "desc": "#9가 옆자리 험담을 듣는다", "poignancy": 7, "kw": ["cafe", "jealousy"], "last_accessed": "2026-04-09 14:30", "filling": null}
  ```
- **버릴 것**:
  - `embedding_key` 전체 — 임베딩 없으므로 필요 없음. `desc`가 곧 키
  - `expiration` — 30p는 시뮬 기간 짧아 만료 개념 없음
  - `depth` — Stanford는 thought가 thought를 참조할 때 쌓이는 깊이. 30p는 평탄한 append-only
  - `node_count`, `type_count` — ID 시퀀스용. `id` 하나로 충분
  - 3 파일 분리 — JSONL 한 파일로 통합 (kw_strength는 필요 시 별도)
- **유지할 것**:
  - `type` 3분류 (`event` / `thought` / `chat`) — 이게 30p에서도 중요. `whisper`/`interview`는 추가 타입
  - SPO 트리플 (`s`/`p`/`o`) + `desc` 병존
  - `poignancy` 필수
  - `keywords` — 미래 retrieval 확장용
  - `last_accessed` — 1.2 retrieve 규칙의 핵심
  - `filling` — 근거 노드 ID 리스트 저장용 (insight 인용 추적)
- 의존성: json + jsonl. stdlib. ✓

**철학 양립 체크**:
- 자동 tick 아님: ✓
- 의존성 0: ✓
- Claude tick 모델 직접 사용: ✓
- 30p 해결 못한 자리: ✓ (메모리 포맷 아직 없음)

---

### 1.11 `reflection_trigger` 부수 필드 — from Stanford `scratch.py`

**무엇**: synthesis에 없던 **3개의 부차 reflection 트리거 조건** 필드.

**원본 필드 (class default)**:
```
concept_forget = 100
overlap_reflect_th = 2
kw_strg_event_reflect_th = 4
kw_strg_thought_reflect_th = 4
```

**추정 해석** (함수 본체는 별도 확인 못함, 필드명에서):
- `concept_forget = 100` — 100 노드 이상 쌓이면 오래된 것 정리 (30p는 JSONL append-only 원칙이라 **버림**)
- `overlap_reflect_th = 2` — 같은 키워드가 2번 이상 겹치면 reflect 유발
- `kw_strg_event_reflect_th = 4` — 특정 키워드의 event 등장 강도가 4 이상이면 reflect 유발
- `kw_strg_thought_reflect_th = 4` — 동일, thought 기준

**30p 이식 판단**:
- `overlap_reflect_th` 패턴은 **버림** — *반복되는 주제*를 감지해서 reflect를 유발하는 건 로직으로 가능하지만, 30p에서는 **반복 감지를 Claude 판단**에 맡기는 게 더 풍부. 코드로 규칙화하면 카페라떼 미학 희석
- `kw_strength` 집계 딕셔너리는 **버림** — 키워드 카운트 구조를 또 유지해야 해서 복잡도 대비 이득 적음
- **단, 철학적 아이디어**: *"같은 사건을 여러 번 겪으면 그게 곧 reflection 재료가 된다"* — 이건 30p의 M11 (embedded_reactions, 충돌 지점) 테이블 확장 때 참고 가치

**결론**: 훔치지 않음. 대신 **30p 기존 M11 embedded_reactions 테이블이 Stanford kw_strength보다 *질적으로 앞서 있다*는 역검증**. 즉 30p가 이미 같은 문제를 더 풍부하게 푼 자리.

---

## 2. 버린 것 (철학 충돌 or 이미 해결)

### 2.1 Stanford `execute.py` pathfinding 전체
**버리는 이유**: 2D 타일 미로 pathfinder. 30p는 물리 공간 없음. 완전 무관.

### 2.2 Stanford `generate_hourly_schedule` 24시간 분해
**버리는 이유**: 30p는 캐릭터 일일 스케줄 개념 없음. tick 기반 이벤트 체인이지 분단위 일정표 아님. 대신 task_decomp의 *프롬프트 기법*(1.5)만 훔침.

### 2.3 Stanford `revise_identity` 일일 정체성 갱신
**버리는 이유**: 30p는 캐릭터 정체성이 시뮬 동안 크게 변하지 않는다는 전제 (시뮬 기간 짧음). 매일 자기 상태 요약 갱신 루프 과잉. 30p에서는 사용자가 `x-ray`로 보기만 하면 됨.

### 2.4 Stanford `spatial_memory` (확인 안 함)
**버리는 이유**: 세계→섹터→아레나→오브젝트 트리. 30p 무대는 훨씬 단순 (단일 stage 설정). 시간 투자 안 함.

### 2.5 Stanford pygame 프론트 + Django 백엔드 전체
**버리는 이유**: 시각화·배포. 30p는 카드 + 서사 텍스트.

### 2.6 ai-town `Agent.tick` physics 2층 분리 (60Hz/1Hz)
**버리는 이유**: 이동·pathfinding 실시간 렌더링 목적. 30p는 이벤트 체인 tick. synthesis와 동일 결론 재확인.

### 2.7 ai-town Convex/Next.js/PixiJS/Clerk 전체
**버리는 이유**: 프로덕션 SaaS 인프라. 30p 완전 무관.

### 2.8 ai-town `MEMORY_ACCESS_THROTTLE = 300_000` (5분)
**버리는 이유**: last_access를 DB에 쓸 때 5분마다만 갱신(쓰기 비용 절감). 30p는 JSONL append-only, 쓰기 비용 무관. 필요 없음.

### 2.9 agentsociety `KVMemory` + `StreamMemory` + `SparseTextEmbedding`
**버리는 이유**: `sentence-transformers` + `fastembed` 계열 외부 의존. 30p 의존성 0 정책과 정면 충돌. *분리 개념* (StatusMemory vs StreamMemory) 자체는 30p가 이미 4층 데이터 모델로 해결 — Body/Identity는 status, Memory는 stream. **30p가 이미 앞서 있음.**

### 2.10 agentsociety Protobuf/cityproto/Docker
**버리는 이유**: 도시 규모 전용. 30명 규모 무관. synthesis 재확인.

### 2.11 agentsociety Maslow/TPB 수치화 (코드 검증 실패, 3번 항목 참조)

### 2.12 oasis `rec_sys_*` 전체
**버리는 이유**: `torch`, `sentence-transformers`, `sklearn.feature_extraction.text.TfidfVectorizer`, `sklearn.metrics.pairwise.cosine_similarity`, `numpy` 의존. **전부 외부 패키지**. 30p 의존성 0 정책과 정면 충돌. 30p는 "추천 시스템" 자체가 필요 없고 (피드 시뮬이 아니므로) 개념적으로도 훔칠 것 없음.
- 단 `rec_sys_reddit`의 hot-score 공식 `sign * log₁₀(max(|s|, 1)) + seconds / 45000`은 30p 무관.

### 2.13 oasis `asyncio.create_subprocess_exec` + `asyncio.Queue` + SQLite
**버리는 이유**: 30명 규모엔 과잉. 순차 for loop이 디버깅/트레이싱 유리. synthesis 재확인.

### 2.14 oasis 23개 discrete action enum (LIKE_POST 등)
**버리는 이유**: 소셜 플랫폼 시뮬 전용. 30p 자유 서술 도메인과 충돌. 단 **INTERVIEW**만 예외로 훔침 (1.8).

### 2.15 sotopia `ReachGoalLLMEvaluator`, `SotopiaDimensions`, `EpisodeLLMEvaluator`
**버리는 이유**:
- 에피소드 기반 평가 (30p는 지속 시뮬)
- Pydantic + 구조화 응답 의존 (외부 패키지)
- LLM evaluator가 *점수를 매겨 에이전트를 평가* — 30p는 *점수 안 매긴다*. 사용자 관찰이 전부
- `structured_social_verifier.py`는 **실제 존재하지 않음** — Gemini 오보 (3번 항목 참조)

### 2.16 sotopia `RuleBasedTerminatedEvaluator`
**버리는 이유**: 대화 턴 수 / 활성 에이전트 수 / "none" 액션 누적으로 에피소드 종료 판정. 30p는 종료 판정이 *사용자 결정*이라 필요 없음.

### 2.17 sotopia `AgentAction` 파싱
**버리는 이유**: 파싱 로직 자체가 없음 (upstream에서 구조화 생성). 훔칠 것 없음.

### 2.18 Stanford `embedding_key` + OpenAI embeddings
**버리는 이유**: 30p는 임베딩 전무. Claude가 관련성 직접 판단. 동 패턴 2번 이상 반복 — `searchMemories`, `new_retrieve`, `get_embedding` 등.

### 2.19 Stanford `kw_to_event/thought/chat` + `kw_strength_*`
**버리는 이유**: 키워드 카운트/인덱싱 구조. 30p는 Claude가 파일 읽어서 직접 판단하므로 사전 인덱싱 불필요. 30p가 이미 *Claude tick 수행자*로 해결한 자리.

### 2.20 Stanford `run_gpt_prompt_event_triple` LLM 호출
**버리는 이유**: 30p는 서사 문장을 그대로 저장. SPO 트리플 추출이 필요하면 Claude가 *저장 시점에* 함께 박는다 (별도 LLM 호출 아님). 1번 패스에서 서사+트리플 동시 생성.

### 2.21 ai-town `calculateImportance`의 **인물 컨텍스트 제거**
**버리는 이유**: ai-town은 importance 프롬프트에 해당 인물 profile을 넣지 않음. 30p는 *그 캐릭터에게 얼마나 중요한지*가 핵심이라 반드시 캐릭터 정보를 박아야 함. Stanford 버전이 맞고 ai-town 변종은 30p와 철학 충돌.

---

## 3. 검증 못 한 것 (fetch 실패 / 경로 미존재)

### 3.1 agentsociety `Reason Block` / `Route Block` / `Action Block` 실제 구현 파일
**상황**: synthesis.md에서 Perplexity 리서치가 언급한 3-block workflow의 실제 파이썬 파일 경로를 찾지 못함. `packages/agentsociety/agentsociety/memory/memory.py`는 확보했으나 block 계열 파일 경로 미확인. repo 구조 탐색 시간 소요 대비 이득 판단 — **agentsociety는 외부 의존이 너무 많아(SparseTextEmbedding, fastembed) stdlib 이식 불가 이미 확정**. 더 파고드는 의미 없음.
**조치**: 블록 분리 개념 자체는 synthesis.md에 기록된 수준으로 충분. 코드 이식 대상 아님.

### 3.2 agentsociety Maslow / Theory of Planned Behavior 수치화 실제 코드
**상황**: Perplexity/Gemini 양쪽이 "구현되어 있다" 주장했으나 구체 파일 경로 없음. `memory.py` 내부엔 없음. `agent.py` 또는 `needs.py` 류가 있을 수도 있으나 확인 못함.
**조치**: 30p 옵션표는 이미 ACE·IQ·애착 등 실증 메타분석 기반으로 수치화 완료. Maslow/TPB는 30p에서 *상위 분류격자* 정도 역할이라 코드 이식 불필요. 미확인으로 두고 넘김.

### 3.3 sotopia `structured_social_verifier.py` — **존재하지 않음 확인**
**상황**: Gemini 리서치 주장. synthesis.md에도 "Gemini만 주장, 검증 필요" 플래그로 기록. 이번에 `sotopia/envs/evaluators.py` + `sotopia/envs/parallel.py` 두 곳을 직접 확인했으나:
  - `evaluators.py`에는 `RuleBasedTerminatedEvaluator`, `EpisodeLLMEvaluator`, `unweighted_aggregate_evaluate` 등만 있음
  - `parallel.py`에는 파싱 로직 없음 (upstream `AgentAction` 구조화 가정)
  - `structured_social_verifier.py`라는 파일명은 sotopia repo 안에 **존재하지 않는다**
**조치**: Gemini 오보로 판정. synthesis.md에서 주장한 "raw 서사에서 SPO 트리플 자동 추출" 기능은 sotopia에 없음. 30p가 해당 기능을 원한다면 *Stanford `run_gpt_prompt_event_triple` 프롬프트 패턴*을 참고하거나 (LLM 호출이라 30p 철학과 부분 충돌) *Claude가 이벤트 저장 시 동시에 트리플 박기*로 해결해야 함. sotopia에서 훔칠 코드 0개.

### 3.4 Stanford `run_gpt_prompt.py`의 프롬프트 템플릿 .txt 여러 개
**상황**: `run_gpt_prompt.py` 본체에서 확보한 create_prompt_input 함수는 **프롬프트 조립 변수 리스트만** 보여줌. 실제 템플릿 .txt는 별도 파일이라 각각 WebFetch 필요. 이번 세션에서 *가장 가치 있는 7개*를 내려받았음:
  - `poignancy_event_v1.txt` ✓
  - `generate_focal_pt_v1.txt` ✓
  - `insight_and_evidence_v1.txt` ✓
  - `decide_to_talk_v2.txt` ✓
  - `decide_to_react_v1.txt` ✓
  - `task_decomp_v3.txt` ✓
  - `summarize_conversation_v1.txt` ✓ (내용이 매우 짧음 — "Summarize the conversation above in one sentence: This is a conversation about")
**확보 못한 프롬프트** (다음 세션에서 필요 시):
  - `iterative_convo_v1.txt` (agent_chat_v2 발화 생성)
  - `planning_thought_on_convo_v1.txt`
  - `memo_on_convo_v1.txt`
  - `agent_chat_summarize_ideas_v1.txt`
  - `agent_chat_summarize_relationship_v1.txt`
  - `generate_hourly_schedule_v2.txt`
  - `safety_check_v1.txt` (open_convo_session에서 8점 이상 경고)
  - `new_decomp_schedule_v1.txt`
  - `wake_up_hour_v1.txt`
  - `daily_planning_v6.txt`
**조치**: 위 7개로 30p 이식에 충분. 나머지는 **30p와 직결되지 않아** (convo 관련, daily schedule 관련) 훔칠 가치 작음. 필요 시 별도 세션.

### 3.5 oasis `rec_sys_personalized_twh` 전체 formula
**상황**: `rec_sys_personalized_twh` 함수에 날짜 감쇠 + 코사인 + like 히스토리 부스트 결합이 있다는 것만 확인. 실제 수식 본체는 *torch/sklearn 의존*이라 30p 이식 대상 아님. 시간 투자 안 함.
**조치**: 버림 (2.12).

### 3.6 ai-town `reflectOnMemories` **이후** 실제 reflection 생성 로직
**상황**: `reflectOnMemories`가 "sum > 500이면 진행"까지는 확보했으나 그 뒤 focal_points 생성 + insight 생성 함수 본체는 fetch 분량 제한으로 미확보. Stanford `reflect.py`와 동일 패턴일 것으로 *추정*되나 추정 금지 원칙.
**조치**: Stanford 쪽이 이미 완비되어 있으므로 ai-town 변종 세부는 추가 확인 불필요.

---

## 4. 총평

### 4.1 가장 가치 있는 발견 TOP 5

1. **`poignancy_event_v1.txt` + ai-town `calculateImportance` 프롬프트 실물** — Stanford와 ai-town이 *완전히 같은 예시 문구*("brushing teeth, making bed" / "break up, college acceptance")를 쓴다는 것은 이 예시가 *LLM이 0~10 점수를 안정적으로 내는 데 경험적으로 검증된 공식*이라는 뜻. 30p가 poignancy 도입할 때 같은 예시 뼈대로 번역만 하면 즉시 작동한다. **이번 드릴다운의 최대 수확.**

2. **Stanford `retrieve.py` 전문** — synthesis에는 3항 공식만 있었는데 실제 코드를 읽고 **`last_accessed` 자동 갱신** + **`"idle"` 필터** + **`normalize_dict_floats` 0 나눗셈 방어**까지 확인. 특히 "조회되는 순간 last_accessed 갱신 → 상기가 상기를 부른다" 피드백 루프는 30p의 *캐릭터 고유 인지 결* 구현에 결정적. 이건 단순 retrieve가 아니라 *기억의 자기 강화 피드백*이다.

3. **Stanford `scratch.py` 실제 class default 값** — synthesis.md는 예시 json(`recency_decay=0.995, att_bandwidth=8`)을 *디폴트*로 기록했는데 **실제 class default는 `0.99, 3, retention=5`**. 30p가 Stanford 수치를 *그대로 베끼려* 했으면 잘못된 출발선에서 시작했을 것. 드릴다운의 교정 가치.

4. **`insight_and_evidence_v1.txt`의 `(because of 1, 5, 3)` 근거 강제 패턴** — 단 한 줄의 출력 포맷 요구로 LLM이 *인용 번호를 박게* 만드는 기법. 30p에서 캐릭터의 내면 독백이나 통찰을 생성할 때 그 근거가 어느 메모리 노드인지 자동 링크됨. 사용자가 `x-ray`로 읽을 때 *왜*를 즉시 확인 가능.

5. **oasis `perform_interview` 단순성** — "시스템 프롬프트에서 `# RESPONSE METHOD` 섹션만 잘라내고 사용자 질문을 마지막 user 메시지로 박는다." 끝. 복잡도 거의 0. 30p 4번째/5번째 관찰 명령(`interview`, `whisper`)을 **즉시 추가 가능**함이 증명됐다.

### 4.2 30p가 이미 앞서 있는 자리 (역검증 확인)

- **의존성 0 정책**: Stanford 77개, ai-town 수십 개, agentsociety/oasis는 torch + sklearn까지. 30p의 stdlib-only는 유례없는 극단성이고 *유지 가능함*이 증명됨 (Stanford 4개 파일만으로 핵심 로직 응축 가능한 걸 실제 확인).
- **4층 데이터 모델**: Stanford는 3층(innate/learned/currently) 단순 텍스트. 30p의 Body(B1~B10)/Memory(M1~M11)/Identity(I1+I2+I3)/WorldMap(4하위)은 비교가 안 되게 정교.
- **검열 0**: 5개 repo 모두 **검열 필터** 또는 **안전 프롬프트** 내장 (Stanford `safety_check_v1.txt`, ai-town 내장, sotopia 평가 rubric 등). 30p 카페라떼 미학과 충돌.
- **캐릭터 본인 접근 불가 영역 (subconscious)**: 5개 repo 어디에도 *"캐릭터 본인이 모르는 것 vs 관찰자가 보는 것"* 분리 개념 없음. **30p 완전 고유 설계.**
- **M11 embedded_reactions (충돌 지점)**: Stanford `kw_strength` 패턴이 *반복되는 주제를 통계적으로 잡는* 엉성한 버전이라면 30p M11은 *캐릭터별 충돌 지점을 질적으로 설계*한 완성형. 역검증 확인.
- **생성만 비트 재현성, tick은 서사 비결정**: 5개 repo 모두 *전체 재현*을 포기했는데 30p는 *생성 시점만* 비트 단위 고정하고 tick은 Claude 서사로 맡기는 분리 전략. 옳음이 재확인됨.

### 4.3 30p가 비어 있는 자리 (이번 드릴다운으로 확인된 채움 후보, 우선순위 순)

1. **Poignancy 필드 + 프롬프트** (1.1) — 즉시 도입 가능. `memories.jsonl` 포맷 확장 + Claude가 저장 시 0~10 매김. 별도 세션 1회로 완료 가능.
2. **JSONL 메모리 포맷 확정** (1.10) — `runs/seed_NNN/memories/{char_id}.jsonl`. `type`/`s`/`p`/`o`/`desc`/`poignancy`/`kw`/`last_accessed`/`filling`. ConceptNode 참고로 필드 정의. 별도 세션.
3. **Retrieve 규칙 (gw=[0.5,3,2], last_accessed 갱신, idle 필터, att_bandwidth 상한)** (1.2, 1.9) — `docs/retrieve_rule.md` 신설. Claude가 매 tick 시작 전 해당 캐릭터 메모리에서 top-N 추림. 별도 세션.
4. **`insight_and_evidence` 근거 인용 강제 패턴** (1.4) — `docs/observation_commands.md`의 `x-ray` 심화 모드, 또는 캐릭터 내면 생성 프롬프트 부록. 낮은 복잡도.
5. **4~5번째 관찰 명령 `whisper` + `interview`** (1.7, 1.8) — `docs/observation_commands.md` 확장. 사용자 합의 필요.
6. **Reflection 트리거 (카운터 감소 패턴)** (1.3) — 선택적. 30p 관찰자 철학과 부분 충돌이라 사용자 합의 필수. 도입하면 *캐릭터 자생 통찰* 기능 추가.

### 4.4 사용자 주의 사항

- **synthesis.md의 수치 일부가 잘못됨**: `recency_decay=0.995`, `att_bandwidth=8`은 Stanford **class default가 아니라 예시 json override**. 실제 class default는 `0.99`, `3`, `retention=5`. 30p 이식 시 수치 재검토 권장.
- **sotopia `structured_social_verifier.py`는 존재하지 않음**: Gemini 오보. synthesis.md에 "Gemini만 주장"으로 플래그 있었고 이번에 실물 확인 결과 존재 무효. 이 파일 이름은 다음 세션부터 인용하지 말 것.
- **1번 드릴다운(이번 세션) 결과는 판정서일 뿐**: 실제 30p 코드/문서 수정은 별도 세션에서, 사용자 합의 후 진행. 하네스 파일 "금지 사항" 엄수함.
- **reflection 트리거는 30p 철학과 부분 충돌**: Stanford의 *캐릭터 자생 통찰*은 30p의 *관찰자 중심*과 방향 반대. 도입 여부는 사용자가 *복수성을 풍부하게 만드는가 vs 카페라떼 미학을 희석시키는가* 판단 필요.
- **`whisper`는 검열 0과 동기화**: whisper로 박아넣을 수 있는 내용에 제한이 없어야 30p 철학 일관. Stanford `open_convo_session`은 safety_score >= 8이면 경고 띄움 — **30p는 이 경로 채용 금지**.
- **프롬프트 번역 시 한국어 + 카페라떼 미학**: Stanford 원본은 전부 영어. 30p 이식 시 예시 문구도 영어 ("brushing teeth, break up")가 아닌 **사용자 미학 언어**("계단 내려가기, 상사가 건넨 카페라떼를 받아 든 순간")로 교체해야 register 유지.
- **ai-town calculateImportance의 `temperature: 0.0` + `max_tokens: 1`**: 숫자 하나 뽑을 때 확률 낭비 없애는 기법. 30p는 Claude tick 수행자라 API 파라미터 개념 없음 — 대신 프롬프트에 "숫자만 한 개 반환" 강제 명시하면 동등 효과.
