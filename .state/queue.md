# 30p 작업 큐

> **규칙**: 새 세션 시작 시 `.state/current.md` 읽고 → 이 큐의 1번부터 실행.
> 완료 시 [x]로 바꾸고, 새 작업은 적절한 위치에 추가.
> 4월 30일 데드라인 — 우선순위는 *사용 가능 시점*이지 *완성도* 아님.

---

## 1순위 (실행)

- [x] **Seed 2 카톡 실험 실행** (2026-04-11 저녁 완료) — 30명 에이전트 3배치 병렬 호출. 결과 `runs/seed_002_kakao/kakao_01~30.md`. 전 과정: `.state/log.md` 2026-04-11 저녁 엔트리
- [x] **30p v0.2 인프라 업데이트** (2026-04-11) — `tables/memory.json` v0.2 (균형·차분형 reflex 추가, M12_resources 신설), `tables/korea.json` v0.2 (by_age 분기, K4_occupation 신설), `scripts/generate_seed.py` 슬롯 기반 age 지원, `summarize_seed.py`/`inspect_char.py` 나이 분기 지원. `runs/seed_002.json` 30명 생성 완료
- [x] **Seed 2 평가 문서** (2026-04-11 저녁 완료) — `runs/seed_002_assessment.md` (303줄). 남은 편향 기록 + 카톡 포맷 한계 진단 + 다음 실험 방향 2개 제시
- [ ] **밤 세션 산출물 4개 읽기 + 종합** — `~/pp/ideas/2026-04-11_건강관리/02_sonnet.md`+`02_opus.md` (쌍) + `runs/self/discoveries/2026-04-11_밤세션/02_자극엔진_sonnet.md`+`02_자극엔진_opus.md` (쌍). 핵심 발산: 자극 엔진 타깃(전용 도구 vs 서비스화), 건강관리 앱 시장 경쟁, 거울 트랩 방어. 종합은 외주 금지
- [ ] **다음 실험 방향 결정** — *현타 자리에서 결정 금물*. 후보: (a) 진짜 타인 1차 데이터(앤두 카톡/통화/블로그 댓글) + 30p 해석 다양성 (b) 30명 간 상호작용 관찰. 카톡 포맷 3회차는 가치 낮음. 사용자 판단 대기. **판정 기준** (2026-04-11 밤 세션 `6df1a163`에서 추가): 나다움 공식 = *기존 나 × 새로움 = (a)×(b)*. 입력에 "상규가 예측 못 한 것"이 있는가. 원칙 출처: `runs/self/discoveries/2026-04-11_밤세션/00_원칙.md`. 후보 (a)·(b) 모두 이 판정 기준을 통과하며, 둘 중 선택 또는 조합은 냉정한 아침에. 추가 고려: 자극 엔진 설계안(`runs/self/discoveries/2026-04-11_밤세션/02_자극엔진_*.md`)이 30p 내부 실험으로 수렴하는 옵션 II를 제안할 수 있음 — 그 경우 후보 (a)의 확장 형태가 됨
- [ ] **tables/identity.json v0.3** (독립 남은 과제) — 성소수자 분포 정상화 (~5%), cognitive.iq 하위 꼬리 축소
- [ ] **region 롤링 버그 픽스** (독립 남은 과제) — `scripts/generate_seed.py`의 `roll_korea`가 slot region을 override 하도록 수정

