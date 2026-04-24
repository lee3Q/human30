# runs/ — 시드별 30명 결과물

이 디렉토리에는 시드 번호별로 굴린 30명 캐릭터의 풀 프로필 JSON이 저장된다.

## 파일명 규칙

`seed_{N}.json` — N은 3자리 0패딩 정수.

예:
- `seed_001.json`
- `seed_042.json`
- `seed_1024.json`

## 파일 구조

`docs/generation_protocol.md` §6 참조. 요약:
```json
{
  "seed": 1,
  "generated_at": "2026-04-08T20:00:00+09:00",
  "constraints": { ... },
  "table_versions": { ... },
  "characters": [ /* 30명 */ ],
  "post_generation_notes": [ ... ]
}
```

## 재현성 정책

- **같은 시드 = 같은 결과물** 원칙은 *이 디렉토리의 파일로* 보장된다 (비트 단위 재현 아님)
- 사용자가 *"시드 N으로 굴려"* 호출 시:
  - `runs/seed_N.json` 존재 → 로드 (재굴림 안 함)
  - 없음 → 굴려서 저장
- **재굴림 필요 시** 사용자가 명시적으로 *"시드 N 재굴림"* 또는 파일 삭제

## 파일 관리

- 30p의 *핵심 결과물*이므로 git 추적 권장
- 크기가 커지면 `.gitignore`에 추가하고 별도 백업
- 5월 이후 Claude Code 부재 시에도 *사용자가 이 JSON만 있으면* 캐릭터 상태 읽을 수 있어야 함

## 시나리오 실행 후

시뮬레이션을 돌린 후 *캐릭터 상태 변화*가 누적되면, 그 결과는 `runs/seed_N_scenario_Sxxx.json` 같은 파생 파일에 저장할 수 있다. 원본 `seed_N.json`은 **불변 초기 상태**로 보존.

명명 제안:
- `seed_001.json` — 시드 1 초기 상태 (불변)
- `seed_001_S001A_t0.json` — 시드 1 + 시나리오 S001-A의 초기 tick
- `seed_001_S001A_t15.json` — tick 15 이후 상태
- `seed_001_S001A_final.json` — 시뮬 종료 상태

이 명명은 첫 시뮬 돌리고 필요에 따라 조정.
