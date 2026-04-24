# 30p 빠른 시작 가이드

**30p (인간30)** — 1분 안에 시작하는 법.

---

## 1단계: 시드 생성 (30초)

```bash
cd ~/pp/30p
python3 scripts/generate_seed.py 1
```

출력: `runs/seed_001.json` (30명 분량)

다른 시드 번호를 쓰면 완전히 다른 30명이 나온다. 같은 번호 = 같은 결과 (비트 재현).

## 2단계: 캐릭터 카드 보기 (10초)

```bash
python3 scripts/card.py 1 all       # 30명 전체 카드
python3 scripts/card.py 1 5         # 5번 캐릭터만
```

## 3단계: LLM에서 시뮬레이션 실행 (2분)

### Claude 웹 / ChatGPT / Gemini

1. `docs/PORTABLE_PROMPT.md` 전체를 복사해서 **시스템 프롬프트**에 붙여넣기
   - Claude 웹: "Custom Instructions" 또는 첫 메시지에 "시스템 프롬프트로 써:" 뒤에 붙여넣기
   - ChatGPT: "Customize ChatGPT" → Instructions에 붙여넣기
   - Gemini: "System Instructions"에 붙여넣기

2. 캐릭터 데이터 제공:
   - `runs/seed_001.json`을 열어서 관찰할 캐릭터 부분을 복사해 대화에 붙여넣기
   - 또는 `card.py` 출력 결과를 붙여넣기

3. play 호출 (자연어):
   ```
   play 시드 1 캐릭터 5 "5분 @ 강당, 처형 투표 결과 발표 직후"
   ```

4. 관찰 명령:
   ```
   x-ray 5        → 속마음 관찰
   phone 5         → 폰 상태 (최근 앱·메시지)
   무의식 5        → 캐릭터 본인도 모르는 것
   ```

### Claude Code (터미널)

```bash
cd ~/pp/30p/play && cc
# "play 시드 1 캐릭터 5 ..." 입력
```

---

## 최소 경로 요약

```
시드 생성 → 카드 확인 → PORTABLE_PROMPT를 LLM에 붙여넣기 → play 호출 → 관찰
```

## 보조 스크립트

| 명령 | 기능 |
|------|------|
| `python3 scripts/summarize_seed.py 1` | 30명 1줄 요약 |
| `python3 scripts/inspect_char.py 1 5` | 5번 캐릭터 상세 필드 |
| `python3 scripts/verify_seed.py 1` | 분포 검증 |

## 전제 조건

- Python 3 (stdlib만, 외부 패키지 불필요)
- `tables/` 폴더에 4개 JSON (body·memory·identity·korea)
- 시뮬레이션 실행을 위한 LLM 접근 (Claude·GPT·Gemini 중任何一个)

## 시나리오 예시

| 시나리오 | play 호출 문장 |
|----------|---------------|
| 처형 투표 | `"처형 투표 후 결과 발표, 강당"` |
| 재수학원 하루 | `"평범한 수요일 오전, 재수학원 자습실"` |
| 명절 모임 | `"추석 저녁, 친척 12명 모임"` |

---

*버전: 2026-04-24. 문의: `~/pp/30p/docs/` 폴더의 상세 문서 참조.*
