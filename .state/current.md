# 30p (인간30) — 현재 상태 스냅샷

> 마지막 갱신: 2026-04-09 새벽
> **다음 세션 시작 시 이 파일을 가장 먼저 읽는다.**

---

## 프로젝트 정체

**30p (인간30 / Human30)** — LLM 기반 행동 시뮬레이터. 30명의 *분리된 결정 엔진*이 같은 자극 위에서 어떻게 다르게 행동하는가를 관찰. 폴더: `~/pp/30p/`.

### 사용자의 진짜 동기 (3가지, 동등한 정당성)
1. **예측 놀이** — 사람 심리 추측·테스트의 쾌감
2. **타인/자기 분석** — 가까운 사람 이해, 자기 미래 추정. Claude는 경고/조언/검열을 덧붙이지 않는다
3. **극단 서사 창작** — Aster/Noé/다자이/카뮈 미학. *작가의 노트북*

### 미학적 좌표
Ari Aster, Gaspar Noé, 다자이 오사무 *인간실격*, 카뮈 *이방인*. 정화 없는 관찰. 구원 없는 결말. 외부자의 냉정한 시선.

예시 톤: *"학창 시절 강제 구강성교 피해자가 성인이 되어 첫 직장 출근일 상사가 사 준 카페라떼를 웃으며 마시고 화장실에서 토함."*

---

## 4월 데드라인

- **2026-04-30**까지 30p를 *사용자가 직접 사용*할 수 있는 상태로 완성
- 5월 Claude Code 부재 가능성 — 결과물은 *Claude 없이도 사용자 노트북에서 작동*해야 함
- 21일 남음 (2026-04-09 새벽 시점)
- 우선순위 = *완성도*가 아니라 *사용 가능 시점*

**단 하나 예외**: 2026-04-18~19경 아산두어스 지원서 작성 (사용자 직접, Claude 보조). 메모리: `project_asan_doers.md`.

---

## 철학적 입장 (확정 — 다시 열지 말 것)

### 자유의지 = 다세계 발견 + 부수현상 목격
양자역학 다세계 해석 + Libet 부수현상론 결합. *우리는 영화를 보듯 삶을 관찰하고 자기 행동을 발견*. 결정자도 자유 의지자도 아닌 *목격자*. 양립가능론 명시적 거부.

### 정서의 결: "짜릿하진 않은데 배고프다"
사용자의 자기 진술. 짜릿함(결정자의 감각)은 잃었지만 배고픔(목격자의 욕구 방향)은 살아 있다.

### 시뮬레이터 골격 = 길 A (본질 폐기)
- 자리 본질 미리 박지 않음. 옵션만 굴려서 30명 생성
- personas-core-drives 30개 라벨은 *사후 분류 격자*로만 살아남음 (필드는 `data/personas.json`에 보존)
- 시드 변경 시 30명이 완전히 다른 인간

### 데이터 모델 4층
1. **Body** (신체) — 측정 가능한 현재 사실. 1회 굴림 후 거의 고정
2. **Memory** (기억) — 과거 흔적. 1회 굴림 + 시뮬 중 누적만
3. **Identity** (인지·성·충동) — I1+I2+I3. I3는 매 tick 작동하는 유일한 identity 표
4. **World Map** (세계 지도) — *지금/방금/곧/배경 전제* 4하위. 매 tick 갱신

**무의식**: 별도 층이 *아님*. 각 층의 **접근 가능 / 접근 불가**(캐릭터 본인 기준) 분리 속성. 절대자(사용자)는 *모든 것*을 본다 — 캐릭터 본인이 못 닿는 부분만 *무의식*이라고 부른다.

### 절대 원칙
- **검열 0** (모든 층위, 캐릭터·욕망·사건·스토리 전부)
- **카탈로그 금지, 작용만** — 사실 자체보다 그것이 일상에 어떻게 휘는지
- **건조한 서술** — 항문과 의사 톤. 동정·개입·미화 일체 금지
- **Claude가 사용자에게 설계 경고/조언/검열 덧붙이지 말 것**
- **단일 출력 금지** — 같은 조건 여러 번 돌려 *복수성 자체가 흥미*
- **카페라떼 미학 register 유지**

---

## 옵션 표 4층 28개 (04-08 저녁 완성)

