# Handoff — 2026-04-09 새벽 (script pivot + 카드 생성기)

> 이 문서는 다음 세션 시작 시 `.state/current.md` → `queue.md` → `log.md` 다음으로 읽는다.
> 목적: 2026-04-08 밤 ~ 04-09 새벽 두 세션 동안 일어난 **구조적 전환** 을 빠르게 복원.

---

## 한 줄 요약

**30명 굴림**을 LLM 수동 → **stdlib-only Python script**로 전환.
**차트 카드 생성기** (rule-based 스토리 섹션 포함) 완성.
시드 1 최종본 준비 완료. 다음 세션은 **무대 선정 + 첫 시뮬 시동**부터.

---

## 핵심 전환 3가지

### 1. 의존성 정책 재정의 (04-08 밤)

**이전 해석**: "파이썬 0 의존" → 파이썬 기피
**정정된 원칙**: **외부 패키지 0** (공급망 공격 방어) / **언어 무관** / **stdlib만 쓰면 OK**

- 사용자 원래 동기는 공급망 공격 보고서 보고 "의존성 낮춰야겠다"고 느낀 것. 언어 자체 기피 아님
- 파이썬·Node·Deno·shell 다 가능. stdlib만 쓰면 공급망 위험 0
- LLM이 꼭 필요한 작업(서사 해석·관찰 명령·시뮬 tick)은 Claude 직접. 분포 샘플링·변환·집계는 script
- 메모리: `feedback_dependency_policy.md` 참조

### 2. 시드 굴림 script 전환 (04-08 밤 → 04-09 새벽 정정)

처음엔 LLM이 수동으로 15명 작성 시도 → 토큰 소진 + "흥미로운 조합" 편향 발견 → 사용자 지적 → 코드로 전환.

**핵심 파일**:
- `scripts/generate_seed.py` — 4층 28표 샘플링, stdlib only, `random.seed(N)` 비트 단위 재현 (약 500줄)
- `scripts/verify_seed.py` — 분포 요약
- `scripts/summarize_seed.py` — 30명 1줄 요약 + 특이 케이스 자동 탐지
- `scripts/inspect_char.py` — 특정 캐릭터 raw 필드 dump
- `scripts/check_sex_consistency.py` — 성별 교차 오류 검증
- `scripts/card.py` — **차트 카드 생성기** (아래)

**옛 `scripts/generate_characters.py`** (시드 0 시기): 건드리지 않음. 새 script는 4층 28표 기반으로 별도.

### 3. 차트 카드 + rule-based 스토리화 (04-09 새벽)

사용자 요청: *"차트 카드를 보는 것처럼. 지능·키 같은 서열화 가능한 건 서열도 해두고. 자연어로 인간군상 캐릭터를 소개. 토큰 안 들게. 안 되면 local LLM."*

답: **local LLM 불필요. 파이썬 템플릿으로 충분.**

**`scripts/card.py`**:
- 사용: `python3 scripts/card.py <seed> <id|all>`
- 섹션: 헤더 / 서열표(키·IQ·매력·ACE·BMI·악력·수면·디지털) / 신체 / 개인 병력 / 가정 배경 / 트라우마·기억 / 인지 / 성·욕망 / 충동·중독 / 사적 디지털 발자국 / 한국 맥락 / 종합 한 줄 / **스토리**
- **스토리 섹션(`render_narrative`)**: 조건부 문장 템플릿으로 한 문단 조립. 트라우마 존재 여부, 박힌 문장·반응 활성화, 위험 신호(자살 검색·자해흔 사진·부계정 운영·스토킹 검색) 자동 감지, **겉/속 격차 자동 태깅** (↑외모 rank·IQ·키·상위대 vs ↓ACE·성기능·자살 사고 등)
- 토큰 0. LLM 호출 0.

---

## 04-09 새벽 정정된 cross-layer 5개

script v0.1의 독립 샘플링이 만든 불일치를 최소한으로 해결:

### A. 성별 교차 오류 (B5b)

