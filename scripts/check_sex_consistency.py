#!/usr/bin/env python3
"""성별 교차 검증: 남성이 '가슴 크기'를 concern에 뽑았는지, 여성이 '성기 크기'를 뽑았는지, 여유증 F 보유 등."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    seed = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
    data = json.loads((ROOT / "runs" / f"seed_{seed:03d}.json").read_text(encoding="utf-8"))
    chars = data["characters"]

    errors = []
    gyno_cases = []

    for c in chars:
        cid = c["id"]
        sex = c["sex"]
        concerns = c["body"]["self_image"]["focused_concern"]
        if sex == "M" and "가슴 크기" in concerns:
            errors.append(f"#{cid:02d} M focused_concern에 '가슴 크기'")
        if sex == "F" and "성기 크기" in concerns:
            errors.append(f"#{cid:02d} F focused_concern에 '성기 크기'")
        for ch in c["body"]["chronic_health"]:
            if "여유증" in ch["condition"]:
                if sex != "M":
                    errors.append(f"#{cid:02d} {sex} 여유증 보유")
                else:
                    gyno_cases.append(f"#{cid:02d} M 여유증 {ch['severity']}")

    if errors:
        print("=== 오류 ===")
        for e in errors:
            print(f"  {e}")
    else:
        print("✓ 성별 교차 오류 없음")

    if gyno_cases:
        print(f"\n=== 여유증 {len(gyno_cases)}명 ===")
        for g in gyno_cases:
            print(f"  {g}")

    # 참고: 어떤 캐릭터가 어떤 focused_concern 뽑았는지 샘플
    print("\n=== focused_concern 샘플 (모든 캐릭터) ===")
    for c in chars[:10]:
        print(f"  #{c['id']:02d} {c['sex']} → {c['body']['self_image']['focused_concern']}")


if __name__ == "__main__":
    main()
