# Alias 제안 — 30p 시뮬 모드 분리 대응

> **이 파일은 제안서다. `~/.zshrc` 는 직접 수정하지 않았다. 사용자가 검토 후 직접 적용한다.**
> 생성: 2026-04-09 (ux_design 하네스 자율 실행)
> 근거: `harnesses/ux_design.md` 섹션 1 + 사용자 메모리 `feedback_alias_convention.md` (*alias 는 cd 만, cc 로 별도 시작*) + `feedback_pp_path.md` (한글 폴더명 지양)

---

## 현재 `.zshrc` 상태 (2026-04-09 확인)

관련 alias 만 추림:

```bash
alias cc="claude --dangerously-skip-permissions"
alias ccc="claude --continue --dangerously-skip-permissions"
alias cs="claude --dangerously-skip-permissions --model sonnet"

alias pp="cd ~/pp/작업실"
alias ss="cd ~/pp/세계관"
alias nn="cd ~/pp/학습/노무사"

alias ppl="bash ~/pp/scripts/pullim-state-commit.sh"
alias pps="echo '=== Active ===' && head -3 ~/pp/pullim/.state/projects/*.md ..."
```

### 문제 진단

1. **`pp` 가 `~/pp` 가 아니라 `~/pp/작업실`** — 워크스페이스 루트 진입 alias 가 없다. `~/pp` 자체로 가려면 매번 타이핑.
2. **`ss` 가 `~/pp/세계관`** — 세계관은 풀림 계열 (동결 대상). 4월 30p 작업 중에는 *거의 쓰지 않을* 경로. 시뮬 모드 진입 alias 로 재할당하는 것이 4월 메인 프로젝트와 정합.
3. **`nn` 이 `~/pp/학습/노무사`** — 노무사는 유지 작업 (스킬로 접근). 30p 작업 모드 진입 alias 로 재할당하면 하루에 여러 번 쓰는 경로가 짧아진다.
4. **한글 폴더 경로 alias** (`작업실`, `세계관`, `학습/노무사`) — 사용자 메모리 `feedback_pp_path.md` (한글 폴더명 지양) 와 *기존 alias 가* 어긋나 있다. 이건 과거 폴더 구조 흔적으로 추정.
5. **`pullim` 관련 `ppl`, `pps`, `p`, `p1`, `p2`, `ppp`, `ww`** — 풀림 계열. *동결* 대상. 이번 작업 범위 외. **건드리지 말 것**.

### 충돌 없는 부분

- **`cc`, `ccc`, `cs`, `gg`** — Claude 시작 alias. 원칙 `cc 로 별도 시작` 과 정합. 유지.
- **`y`, `qq`** — 다른 LLM. 유지.
- **`q` 함수** — 리서치 저장 함수. 유지.
- **`gclaude` 함수** — GLM 전환. 유지.

---

## 제안안

### Variant A — 요구된 기본안 (사용자 원칙 최대 적용)

```diff
-alias pp="cd ~/pp/작업실"
-alias ss="cd ~/pp/세계관"
-alias nn="cd ~/pp/학습/노무사"
+alias pp="cd ~/pp"              # 워크스페이스 루트
+alias nn="cd ~/pp/30p"          # 30p 작업 모드
+alias ss="cd ~/pp/30p/play"     # 30p 시뮬 모드
```

**근거**:
- `pp` = 워크스페이스 루트. 기존 `~/pp/작업실` 경로는 4월 구조 개편 후 거의 안 씀 (사용자가 4월 5일 폴더 전면 개편 커밋)
- `nn` = 30p 작업 모드. "`n`=`nonsa`(노무사)" 해석을 버리고 "`nn`=`30p` 작업" 으로 재정의. 4월 한달 메인 프로젝트에 짧은 alias 를 주는 것이 비용 대비 효과 큼
- `ss` = 30p 시뮬 모드 (`play/`). "`s`=`세계관`" 해석을 버림. 세계관 자체가 4월 동결 대상
- 원칙 준수: *cd 만 하고, cc 로 별도 시작*. cc 는 현재 그대로 (`alias cc="claude --dangerously-skip-permissions"`)

**사용 흐름**:
```
nn && cc    ← 30p 작업 세션 (설계·옵션표·스킬 변환)
ss && cc    ← 30p 시뮬 세션 (play·관찰)
pp          ← 루트로 나오기
```

### Variant B — 충돌 회피안 (`ss` 가 편해서 바꾸기 싫은 경우)