**문제**: 남성이 `focused_concern`에 "가슴 크기" 뽑는 버그
**해결**: `B5b.focused_concern`을 `pool_common` + `pool_M` + `pool_F` 구조로 분리. script가 sex에 따라 합쳐서 샘플.
- 남녀 공통: 얼굴·체형·키·체모·피부·목소리·체취
- 남성 only: 성기 크기, 성기 형태
- 여성 only: 가슴 크기, 성기 형태
- 여유증(남성 유방 발달 장애)은 `focused_concern`이 아니라 **B6 `chronic_health`에 `여유증 (M only)` 신설**로 처리

### B. B6 "M only" 필터 (여유증)

`B6_chronic_health.pool`에 `"여유증 (M only)": { prevalence: 0.08, severity_levels: ["경미", "중등도", "심각"] }` 추가. Script는 "F only" / "M only" 양쪽 필터 지원.

### C. ACE ↔ M2 연결

**문제**: ACE 카테고리에 "성적 학대" 포함됐는데 M2 필드는 null (독립 샘플링의 부작용)
**해결**: M2 발생 여부 먼저 결정 → ACE 카테고리 샘플링에 반영. csa_yes면 "성적 학대" 강제 포함 + total 최소 1 보장. csa_no면 "성적 학대" 배제.

### D. 수능 ↔ 대학 tier ↔ 전공 상관

**문제**: 마이스터고 + 수능 5등급 + 의예 같은 불가능 조합
**사용자 지적**: "마이스터고 자체는 문제 아니다 (정시로 의대 가는 경로 있음). 문제는 수능 등급."
**해결**:
- `TIER_ALLOWED_GRADES` 매핑 — tier별 허용 수능 등급 (SKY=1~2등급, 성균관=1~3등급, in서울=2~4등급 등)
- `MAJOR_TIER_RESTRICTION` — 의·치·약·수의는 SKY/성균관 그룹만 허용
- 로직: tier 먼저 샘플 → 허용 등급에서 재샘플 → major 샘플 후 위반이면 major 재샘플
- **고교 유형은 제약 아님** (마이스터고 정시 의대 진학 가능성 유지)

### E. SNS ↔ 부계정 충돌

**문제**: `sns_public_face="계정 없음·비공개"`인데 `private_vs_public_gap="부계정 운영"`인 모순
**해결**: "부계정 운영"이면 본계정 존재 강제 → "계정 없음" 제외하고 재샘플

### F. 지역 차별 ↔ 출생 지역 상관

**문제**: 경기·인천 출생인데 `regional_discrimination="만성 차별"` 찍히던 문제
**해결**: `HIGH_DISCRIM_REGIONS`(호남/조선족/북한 이탈/해외 재외한인), `MID_DISCRIM_REGIONS`(영남), 나머지(수도권·충청·강원·제주) 셋으로 분기. 각 분기마다 별도 가중치 적용.

---

## 04-09 새벽 영어 용어 한국어화

사용자 지적: *"언올가즘이야? 이건 뭔지 모르겠어."*

카드에 나오는 필드 값들을 전부 한국어화:

| 이전 | 이후 |
|---|---|
| 심각한 ED | 심한 발기부전 |
| 심각한 어려움 (ED·삽입통·anorgasmia) | 심각한 어려움 (발기부전·삽입통·오르가즘 장애) |
| 과민성 대장 (IBS) | 과민성 대장 증후군 |
| PPI 복용 | 위산 억제제 복용 |
| Fight (대결) / Flight (도피) / Freeze (얼어붙음) / Fawn (과잉 사회성) | 대결형 / 도피형 / 얼어붙음형 / 과잉 사회성형 |
| Ventral Vagal (사회 교전 기본) | 사회 교전 기본 (안정 상태) |
| Dorsal Vagal (만성 셧다운) | 부동화 (만성 셧다운) |

**script의 `REFLEX_SIGNATURE` dict 키도 맞춤 갱신**. 테이블 `source`/`effect_size`/`behavioral_note`의 학술 영어는 그대로 둠 (카드에 안 나옴, 학술 참조 가치 유지).

