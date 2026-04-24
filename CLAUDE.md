# 30p (인간30 / Human30)

**작업 모드** — 설계·고치기·옵션표·스킬 변환·리서치 전용. 시뮬(play·관찰)은 `~/pp/30p/play/` 에서 별도 세션으로 돌린다 (`play/CLAUDE.md` 참조).

LLM 기반 30인 행동 시뮬레이터. 30개의 *분리된 결정 엔진*이 같은 자극 위에서 어떻게 다르게 행동하는가를 관찰하는 도구. 사용자의 4월 메인 프로젝트.

## 모드 분리 (2026-04-09 도입)

- **작업 모드** (이 파일): `cd ~/pp/30p && cc` — 설계, 옵션표 정정, 스킬 변환, 리서치 문서 작성, 하네스
- **시뮬 모드**: `cd ~/pp/30p/play && cc` — play 호출, x/폰/무의식 관찰, 시뮬 결과 저장. 설계·옵션표 수정 금지
- **공유 폴더**: `runs/`, `tables/`, `stages/`, `scenarios/`, `docs/`, `research/`, `scripts/`, `.state/` — 두 모드 모두 접근
- **명세서**: 시뮬 모드의 명령 어휘·시간 단위·파일 포맷은 `docs/session_flow.md` 가 정답

## 세션 시작 루틴 (필수)

1. **`.state/current.md`** — 정체·철학·진행 상황 스냅샷
2. **`.state/queue.md`** — 우선순위 작업 목록
3. **`.state/log.md` 최근 3개 엔트리** — 최근 세션 맥락
4. **`.state/handoffs/` 최신 파일** — 세션 브리지 (특히 `*_mega.md`는 거대세션의 철학 축 + 금지 항목 + 사용자 정서 포함)
5. 그다음에 사용자 메시지에 답한다.

### 3겹 컨텍스트 안전망

```
Layer 1: .state/current.md + queue.md + log.md   ← 항상 (결론·상태·큐)
Layer 2: .state/handoffs/최신.md                    ← 세션 브리지 (맥락·과정·금지)
Layer 3: /resume-session [session-id]               ← 풀 transcript (세부 필요 시)
```

## 절대 원칙

- **검열 0** — 모든 층위, 캐릭터·욕망·사건·스토리 전부
- **카탈로그 금지, 작용만** — 사실 자체보다 그것이 일상에 *어떻게 휘는지*
- **건조한 서술** — *항문과 의사 톤*. 동정·개입·미화 일체 금지. 페르소나·관찰 텍스트만 건조 (캐릭터 *발화*에는 적용 안 됨)
- **사용자에게 설계 경고/조언/검열 덧붙이지 말 것** — 명시적으로 거부됨
- **단일 출력 금지 (재미 기능)** — 같은 조건 여러 번 돌려 *복수성 자체가 흥미*
- **카페라떼 미학 register 유지** — 시뮬레이터를 온건한 일상 도구로 축소시키지 말 것
- **무의식 = 캐릭터 본인이 접근 불가**한 부분. 절대자(사용자)는 *항상* 모든 것을 본다

## 데이터 모델 4층

1. **Body** — 측정 가능한 현재 사실
2. **Memory** — 과거 흔적
3. **Identity** — I1 인지 + I2 성 + I3 충동·중독·사적 디지털 발자국
4. **World Map** — 4 하위(*지금/방금/곧/배경 전제*), 매 tick 갱신

**무의식**은 별도 층 아님. 각 층의 *접근 가능 / 접근 불가* 분리 속성.

## 의존성 정책 (2026-04-08 재정의)

**외부 패키지 0** (공급망 공격 방어). 언어 무관 — 파이썬·Node·Deno 다 OK, 단 stdlib만.

- **시드 굴림**: `scripts/generate_seed.py` — stdlib Python, `random.seed(N)`으로 비트 단위 재현. 실행: `python3 scripts/generate_seed.py 1`
- **검증/요약**: `scripts/verify_seed.py`, `scripts/summarize_seed.py` — 분포 체크 + 30명 1줄 요약 + 특이 케이스 탐지
- **시뮬레이션 tick·관찰 명령** (`x-ray`/`phone`/`subconscious`): **Claude가 직접** 수행. 서사·맥락 해석이라 코드로 안 됨
- **옛 인프라** (`pyproject.toml`·`uv.lock`·`.venv/`·`scripts/generate_characters.py`·`.env.example`): 시드 0 시기. 건드리지 않음. 새 `generate_seed.py`는 4층 28표 기반 — 다른 시스템

## 세션 종료 루틴

1. `.state/log.md` 끝에 이번 세션 엔트리 추가 (목적/행위/근거/산출물/차단/다음, 태그)
2. `.state/queue.md` 갱신 (완료 [x], 새 발견 추가)
3. `.state/current.md`의 *현재 상태 / 미해결* 섹션 갱신
4. 거대 세션/전환점이면 `.state/handoffs/{날짜}_handoff*.md` 작성
5. 메모리 갱신이 필요하면 `~/.claude/projects/-Users-sanggyulee-pp/memory/`에 반영

## 폴더 구조

```
~/pp/30p/
├── CLAUDE.md            ← 이 파일 (작업 모드)
├── play/                ← 시뮬 모드 진입점
│   └── CLAUDE.md        ← 시뮬 전용 규칙 (play/x/폰/무의식만)
├── README.md
├── .state/              ← 세션 간 상태
│   ├── current.md
│   ├── log.md
│   ├── queue.md
│   └── handoffs/
├── data/                ← 시드 0 보존 (참고용)
├── tables/              ← 옵션 표 (4층 28개)
│   ├── body.json        (11)
│   ├── memory.json      (11)
│   ├── identity.json    (3)
│   └── korea.json       (3)
├── runs/                ← 시드별 30명 결과물
├── stages/              ← 무대 카탈로그
├── scenarios/           ← 시나리오
├── docs/                ← 절차·프로토콜
│   ├── operating.md
│   ├── generation_protocol.md
│   ├── observation_commands.md
│   └── session_flow.md  ← 시뮬 모드 명세 (명령 어휘·시간·포맷)
└── research/            ← 1차 리서치
```

## 4월 데드라인

- **2026-04-30**까지 30p를 *사용자가 직접 사용*할 수 있는 상태로 완성
- 5월 Claude Code 부재 가능성 — 결과물은 *Claude 없이도 사용자 노트북에서 작동*해야 함
- 우선순위 = *완성도*가 아니라 *사용 가능 시점*
