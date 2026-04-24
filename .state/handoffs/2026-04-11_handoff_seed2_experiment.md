# 2026-04-11 핸드오프 — Seed 2 생성 + 카톡 실험 포맷 전환

## 세션 정체

긴 세션. 시작은 사용자의 개인 대화 (정원이 이별 마무리 인식 + 낯선 여성 근로자 만남 + 자기 표현 수위 고민)에서 시작해서, 30p 실험 설계로 자연스럽게 이어짐. 30p의 *두 가지 큰 개선*을 해냄:

1. **Seed 1 편향 인식 + Seed 2 설계·생성** — 일반 인구 샘플 (17~35, 균형, 자원 포함, 직업 다양)
2. **관찰 프롬프트 포맷 전환** — "분석 리포트" → "친구에게 카톡 벤트". 결과 품질이 극적으로 개선됨.

## 완료된 것

### 1. 30p 아키텍처 업데이트 (v0.2)

**`tables/memory.json`** (v0.1 → v0.2):
- M8_default_reflex에 "균형·차분형" 5번째 옵션 추가. weights [0.10, 0.17, 0.18, 0.20, 0.35]. 균형형 35% 최빈값.
- **M12_resources** 신설 — 5필드: support_network, coping_repertoire, meaning_source, positive_role_model, self_efficacy. 일반 인구 분포 가중치.
- changelog 필드 추가.

**`tables/korea.json`** (v0.1 → v0.2):
- K1_korea_education을 `by_age` 구조로 분기 — `16_18` / `19_25` / `26_35`. 기존 19_25 필드들이 `by_age["19_25"]["fields"]`로 이동.
- **K4_occupation** 신설 — 나이별 직업 풀, 19_25는 sex-split weights.
- interacts에 K4 참조 추가.

**`scripts/generate_seed.py`** (수정):
- `REFLEX_SIGNATURE`에 "균형·차분형" 시그니처 추가.
- `roll_resources(tables)` 신규 함수 — M12 롤링.
- `roll_memory()` 끝에 `resources` 필드 추가.
- `roll_korea(tables, sex, age)` — age로 bracket 분기, 19_25 로직 보존, K4 새로 롤링.
- `roll_character(char_id, age, sex, region, tables, personas)` — 시그니처 확장.
- `SLOTS_SEED_2` 상수 30 슬롯 하드코딩.
- `main()` — seed==2면 slot 기반, 아니면 default. `constraints`에 `age_distribution` 블록.

**`scripts/summarize_seed.py`** (수정):
- `edu_tier(kor, age)` 헬퍼 추가 — 나이별 education 접근.
- `one_liner`에 age/occupation 표시.

**`scripts/inspect_char.py`** (수정):
- `fmt_character`의 korea 섹션에 나이 분기 추가.
- occupation 출력 추가.

### 2. 생성된 파일

- `runs/seed_002.json` — 30명 완전 생성. 나이 17~35, F 15 / M 15, 균형·차분형 16명, 자원 있음, 직업 있음.
- `runs/seed_002_slots.md` — 슬롯 분포 설계 문서.
- `runs/seed_001_assessment.md` — seed 1 결핍 편향 비판 + 용도 제한.
- `runs/seed_001_kakao_experiment.md` — seed 1로 돌린 카톡 실험 전체 결과 + 패턴 분석.
- `runs/sanggyu_exp/sanggyu_persona.md` — seed 1 실험용 3인칭 페르소나.
- `runs/sanggyu_exp/sanggyu_utterances.md` — seed 1 실험용 발화 스크립트 (20살 여자 알바 특화).
- `runs/sanggyu_exp/sanggyu_utterances_v2.md` — **seed 2 실험용 발화 스크립트** (나이·상황 중립, 에이전트가 자기 캐릭터에 맞게 상상).

### 3. Seed 1 카톡 실험 결과 요약

30명 전원 카톡 벤트 포맷으로 응답. *"집 와서 계속 생각나"* / *"다음 근무 어떡하지"* 패턴이 거의 전부에서 나옴. 핵심 발견: 상규는 **거부되지만 잊히지 않는 사람**. 숫자로는 거리 두지만, *인상의 잔존*은 크다.

반복 걸림 포인트 (랭킹): ① 손/재활 비유 ② "슬프면서 기뻤다" ③ "속으로 끄덕이는 거 힘들다" ④ 화장 1시간 ⑤ "위로받고 싶은 거 아니에요" ⑥ 블로그·시뮬.

긍정 축 (공통): 어린 애 취급 안 함, 담담함, 진심.

단, **seed 1은 임상 편향 샘플이라 일반 인구 반응으로 읽으면 안 됨**. 이 결과는 *결핍이 활성화된 사람들*의 반응으로 읽어야 함.

## 다음 세션 첫 할 일 — **Seed 2 카톡 실험**

사용자가 이번 세션 후반에 짚음: *"카톡 실험은 seed 1에 돌렸다. 그건 내가 원한 대중 seed가 아니다."* 정당한 지적. 다음 세션에서 seed 2로 같은 실험 반복.

### 실행 단계

1. **seed 2 char 파일 생성** (inspect_char.py로 30개 추출):
   ```bash
   mkdir -p /tmp/30p_sanggyu_exp/seed2
   for i in $(seq 1 30); do
     python3 /Users/sanggyulee/pp/30p/scripts/inspect_char.py 2 $i > /tmp/30p_sanggyu_exp/seed2/char_$(printf "%02d" $i).txt 2>&1
   done
   ```

