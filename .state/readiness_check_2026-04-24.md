# 30p 4/30 데드라인 D-6 준비 상태 점검

**점검일**: 2026-04-24
**데드라인**: 2026-04-30 (D-6)
**목표**: "사용자가 직접 사용할 수 있는 상태" + "Claude 없이도 사용자 노트북에서 작동"

---

## 1. 독립 실행 가능 항목 (Claude 무관)

| 기능 | 명령 | 상태 | 비고 |
|------|------|------|------|
| 시드 생성 | `python3 scripts/generate_seed.py N` | ✅ 정상 | stdlib only, 비트 재현 |
| 카드 생성 | `python3 scripts/card.py N [id\|all]` | ✅ 정상 | 차트+서열+스토리 |
| 시드 요약 | `python3 scripts/summarize_seed.py N` | ✅ 정상 | 30명 1줄 요약 |
| 캐릭터 검사 | `python3 scripts/inspect_char.py N id` | ✅ 정상 | 상세 필드 |
| 시드 검증 | `python3 scripts/verify_seed.py N` | ✅ 정상 | 분포 체크 |

**결론**: 시드 생성 파이프라인은 Claude 없이 완전히 작동. 의존성 0.

## 2. Claude 의존 항목 (핵심 문제)

| 기능 | Claude 필요 | 대안 가능? |
|------|-------------|-----------|
| play 모드 (시뮬 tick) | **필수** | 다른 LLM으로 이식 가능 (아래 참조) |
| x-ray / phone / 무의식 | **필수** | system prompt 이식으로 해결 |
| 캐릭터 행동 생성 | **필수** | LLM 호출 = 엔진 본체 |
| 관찰 결과 해석 | **필수** | LLM 필요 |
| 옵션표 수정 | **필수** | JSON 직접 편집 가능 (숙련자) |

**핵심 인식**: 30p의 시뮬레이션 엔진 = LLM. 코드가 엔진이 아니다. `generate_seed.py`는 캐릭터를 *생성*하지만, 캐릭터가 *행동*하는 것은 LLM의 역할이다. 이 구조는 Stanford Generative Agents와 동일.

## 3. Claude 부재 대비 전략

### 전략 A: 이식 가능 시스템 프롬프트 (권장)

`play/CLAUDE.md` + `docs/session_flow.md` + `docs/observation_commands.md`를 하나의 독립적 시스템 프롬프트로 병합. 이 프롬프트는 Claude가 아니라 **어떤 LLM**에도 작동:

- GPT-4 / GPT-4o: system message로 삽입
- Gemini: system instruction으로 삽입
- 로컬 모델: 시스템 프롬프트로 삽입
- Perplexity: 기능 제한적이나 기본 play 가능

**필요 작업**:
1. `play/CLAUDE.md` → LLM 불문 버전으로 변환 (Claude Code 특화 명령 제거)
2. `session_flow.md` 핵심 섹션(2~9) 병합
3. `observation_commands.md` 출력 포맷 병합
4. `current.md`의 4층 데이터 모델·철학 핵심 병합
5. 결과물: `~/pp/30p/docs/PORTABLE_PROMPT.md` (단일 파일)

### 전략 B: 옵션표 + 시드 JSON 직접 열람

LLM 없이도 시드 JSON을 열어서 캐릭터 데이터를 읽을 수 있다. `card.py`로 카드 생성 후 인쇄해둘 수도 있다. 하지만 "시뮬레이션"은 불가능. 정적 캐릭터 카탈로그로만 사용.

### 전략 C: Python TUI (보류)

의존성 정책(외부 패키지 0)과 충돌. Textual·Rich 등 필요. 4/30까지 불가.

## 4. D-6 필수 태스크

### 4/25 (금) — 전략 A 실행

- [ ] PORTABLE_PROMPT.md 초안 작성
- [ ] 기존 play 모드 문서 4개에서 핵심 추출·병합
- [ ] LLM 불문 동작 테스트 (GPT-4o 1회, Gemini 1회)

### 4/26 (토) — 이식 테스트

- [ ] GPT-4o에서 시드 1 캐릭터 #1 x-ray 실행
- [ ] Gemini에서 시드 1 play "5분 @ 강당 '처형 투표 결과 발표'" 실행
- [ ] 각 LLM별 출력 품질 비교

### 4/27~28 (일~월) — 이식 검증

- [ ] 다른 LLM에서도 카페라떼 미학 register 유지되는지 확인
- [ ] 4층 데이터 모델 이해도 확인
- [ ] 관찰 명령 출력 포맷 준수 확인

### 4/29~30 (화~수) — 최종

- [ ] PORTABLE_PROMPT.md 최종 버전
- [ ] 사용법 1페이지 가이드 (`~/pp/30p/docs/QUICKSTART.md`)
- [ ] 이상규가 cc 없이 다른 LLM으로 바로 시작할 수 있는 상태

## 5. 현재 기능 요약

**할 수 있는 것** (지금 당장):
- `python3 scripts/generate_seed.py 42` → 새 시드 30명 생성
- `python3 scripts/card.py 42 all` → 30명 카드 출력
- `cd ~/pp/30p/play && cc` → Claude Code에서 play 모드

**할 수 없는 것** (Claude 없이):
- 캐릭터 행동 시뮬레이션
- 관찰 명령 (x-ray, phone, 무의식)
- 시나리오 실행

**4/30까지 해결해야 할 것**:
- PORTABLE_PROMPT.md로 Claude 의존성 제거
- 다른 LLM에서 최소 play + x-ray 동작 확인

---

*점검: 2026-04-24 (Opus 자율 세션)*
