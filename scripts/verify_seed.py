#!/usr/bin/env python3
"""seed_NNN.json 간단 분포 검증. stdlib only."""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    seed = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
    path = ROOT / "runs" / f"seed_{seed:03d}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    chars = data["characters"]

    print(f"=== seed {seed} 분포 ===")
    print(f"총 캐릭터: {len(chars)}")
    sex_count = Counter(c["sex"] for c in chars)
    print(f"성비: M={sex_count['M']} F={sex_count['F']}")

    ace_dist = Counter(c["memory"]["ace"]["total"] for c in chars)
    print(f"ACE 분포: {dict(sorted(ace_dist.items()))}")

    iqs = [c["identity"]["cognitive"]["iq"] for c in chars]
    print(f"IQ: 평균={sum(iqs) / len(iqs):.1f}, min={min(iqs)}, max={max(iqs)}")

    csa_m = sum(1 for c in chars if c["memory"]["csa"] and c["sex"] == "M")
    csa_f = sum(1 for c in chars if c["memory"]["csa"] and c["sex"] == "F")
    print(f"CSA 발생: 전체 {csa_m + csa_f}명 (M {csa_m}/15, F {csa_f}/15)")

    att = Counter(c["memory"]["attachment"]["style"] for c in chars)
    print("Attachment:")
    for k, n in att.most_common():
        print(f"  {k}: {n}")

    reflex = Counter(c["memory"]["default_reflex"]["primary"] for c in chars)
    print("Default reflex:")
    for k, n in reflex.most_common():
        print(f"  {k}: {n}")

    tier = Counter(c["korea"]["education"]["university_tier"] for c in chars)
    print("대학 tier:")
    for k, n in tier.most_common():
        print(f"  {k}: {n}")

    orient = Counter(c["identity"]["sexuality"]["orientation"] for c in chars)
    print("Sexual orientation:")
    for k, n in orient.most_common():
        print(f"  {k}: {n}")

    heights = [c["body"]["height_cm"] for c in chars]
    print(f"키: 평균={sum(heights) / len(heights):.1f}cm, min={min(heights)}, max={max(heights)}")


if __name__ == "__main__":
    main()