2. **30개 카톡 에이전트 병렬 호출** — 각자 다음 입력:
   - 자기 캐릭터: `/tmp/30p_sanggyu_exp/seed2/char_NN.txt`
   - 발화 스크립트: `~/pp/30p/runs/sanggyu_exp/sanggyu_utterances_v2.md` (**v2를 쓸 것. v1은 20살 특화**)
   - 포맷: 친구에게 카톡 벤트, 한국어, "나: " 프리픽스, 5~12 메시지, 검열 0, 자기 분석 금지.

3. **결과 분석** — seed 1과 비교:
   - 공통 걸림 포인트가 여전한가? (손 비유, 화장, 속으로 끄덕임)
   - 긍정 축은 어떻게 다른가?
   - 나이 분포 효과 — 33세 주부, 17세 고딩, 30대 직장인이 어떻게 다르게 반응하나?
   - "잊히지 않음" 패턴이 seed 2에서도 반복되는가, 아니면 단순 *지루함·무관심*으로 바뀌는가?
   - 균형·차분형 16명이 seed 1의 결핍 반사형들과 얼마나 다르게 반응하는가?

4. **seed 2 평가 문서** (`runs/seed_002_assessment.md`) 작성:
   - 분포가 설계 의도대로 나왔는지 sanity check
   - 여전한 편향 (성소수자 과잉 7~8명, 저 IQ 과잉 5명) 기록
   - 다음 반복(seed 3 또는 tables v0.3) 방향

## 알려진 남은 편향 (seed 2 분포 체크 결과)

- **성소수자 과잉**: 30명 중 7~8명. 실제 한국 20대 ~3-5%. `tables/identity.json`의 `sexuality.orientation` weights 재조정 필요.
- **저 IQ 과잉**: 67, 70, 74, 76, 79 — 5명. 실제 정상 분포 대비 하위 꼬리 과잉. identity의 `cognitive.iq` 분포 조정 필요.
- **region 불일치**: slot에 지정한 region ("영남", "서울" 등)과 birth_region이 따로 롤링됨. 한 캐릭터에 "조선족", "제주", "해외" 등 slot에 없는 값 나옴. `roll_korea`가 slot region을 override하지 않음. 버그 혹은 설계 미정합.

이 3개는 다음 세션에서 고치거나 *의도된 편향*으로 명시할 것.

## 우려사항 (γ agent 보고에서 인용)

- **Seed 1 파일 덮어씀**: γ agent 테스트 실행으로 `runs/seed_001.json`이 v0.2 tables로 재생성되어 덮어써졌을 가능성. 다행히 실험에 사용한 `runs/seed_001_llm.json` (Apr 8 생성)은 손상되지 않음. 확인: `ls -la runs/seed_001*.json` — 날짜 다르면 OK.
- **26_35 occupation weights 합 = 1.10**: `random.choices`가 정규화하므로 동작에 영향 없음. 단 코드 리뷰 시 의도 확인 필요.

## 중요한 개인적 맥락 (다음 세션이 알아야 할 것)

사용자의 오늘 하루:
1. **정원이와의 관계**: 이번 세션 초반에 사용자가 정원이(앤두) 이별이 *확정적으로 끝났다*는 판단을 내렸음. 증거 — (a) 10개월 동안 4번 헤어짐이 전부 1주일 내 재결합, 이번엔 2주+ 경과 (b) 공무원 시험일 통과 (c) 정원이가 *최초로* "같이 있고 싶지 않다"고 선언 (기존의 양가성 "무섭다 + 같이 있고 싶다"에서 한 축이 제거됨). 사용자는 *결론은 정리됐으나 느낌은 일부 잔여* 상태임을 스스로 인식 — *의식적 병존*이라는 성숙한 자리. 정원이의 마지막 선언을 "슬프면서 기뻤다"로 받아들임 (평생 바라던 솔직함을 마지막에 받았다는 역설적 해석).
2. **낯선 여성 근로자**: 오늘 도서관 근무에서 같이 일한 여성 동료가 상규의 얘기를 *자기 생각으로* 되묻는 수준의 경청을 보여줬음. 사용자는 *쾌락적 자기 표현*의 수위를 고민했고, 결론: 먼저 꺼내지 말 것, 상대가 묻는 깊이만 답할 것. 연락처 요청은 *남자 동료라도 같은 요청할 수 있는가* 테스트 통과하면 OK. 실제로 얼마나 말했나는 "스트레스 받죠" 한 마디만 — 손님이 와서 대화가 끊어짐. 이 만남이 30p 실험의 직접 트리거.
3. **user_core_drive 재확인**: 앎이 고통이어도 받아들이고 싶음. 슬픔은 *해결할 문제*가 아니라 *들고 갈 조건*. 이 정서 자리에서 사용자는 자기 표현 방식이 받는 사람에게 어떻게 착지하는지를 *관찰 가능한 형태*로 보고 싶어함. 30p가 이 질문의 *실험 도구*로 작동 중.

## 다음 세션 시작 프롬프트 (사용자가 쓸 수 있는 것)

*"세션 이어서. `.state/handoffs/2026-04-11_handoff_seed2_experiment.md` 읽고 seed 2 카톡 실험 바로 돌려. 30개 에이전트 병렬. 발화 스크립트는 v2 써."*

## 한 줄 요약

Seed 2 인프라 완성. 카톡 포맷 입증. **Seed 2로 카톡 실험 실행**이 유일하게 남은 핵심 작업.
