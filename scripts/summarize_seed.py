#!/usr/bin/env python3
"""seed_NNN.json의 30명 1줄 요약 + 특이 케이스 하이라이트. stdlib only."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def edu_tier(kor, age):
    edu = kor["education"]
    if age is not None and age <= 18:
        return edu.get("school_type", "고등")[:12]
    if age is not None and age >= 26:
        return edu.get("university_tier_past", edu.get("final_education", "졸업"))[:12]
    return edu.get("university_tier", edu.get("final_education", "?"))[:12]


def one_liner(c):
    sex = c["sex"]
    body = c["body"]
    mem = c["memory"]
    ident = c["identity"]
    kor = c["korea"]
    age = c.get("age")

    height = body["height_cm"]
    face_score = body["face_attractiveness"]["absolute_score"]
    face_rank = body["face_attractiveness"]["sex_rank"]
    iq = ident["cognitive"]["iq"]
    ace = mem["ace"]["total"]
    att_style = mem["attachment"]["style"]
    reflex = mem["default_reflex"]["primary"].split(" ")[0]
    tier = edu_tier(kor, age)
    occupation = kor.get("occupation", "")
    region = kor.get("region_voice", {}).get("birth_region", "").split(" ")[0] if kor.get("region_voice") else c.get("region", "?").split(" ")[0]
    csa_flag = " M2+" if mem["csa"] else ""
    labels = " / ".join(c.get("post_hoc_label", []))
    age_str = f"{age}세" if age is not None else ""

    return (
        f"#{c['id']:02d} {sex} {age_str} {height:.0f}cm 매력{face_score}(rank{face_rank}) "
        f"IQ{iq} ACE{ace}{csa_flag} {att_style.split('-')[0][:8]} {reflex} "
        f"[{tier}] [{occupation[:14]}] {region}"
        + (f" → {labels}" if labels else "")
    )


def highlight(chars):
    """특이 케이스 5개 자동 탐지."""
    candidates = []

    # 고ACE + 고IQ (길항 조합)
    for c in chars:
        if c["memory"]["ace"]["total"] >= 4 and c["identity"]["cognitive"]["iq"] >= 115:
            candidates.append((f"고ACE+고IQ 조합", c))

    # M2 발생
    for c in chars:
        if c["memory"]["csa"]:
            candidates.append((f"M2 발생", c))

    # 극단 IQ
    chars_by_iq = sorted(chars, key=lambda c: c["identity"]["cognitive"]["iq"])
    if chars_by_iq:
        candidates.append(("최저 IQ", chars_by_iq[0]))
        candidates.append(("최고 IQ", chars_by_iq[-1]))

    # 외모 1위 M/F
    m_chars = sorted([c for c in chars if c["sex"] == "M"], key=lambda c: c["body"]["face_attractiveness"]["sex_rank"])
    f_chars = sorted([c for c in chars if c["sex"] == "F"], key=lambda c: c["body"]["face_attractiveness"]["sex_rank"])
    if m_chars:
        candidates.append(("남성 외모 1위", m_chars[0]))
    if f_chars:
        candidates.append(("여성 외모 1위", f_chars[0]))

    # 디지털 compulsion 임상 수준
    for c in chars:
        if "임상 수준" in c["identity"]["impulse_footprint"]["A_impulse"]["compulsion"]:
            candidates.append(("디지털 임상 수준", c))

    # 성소수자
    for c in chars:
        o = c["identity"]["sexuality"]["orientation"]
        if o not in ("이성애 (이성에게만)", "이성애 우세 + 동성 끌림 약함"):
            candidates.append((f"성소수자 ({o})", c))

    # 자살 사고·유서 초안 일기
    for c in chars:
        if "자살 사고" in c["identity"]["impulse_footprint"]["B_footprint"]["journal_tone"]:
            candidates.append(("자살 사고 일기", c))

    return candidates


def main():
    seed = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
    path = ROOT / "runs" / f"seed_{seed:03d}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    chars = data["characters"]

    print(f"=== seed {seed} 30명 1줄 요약 ===\n")
    for c in chars:
        print(one_liner(c))

    print("\n=== 특이 케이스 하이라이트 ===\n")
    seen = set()
    for tag, c in highlight(chars):
        key = (tag, c["id"])
        if key in seen:
            continue
        seen.add(key)
        print(f"[{tag}] {one_liner(c)}")


if __name__ == "__main__":
    main()
