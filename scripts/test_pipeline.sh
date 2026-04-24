#!/usr/bin/env bash
# test_pipeline.sh — 30p 전체 파이프라인 일괄 테스트
# 사용: bash test_pipeline.sh [시드번호]
# 기본: 시드 99 (테스트 전용, 기존 시드 덮어쓰지 않음)
set -euo pipefail

SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPTS")"
SEED="${1:-99}"
PADDED="$(printf '%03d' "$SEED")"
SEED_FILE="$ROOT/runs/seed_${PADDED}.json"

PASS=0; FAIL=0; WARN=0
p() { echo "  ✅ $1"; PASS=$((PASS+1)); }
f() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
w() { echo "  ⚠️  $1"; WARN=$((WARN+1)); }

echo "========================================"
echo " 30p 파이프라인 테스트 — seed $SEED"
echo "========================================"
echo ""

# ── 0. 사전 조건 ──
echo "── 0. 사전 조건 ──"
for f in "$ROOT/tables/body.json" "$ROOT/tables/memory.json" "$ROOT/tables/identity.json" "$ROOT/tables/korea.json"; do
  if [ -f "$f" ]; then p "$(basename "$f") 존재"; else f "$(basename "$f") 누락"; fi
done
for s in generate_seed.py verify_seed.py summarize_seed.py inspect_char.py card_renderer.html; do
  if [ -f "$SCRIPTS/$s" ]; then p "$s 존재"; else f "$s 누락"; fi
done
echo ""

# ── 1. 시드 생성 ──
echo "── 1. 시드 생성 (generate_seed.py) ──"
if python3 "$SCRIPTS/generate_seed.py" "$SEED" 2>&1; then
  if [ -f "$SEED_FILE" ]; then
    SIZE=$(wc -c < "$SEED_FILE")
    p "시드 파일 생성됨 (${SIZE} bytes)"
  else
    f "시드 파일 미생성"
  fi
else
  f "generate_seed.py 실행 실패"
fi
echo ""

# ── 2. JSON 구조 검증 ──
echo "── 2. JSON 구조 검증 ──"
if [ ! -f "$SEED_FILE" ]; then
  f "시드 파일 없음 — 이후 단계 건너뜀"
else
  # 기본 필드 확인
  if python3 -c "
import json, sys
d = json.load(open('$SEED_FILE'))
assert 'seed' in d, 'seed 필드 누락'
assert 'characters' in d, 'characters 필드 누락'
assert isinstance(d['characters'], list), 'characters가 리스트가 아님'
assert len(d['characters']) == 30, f'캐릭터 수 {len(d[\"characters\"])} (30 expected)'
c = d['characters'][0]
for k in ('sex','age','body','memory','identity','korea'):
    assert k in c, f'캐릭터 필드 {k} 누락'
print(f'  캐릭터 {len(d[\"characters\"])}명, 필드 구조 OK')
" 2>&1; then
    p "JSON 구조 유효"
  else
    f "JSON 구조 오류"
  fi
fi
echo ""

# ── 3. 분포 검증 (verify_seed.py) ──
echo "── 3. 분포 검증 (verify_seed.py) ──"
if [ -f "$SEED_FILE" ]; then
  if python3 "$SCRIPTS/verify_seed.py" "$SEED" 2>&1; then
    p "verify_seed.py 실행 성공"
  else
    f "verify_seed.py 실행 실패"
  fi
else
  w "시드 파일 없음 — 건너뜀"
fi
echo ""

# ── 4. 요약 (summarize_seed.py) ──
echo "── 4. 1줄 요약 (summarize_seed.py) ──"
if [ -f "$SEED_FILE" ]; then
  if python3 "$SCRIPTS/summarize_seed.py" "$SEED" 2>&1; then
    p "summarize_seed.py 실행 성공"
  else
    f "summarize_seed.py 실행 실패"
  fi
else
  w "시드 파일 없음 — 건너뜀"
fi
echo ""

# ── 5. 개별 캐릭터 검사 (inspect_char.py) ──
echo "── 5. 개별 캐릭터 검사 (inspect_char.py, 3명) ──"
if [ -f "$SEED_FILE" ]; then
  if python3 "$SCRIPTS/inspect_char.py" "$SEED" 1 15 30 2>&1; then
    p "inspect_char.py 실행 성공 (1, 15, 30)"
  else
    f "inspect_char.py 실행 실패"
  fi
else
  w "시드 파일 없음 — 건너뜀"
fi
echo ""

# ── 6. 카드 렌더러 파일 무결성 ──
echo "── 6. 카드 렌더러 HTML ──"
RENDERER="$SCRIPTS/card_renderer.html"
if [ -f "$RENDERER" ]; then
  if grep -q 'loadSeed' "$RENDERER" && grep -q 'renderCard' "$RENDERER"; then
    p "card_renderer.html 핵심 함수 존재"
  else
    f "card_renderer.html 핵심 함수 누락"
  fi
  # 시드 JSON을 드래그앤드롭 가능한지 input[type=file] 확인
  if grep -q 'type="file"' "$RENDERER"; then
    p "파일 입력 UI 존재"
  else
    w "파일 입력 UI 누락"
  fi
else
  f "card_renderer.html 파일 없음"
fi
echo ""

# ── 7. 재현성 테스트 ──
echo "── 7. 재현성 테스트 (같은 시드 = 같은 결과) ──"
if [ -f "$SEED_FILE" ]; then
  # generated_at 타임스탬프 제외 후 비교
  BODY1=$(python3 -c "
import json
d = json.load(open('$SEED_FILE'))
d.pop('generated_at', None)
json.dumps(d, sort_keys=True, ensure_ascii=False)
")
  python3 "$SCRIPTS/generate_seed.py" "$SEED" > /dev/null 2>&1
  BODY2=$(python3 -c "
import json
d = json.load(open('$SEED_FILE'))
d.pop('generated_at', None)
json.dumps(d, sort_keys=True, ensure_ascii=False)
")
  if [ "$BODY1" = "$BODY2" ]; then
    p "재현성 확인 (generated_at 제외 후 동일)"
  else
    f "재현성 실패 (본문 불일치)"
  fi
else
  w "시드 파일 없음 — 건너뜀"
fi
echo ""

# ── 결과 ──
echo "========================================"
echo " 결과: PASS=$PASS  FAIL=$FAIL  WARN=$WARN"
if [ "$FAIL" -eq 0 ]; then
  echo " 🟢 전체 통과"
else
  echo " 🔴 실패 $FAIL건 — 수정 필요"
fi
echo "========================================"

# 테스트 시드 정리 (기존 시드가 아닌 경우만)
if [ "$SEED" = "99" ] && [ -f "$SEED_FILE" ]; then
  rm "$SEED_FILE"
  echo " (테스트 시드 seed_099.json 정리됨)"
fi

exit "$FAIL"