- [x] **HARNESS_product Step 3 — MVP 구현** (04-11 새벽) — `product/analyze.py` + `product/prompt.py` + `product/run.py`. 범용 카톡 분석 + LLM 발견 생성 + 반박 루프. stdlib only. 3개 CSV 테스트 통과
- [ ] **HARNESS_product Step 4 — 테스트** — (1) `ANTHROPIC_API_KEY` 설정 후 run.py 풀 루프 테스트 (2) 이상규 카톡 재실행 → 기존 발견과 비교 (3) 다른 사람 카톡으로 실행 (4) **경쟁 감별** (2026-04-11 밤 상규 관찰 추가): GPT로 카톡 분석하는 일반 서비스(X/유튜브 바이럴, 전용 앱)와 같은 입력에서 HARNESS가 다른 출력을 내는지 확인. 환각률·반박 루프 흡수 여부·숫자 기반 해석 차이를 측정 항목에 포함. 차별점 3개 (입력 규모/장인성, Python 숫자 파싱, 반박 루프)가 실제로 시장 대비 해자 역할 하는지 판정
- [x] **시드 1 굴림** (04-08 밤 초안, 04-09 새벽 정정 5회 후 최종) — `scripts/generate_seed.py 1` → `runs/seed_001.json`. Cross-layer 5개 상관 + 영어 용어 한국어화 전부 반영
- [x] **차트 카드 생성기** (04-09 새벽) — `scripts/card.py` stdlib only, rule-based 스토리 섹션 포함. 사용: `python3 scripts/card.py 1 <id>` 또는 `all`
- [x] **시드 1 30명 훑기** — 04-09 저녁, seed_001.json 30인 요약 덤프 경유 확인. 마음에 드는 수준 (투표 시뮬로 바로 진행)
- [x] **첫 시뮬레이션 시동 (S002 의무 생식 투표)** — 04-09 저녁 완료. `runs/seed_001_S002_vote1.md` 저장. 무대 없음, 시나리오 S002 신설
- [x] **UX 설계 하네스 실행 (시뮬 모드 폴더 분리 + session_flow.md)** — 04-09 자율 실행. 산출: `play/CLAUDE.md` 신설, `30p/CLAUDE.md` 작업 모드 명시 갱신, `docs/session_flow.md` 신설 (섹션 2~9), `harnesses/alias_proposal.md` 신설(`.zshrc` 직접 수정 X). B 에이전트가 A의 `code_drilldown.md` 11개 훔친 패턴 중 poignancy 프롬프트 + att_bandwidth + load_history_via_whisper + scratch 수치 교정(`0.99, 3, 5`) 반영. 17개 `TODO(사용자 확정)` 인라인 표시 + 부록 B 일람
- [x] **session_flow.md TODO 17개 1차 훑기** (2026-04-09 오후) — 5개 확정(#1 `play` 유지, #5 att_bandwidth 미도입, #7 `x all` 허용, #13 내면 병기 유지, #15 poignancy 빼기), 12개 보류(play 돌려보고 결정). 부록 B 재구조화 + 섹션 4/5/8 인라인 마커 *확정*으로 교체 + 예시에서 `poignancy: 7` 줄 제거
- [x] **alias Variant A 적용** (2026-04-09 오후) — `~/.zshrc` 직접 수정. `pp=~/pp`, `nn=~/pp/30p`, `ss=~/pp/30p/play`. 기존 한글 경로 alias 3개 재할당. 풀림·pullim 계열 건드리지 않음. 새 터미널 필요
- [x] **session_flow.md 섹션 2 자연어 전용 재작성** (2026-04-09 저녁) — play 모드 첫 진입 직전 사용자 지적. *사용자 = 자연어만, Claude = 내부 변환*. 표 서열 뒤집기. 해석 원칙 6개 + 내부 의미 분류 표 (카드 조회 항목 신설). 부록 B #2 확정으로 이동. 한국어 우선 원칙 명시
- [x] **vote1 "요약 덤프 경유" 의심 사건 조사** (2026-04-10 새벽) — 사용자 질문 *"vote1이 모든 디테일 고려한 결과인가 요약 기반인가"*. transcript (7aa58810, 154줄 jsonl) 조사 결과 **line 120 이 58,694 토큰 거대 메시지** → 원본 seed_001.json 거의 전체(~80%)가 투표 실행 직전 컨텍스트에 있었음 확정. vote1.md 는 **원본 기반, 신뢰 가능, 재실행 불필요**. "요약 덤프 경유" 메타 표기는 부정확 기록이었음 → 정정 완료. 재발 방지 원칙 session_flow.md 섹션 4 Step 1 + 섹션 8 근거 필드 필수(부록 B #14 확정으로 이동). 상세: `.state/postmortem_vote1_summary_dump.md`
- [ ] **시뮬 결과 사용자 검증** — `seed_001_S002_vote1.md` 납득 가능성 / 억지 선택 / 예측 가능성 판단. 옵션 표 정정 근거
- [ ] **관찰 명령 엔진 감 확인** — 특정 캐릭터 x-ray / phone / subconscious 한 번씩 돌려서 3 명령 출력 포맷 점검 (엔진 감 확인은 투표로 1차 완료, 관찰 명령은 별도)
- [ ] **무대 선정** — 시뮬 2회차부터 무대 추가. S01 재수학원은 예시. 회사 워크숍·명절 모임·지하철 멈춤·평범한 하루 등에서 선택
- [ ] **S001 처형 투표 초안 검수** — 4 변형 절차 확인 (별개 시나리오, 언제든 실행 가능)

## 2순위 (스킬 변환)

- [ ] **30p를 Claude Code 스킬로 패키징** — `.claude/skills/30p/SKILL.md` + 리소스 파일들로 재구성. *5월 Claude 부재 대비*에 결정적 (다른 LLM에 이식 가능). 첫 시뮬 1회 후 실행 경로 확정되면 즉시 착수
- [ ] **스킬 호출 정의** — `/30p 시드 N 굴려`, `/30p phone #N`, `/30p x #N`, `/30p sub #N`, `/30p 시뮬 시작 (시드·무대·시나리오)`

## 3순위 (경험 누적 + 피드백)

- [ ] **2~3차 시뮬레이션** — 같은 시드 다른 변형 / 다른 시드 같은 변형 (복수성 검증)
- [ ] **옵션 표 정정 라운드** — 첫 시뮬 돌리고 빠진 영역·이상한 분포 사용자 지적 반영
- [ ] **무대 2~3개 추가** — 다양한 압력 조합 (회사 워크숍 / 재난 대피소 / 우주선 등)
- [ ] **사용 경험 정리** — *이게 사용자 삶에 영향을 주는가* 5월 결정 근거
- [x] **리서치 훑기** (2026-04-09 완료) — `research/20260409_005841_인간/raw.md` Stanford Generative Agents 등 오픈소스 참고. 실제 소스 코드 드릴다운 결과: `research/인간30에이전트2/code_drilldown.md`. 훔친 패턴 11개, 버린 패턴 21개, 검증 실패 6건. 최대 수확: poignancy 프롬프트 실물, retrieve.py 전문(last_accessed 자가강화 피드백), scratch.py 실제 default 수치(synthesis.md 수치 일부 교정)

## 4순위 (4월 19일 예외)

- [ ] **2026-04-18~19 아산두어스 지원서** — 사용자 직접 작성, Claude 보조. 30p 진척 소재 사용 가능. 메모리: `project_asan_doers.md`

## 보류 (4월 이후)

- [ ] 외부 규칙 엔진 (LLM 호출 외 결정 로직)
- [ ] Python + Textual TUI (보류 — 외부 패키지 필요하므로 의존성 정책 위반)
- [ ] KNHANES·KoWePS 실제 수치로 옵션 표 분포 교체 (현재는 디자인 추정)
- [ ] 옵션 표 연령·문화 시프트 파라미터 (20세 한국 외 컨텍스트 지원)

## 완료 (04-08 저녁까지)

- [x] **`docs/generation_protocol.md` 작성** — Claude 수행 절차, 파이썬 0 의존, 재현성은 결과물 JSON으로
- [x] **`docs/observation_commands.md` 작성** — x-ray / phone / subconscious 3 명령 출력 포맷
- [x] **`runs/README.md` 작성** — 시드별 결과물 저장 규칙
- [x] **`stages/README.md` + `stages/S01_jaesu_academy.md`** — 첫 무대 예시 (확정 아님)
- [x] **`scenarios/S001_execution_vote.md`** — 처형 투표 4 변형 초안 (사용자 검수 대기)
- [x] 루트 `~/pp/CLAUDE.md` 30p 중심 전면 재작성
- [x] 30p 내부 정비 (CLAUDE.md / current.md / queue.md / log.md / README.md / handoff mega)
- [x] 폴더 재구성: cls30 → 30p 승격, 얼린 트랙 → `~/pp/동결/` 이동
- [x] 메모리 정비 — 9 메모리 + 인덱스 새로 작성, 풀림 단어 0
- [x] body.json 정정 — 허리(waist) B3 추가 + B8 sensory_profile 단순화(시력만)
- [x] memory.json 작성 — M1~M10 + **M11 embedded_reactions 신설** (사용자 가슴 사례 기반)
- [x] identity.json 작성 — I1 cognitive_ability + I2 sexuality
- [x] korea.json 작성 — K1 education + K2 appearance + K3 region_voice
- [x] **I3 impulse_and_footprint 신설** — 두 하위 축: [A] 충동·중독 [B] 사적 디지털 발자국
- [x] 28 옵션 표 1차 박힘 (body 11 + memory 11 + identity 3 + korea 3)
- [x] 관찰 인터페이스 3 명령 정의 (x-ray/phone/subconscious)
- [x] 무의식 정의 명확화 (캐릭터 본인 접근 불가, 절대자는 항상 본다)
- [x] 폴더 재구성: cls30 → 30p 승격, 풀림 관련 동결 폴더 이동
- [x] 루트 CLAUDE.md + 30p/CLAUDE.md 재작성
- [x] 메모리 정비 — 9 메모리 + 인덱스 새로 작성

## 04-08 이전 완료

- [x] 프로젝트 정체 재정의 (cls30 → 인간30, 무대 가변·30인 본질) (04-08 아침)
- [x] 자유의지 입장 확정 (다세계 발견 + 부수현상 목격) (04-08 아침)
- [x] 데이터 모델 4층 확정 (04-08 아침)
- [x] 길 A (본질 폐기) 결정 (04-08 아침)
- [x] Claude + Gemini + Perplexity 3자 리서치 합성 (04-08 아침)
- [x] `.state/` 워크플로우 구축 (04-08 아침)