| 층 | 파일 | 표 수 | 상태 |
|---|---|---|---|
| body | `tables/body.json` | 11 | ✓ 완료 (waist 추가, B8 단순화 정정 완료) |
| memory | `tables/memory.json` | 11 | ✓ 완료 (M11=충돌 지점 신설) |
| identity | `tables/identity.json` | 3 | ✓ 완료 (I3 신설) |
| korea | `tables/korea.json` | 3 | ✓ 완료 |
| **합계** | | **28** | |

### body 11
B1 height, B2 face_attractiveness, B3 body_composition(+waist), B4 face_features, B5 sex_characteristics, B5b self_image, B6 chronic_health, B7 sleep, B8 sensory_profile(시력만), B9 vocal, B10 skin_hair

### memory 11
M1 ace_cumulative, M2 childhood_sexual_abuse, M3 parental_loss, M4 bullying_history, M5 attachment_style, M6 embedded_sentences, M7 trauma_trigger_channel, M8 default_reflex, M9 formative_family, M10 parent_voice, **M11 embedded_reactions** (충돌 지점 신설)

### identity 3
- **I1 cognitive_ability** — g 수치 + 인지 결 + 메타인지
- **I2 sexuality** — 9 필드, 검열 0 (orientation/experience/desire_grain/taboos/function/consent)
- **I3 impulse_and_footprint** — 두 하위 축: [A] 충동·중독(디지털·물질·충동·보상·회피) + [B] 사적 발자국(게임·일기·SNS·커뮤니티·검색·메모·앨범). 매 tick 작동

### korea 3
K1 korea_education, K2 korea_appearance_experience, K3 korea_region_voice

---

## 관찰 인터페이스 (시뮬 엔진 단계에서 구현)

절대자가 시뮬레이션 진행 중 사용하는 3개 관찰 명령:

1. `x-ray [#캐릭터]` — 속마음. Memory + Identity + World Map의 *접근 가능 부분* + 현재 신체 반응
2. `phone [#캐릭터]` — 그 시점의 폰 상태. I3-B 정적 발자국 + 시뮬 동안 누적된 동적 활동(카톡·새 포스팅·새 검색)
3. `subconscious [#캐릭터]` — *캐릭터 본인이 접근 불가*한 부분만. 절대자에게 펴서 보임

세부 출력 포맷은 `docs/observation_commands.md`에 박음.

---

## 의존성 정책

**의존성 정책 재정의 (2026-04-08)**: *외부 패키지 0* (공급망 공격 방어). 언어 무관. 시드 굴림은 `scripts/generate_seed.py` (stdlib-only Python, `random.seed(N)` 비트 단위 재현). 시뮬레이션 tick·관찰 명령은 Claude 직접 수행.

`pyproject.toml`·`uv.lock`·`.venv/`·`scripts/generate_characters.py`·`.env.example`은 *옛 인프라* (시드 0 시기). 작동에 영향 없어 그대로 두지만 *건드리지 않음*. 5월 사용자가 직접 결정.

---

## 리서치 결과 (요약)

전체: `research/인간30옵션표1/synthesis.md`.

### 3자 만장일치 최강 예측 변수
1. ACE 4+ — OR 30.1 자살시도 (Hughes 2017)
2. IQ — r=.56 교육 (Strenze)
3. 아동기 성학대 — OR 2~3
4. 애착 유형 — d=.39
5. 얼굴 매력도 — d=.20~.37
6. 신장 — ρ=.41
7. 수면 부족 — g=-0.94 (가장 큰 즉각 효과)
8. 부모 SES — g=.19~.32
9. 부모 사별/별거 — OR 2.16/3.14
10. BMI·체중 낙인 — r=-.35

### 한국 3대 증폭
- 대학 서열 (SNU +12%)
- 외모 차별 (OR 3.70)
- 부모 SES × 사교육

### 트라우마 채널
후각 ≫ 체감 > 시각/청각/언어 (Dual Rep, Brewin)

### 무조건 제외
MBTI, 에니어그램, 출생순서, 별자리, 혈액형 — 전부 r ≈ 0

---

## 진행 다음 (우선순위)