```diff
-alias pp="cd ~/pp/작업실"
+alias pp="cd ~/pp"              # 워크스페이스 루트
+alias nn="cd ~/pp/30p"          # 30p 작업 모드
+alias pl="cd ~/pp/30p/play"     # 30p 시뮬 모드 (pl = play 축약)
 # ss, nn 기존 경로 유지
```

`ss`, `nn` 기존 한글 경로를 *유지*하고, 시뮬 모드는 새 alias `pl` 로 추가. 기존 근육 기억 파괴 최소화. 단 `nn` 이 노무사를 가리키므로 30p 작업은 매번 `cd ~/pp/30p` 풀 타이핑 또는 새 alias `thirp` 같은 것 필요 — 타협안이라 최적 아님.

### Variant C — 완전 새 네이밍 (충돌 회피 + 원칙 준수)

```diff
+alias pp="cd ~/pp"                  # 루트
+alias th="cd ~/pp/30p"              # 30p 작업 모드 (th = thirty)
+alias tp="cd ~/pp/30p/play"         # 30p 시뮬 모드 (tp = thirty play)
 # ss, nn 기존 경로 유지 (건드리지 않음)
```

`th`, `tp` 는 기존 어느 alias 와도 충돌 안 함. 30p 전용 네이밍이라 의미가 명확. 단 두 글자 근육 기억을 새로 만들어야 함.

---

## 추천: **Variant A**

- 4월 30p 메인 프로젝트 기간 (21일) 중 가장 자주 쓰는 경로 2개 (`30p/`, `30p/play/`) 에 제일 짧은 alias (`nn`, `ss`) 를 배정
- 기존 `pp=~/pp/작업실` 은 4월 폴더 개편 이후 거의 의미 없는 경로
- `ss=~/pp/세계관` 은 동결 대상이라 4월엔 쓸 일 없음
- 사용자 원칙 (*cd 만, cc 로 별도 시작*, *한글 폴더 지양*) 에 가장 잘 맞음

**단 하나의 리스크**: `nn` 이 "노무사" 로 근육에 박혀 있으면 초기 며칠 헷갈림. 노무사는 스킬로 접근하므로 alias 자체가 필수는 아니지만, 필요하면 `no` 또는 `nm` 같은 새 alias 추가:

```diff
+alias no="cd ~/pp/학습/노무사"    # 노무사 (기존 nn 이 30p 로 재할당됐으므로 대체)
```

---

## 적용 방법 (사용자가 승인 후 직접)

### Step 1 — `.zshrc` 편집
```
$EDITOR ~/.zshrc
```
위 Variant A diff 를 수동 반영. 기존 `pullim` 관련 줄 절대 건드리지 않기.

### Step 2 — 새 터미널 열기 (권장)
`source ~/.zshrc` 보다 *새 터미널* 이 깔끔. 기존 쉘의 구 alias 잔존 방지.

### Step 3 — 확인
```
alias pp nn ss
```
3개 모두 새 경로 출력되면 완료.

### Step 4 — 동작 확인
```
nn    # → ~/pp/30p (작업 모드 진입)
cc    # → Claude 시작, CLAUDE.md 자동 로드
# 다른 터미널 창에서:
ss    # → ~/pp/30p/play (시뮬 모드 진입)
cc    # → Claude 시작, play/CLAUDE.md 자동 로드
```

두 창이 *다른 모드*로 분리되면 성공.

---

## 건드리지 않은 것 (명시)

- `~/.zshrc` 파일 자체 (이 제안서만 생성)
- `cc`, `ccc`, `cs`, `gg`, `gclaude`, `y`, `qq` (Claude / LLM 시작 계열)
- `q` 함수 (리서치 저장)
- `ppl`, `pps`, `p`, `p1`, `p2`, `ppp`, `ww` 함수 (pullim / 동결 계열 — 건드리지 말 것)
- `PATH`, `source` 관련 줄
- Telegram Bot 관련 줄

---

## 메모 — 사용자 원칙 재확인

`feedback_alias_convention.md`: *"alias 는 cd 만, cc 로 별도 시작"* → 이 제안은 100% 준수 (`pp/nn/ss` 전부 순수 cd).

`feedback_pp_path.md`: *"한글 폴더명 지양, 단 '동결' 은 예외"* → Variant A 는 한글 경로 alias 3개를 전부 영문 경로로 재할당.

`feedback_simplicity.md`: *"이미 있는 시스템 활용 → 새 메커니즘"* → 기존 3개 alias (`pp/nn/ss`) 이름을 재활용. 새 alias 추가 대신 재할당. 최소 변경.