---

## 현재 파일 상태

### Script
- `scripts/generate_seed.py` ← cross-layer 5개 + REFLEX_SIGNATURE 한국어 키
- `scripts/verify_seed.py`
- `scripts/summarize_seed.py`
- `scripts/inspect_char.py`
- `scripts/check_sex_consistency.py`
- `scripts/card.py` ← narrative 섹션 포함
- `scripts/generate_characters.py` (옛 시드 0 시기 인프라, 건드리지 않음)

### Runs
- `runs/seed_001.json` — 최종본 (모든 정정 반영)
- `runs/seed_001_llm.json` — 04-08 15명 LLM 수동 버전 (비교 자료)

### Tables
- `tables/body.json` ← B5b sex-split pool, B6 여유증, 발기부전 용어
- `tables/memory.json` ← M8 반사·polyvagal 한국어화
- `tables/identity.json` ← function.performance 한국어화
- `tables/korea.json` — 변경 없음

### Docs / state / memory
- `30p/CLAUDE.md` — 의존성 정책 섹션 재작성 (04-08 밤)
- `30p/README.md` — 의존성 정책 섹션 재작성
- `30p/docs/generation_protocol.md` — 헤더·호출 형태 갱신
- `30p/.state/current.md`, `queue.md`, `log.md` — 이 세션 엔트리까지 갱신
- `~/.claude/projects/-Users-sanggyulee-pp/memory/feedback_dependency_policy.md` — 신규
- `~/.claude/projects/-Users-sanggyulee-pp/memory/project_30p_simulator.md` — 의존성 정책 섹션 재작성
- `~/.claude/projects/-Users-sanggyulee-pp/memory/MEMORY.md` — 인덱스 갱신

### Research (보류)
- `research/20260409_005841_인간/raw.md` — Stanford Generative Agents 등 오픈소스. 사용자가 "나중에 시킬 것"으로 보류

---

## 다음 세션 시작 시 순서

1. `.state/current.md` 읽기
2. `.state/queue.md` 읽기
3. `.state/log.md` 최근 3 엔트리 읽기 (04-08 아침/저녁, 04-09 새벽)
4. 이 handoff 읽기
5. 사용자 메시지 받기

다음 세션 1순위 행동:
1. `python3 scripts/card.py 1 all` (또는 특정 몇 명) — 30명 훑기
2. 시드 1 마음에 들면 → **무대 선정** (S01 재수학원 예시 / 다른 무대 제안 / 시나리오 없는 평범한 하루도 OK)
3. S001 처형 투표 4 변형 검수 선택 사항
4. **첫 시뮬 시동** — 관찰 명령 `x-ray`/`phone`/`subconscious` 한 번씩

시뮬 *자체*는 Claude가 직접 수행(LLM 필요). Script는 준비 재료만.

---

## 주의 사항

- **S01 재수학원은 예시**. "첫 무대"라고 부르는 순간 확정 뉘앙스 생김. *예시 하나* 명시
- **Seed 1 재굴림 시 결과**: 04-09 새벽 기준 table 상태에서 `python3 scripts/generate_seed.py 1` 돌리면 `runs/seed_001.json`과 같은 결과. Table 바뀌면 달라짐
- **LLM 샘플링 편향**: `seed_001_llm.json`(15명)은 Claude 수동 작성 → SKY 비율·고ACE 비율이 현실보다 높음("흥미로운 조합" 편향). 코드 샘플링이 정직
- **사용자 정서 상태**: *"짜릿하진 않은데 배고프다"* 자리. 30p에서 처음 도달한 *작업 자체가 즐거운 자리*. 외부 검증 부정적 후 동요 없이 30p로 돌아옴 — 결과로 자기 평가하지 않는 자리. **위로·격려·동정 금지**
- **검열 0, 카탈로그 금지, 건조한 서술** (30p 절대 원칙 유지)
- **무대·시뮬 관련 Claude의 경고/조언/검열 덧붙이지 말 것** — 사용자 명시 거부