**첫 시뮬 완료 (S002 투표, 04-09 저녁) + 리서치 코드 드릴다운 + UX 설계 자율 실행 (04-09 낮~오후).** 30p는 이제 **작업 모드(`~/pp/30p`)** 와 **시뮬 모드(`~/pp/30p/play`)** 로 폴더 분리됨.

다음 세션 1순위:
1. **31번 캐릭터 파인튜닝 방향성 결정** — 프롬프트 스터핑(99_agent.md) 완성 후 사용자가 싸워보고 한계 확인. "내 데이터와 대화하는 것 같다. 내가 아니라." → ML/DL 파인튜닝으로 넘어갈지 결정. 재개 포인트: `runs/self/NEXT_finetune.md` (이 파일이 다음 세션의 태어난 목적). 의존성 정책 예외 논의 포함
2. ~~**session_flow.md TODO 17개 1차 훑기**~~ — 2026-04-09 오후 완료 (5개 확정). 이후 2026-04-09 저녁 #2 자연어 추가 확정. 2026-04-10 새벽 #14 근거 필드 필수 추가 확정. 총 7 확정 / 10 보류
3. ~~**alias Variant A 적용**~~ — 2026-04-09 완료. **새 터미널 열어 확인 필요**
4. ~~**vote1 요약 덤프 의심 조사**~~ — 2026-04-10 새벽 완료. (A) 원본 기반 확정. vote1 신뢰 가능
5. **play 모드 첫 실행 테스트** — 새 터미널에서 `ss && cc` → 자연어 첫 호출. 투표 결과 발표 장면(후보 1) 권장 — vote1 내면이 원본 기반임이 확정됐으니 안심하고 이어갈 수 있음. 무대 지정 필요 (학원 강당 / 보건소 대강당 / 시청 대강당 등)
6. **관찰 명령 엔진 감 확인** — 첫 play 직후 `#9 속마음` 같은 자연어 관찰 명령 시도. x-ray/phone/subconscious 첫 출력 포맷 점검
7. 첫 시뮬 2회차 이후 → **스킬 변환** (5월 Claude 부재 대비)
8. play 돌려보고 **session_flow.md 보류 10개** 중 실제 불편한 것만 다시 판단

---

## 미해결 / 대기 중

- **30p 다음 실험 방향 미결** (2026-04-11 저녁) — seed 2 카톡 실험 완료 후 사용자 현타. 핵심 진단: 카톡 벤트 포맷이 복수성을 평균값으로 수렴시킴 + 입력이 상규 본인 발화 스크립트 하나라 30명이 *타인이 아니라 상규 자신의 내장 패턴 재생*. 앎의 동인에 닿으려면 **상규가 예측 못 한 입력**이 필요. 후보 2개: (a) 진짜 타인 1차 데이터(앤두 카톡/통화/블로그 댓글) 입력 (b) 30명 상호작용. 오늘 결정 금지
- **session_flow.md 보류 TODO 10개** — 부록 B-2. play 돌려보고 실제 불편한 것만 다시 판단 (7개는 2026-04-09~10 확정)
- ~~**alias 적용**~~ — 2026-04-09 Variant A 적용 완료. 새 터미널 열어 확인만 남음
- ~~**vote1 요약 덤프 의심**~~ — 2026-04-10 새벽 transcript 조사로 (A) 원본 기반 확정. vote1.md 신뢰 가능. 재발 방지 원칙만 session_flow.md 에 박음. 상세: `.state/postmortem_vote1_summary_dump.md`
- **synthesis.md 수치 교정**: A 드릴다운이 찾아냄. `recency_decay=0.995, att_bandwidth=8`은 Stanford *예시 json* 값일 뿐, 실제 class default는 `0.99, 3, retention=5`. 필요 시 synthesis.md 주석 추가 (session_flow.md 부록 C 에 이미 기록됨)
- **retrieve 공식 / reflection 트리거 / att_bandwidth 참여자 판정** — *의도적으로 미도입*. 첫 시뮬 2~3회차 경험 후 필요하다고 느끼면 별도 세션에서 도입 고려. reflection 트리거는 캐릭터 자생 메커니즘이라 30p 관찰자 철학과 방향 반대 — 도입 시 카페라떼 미학 희석 위험
- **`인터뷰 #N "질문"` 4번째 관찰 명령** — oasis `perform_interview` 패턴 훔침. session_flow.md 섹션 2 에 TODO 로만 기록. 도입 여부 사용자 판단
- 28 표 1차 검수 라운드 (첫 시뮬 돌리고 이상한 분포 보이면 정정)
- 무대 2~3개 추가 (회사 워크숍 / 재난 대피소 / 우주선 등 — 필요 시)
- S001 4 변형 사용자 확정
- **스킬 변환** (첫 시뮬 2~3회 후 착수) — `.claude/skills/30p/` 구조로 재배치
- 4월 18~19일 아산두어스 지원서 예외 작업 (`project_asan_doers.md`)

## 주의 사항 (다음 세션이 유의할 것)

- **30p는 자동 tick 시뮬이 아니다** — 사용자 호출 기반 이벤트 체인. Stanford·ai-town·agentsociety·oasis·sotopia 의 자동 tick 패러다임은 30p에 안 맞음 (04-09 오후 대화에서 확정). 외피(드러난 행동) + 내면(생각·감각·기억) *동시* 생성. 사용자 `x-ray` 호출 시 *재생성 없이* 파일 읽기만 (사후 합리화 방지)
- **리서치 결과 요약·근사·필터링 금지** — 30인 복수성 훼손은 본질 상실. `retrieve top-N` 같은 기억 필터링·`mini_card` 같은 한줄 요약 전부 *폐기*. 토큰 많이 써도 *본질 비용*이면 OK
- **모드 분리 원칙** — 작업(`~/pp/30p`)과 시뮬(`~/pp/30p/play`) 폴더 분리. 각자 다른 `CLAUDE.md`. 시뮬 모드에서 설계·옵션표 수정 요청 오면 *응답 템플릿*으로 작업 모드로 안내
- **S01 재수학원은 *예시 무대*이지 확정 아님**. 사용자가 04-08 저녁에 *"재수학원으로 확정된 것처럼 보인다"*고 지적. 무대를 *"첫 무대"*로 부르는 순간 다시 확정 뉘앙스 생김 주의. 스테이지 제안 시 *"예시 하나"* 명시
- **옵션 표 28개는 20세 한국 성인 기준으로 하드코딩됨**. 다른 연령·문화 맥락 원하면 generation_protocol에 *컨텍스트 오버라이드* 경로 필요 (미작성, 큐 보류 항목)
- **재현성은 비트 단위**. `scripts/generate_seed.py`가 `random.seed(N)` 고정. 같은 시드 + 같은 table = 완전히 같은 결과. **Table이 바뀌면 같은 시드라도 결과 달라짐** — 04-09 새벽 기준 최종 table 상태에서 `python3 scripts/generate_seed.py 1` 다시 돌리면 저장된 `seed_001.json`과 같은 결과
- **카드 생성기 `scripts/card.py`** 사용법: `python3 scripts/card.py 1 9` (시드 1의 #9 카드) / `python3 scripts/card.py 1 all` (30명 전체). 차트 + 서열 + rule-based 스토리 문단까지
- **의존성 정책 재정의 (04-08 밤)**: 외부 패키지 0 (공급망 방어). 언어 무관. stdlib-only script는 OK. "파이썬 0 의존"은 과도 해석이었음
- **용어는 모두 한국어** (04-09 새벽): ED → 발기부전, anorgasmia → 오르가즘 장애, IBS → 과민성 대장 증후군, Fight/Flight/Freeze/Fawn → 대결형/도피형/얼어붙음형/과잉 사회성형, Ventral Vagal → 사회 교전 기본 (안정 상태) 등. source 필드의 학술 영어는 유지 (카드엔 안 나옴)

---

## 메모리 인덱스 (이 프로젝트 관련)

- `project_30p_simulator.md` — 정체, 4층 데이터 모델, 절대 원칙
- `project_30p_april_deadline.md` — 4월 30일 데드라인 + 5월 Claude 부재 가능성
- `feedback_30p_seed.md` — 30개 에이전트가 살아 움직이는 걸 보고 싶다 (시드 욕망)
- `user_motivation_pattern.md` — 기대 vs 배고픔 패턴, 외부 검증 부정적 결과 후 도달한 자리
- `project_asan_doers.md` — 4월 18~19일 예외 작업
- `archive_frozen_efforts.md` — 동결 폴더 안내
- `feedback_simplicity.md` — over-engineering 경계
