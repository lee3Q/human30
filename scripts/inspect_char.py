#!/usr/bin/env python3
"""특정 캐릭터의 핵심 필드만 뽑아 깊이 있는 요약 출력. stdlib only.

사용: python3 inspect_char.py <seed> <id1> [id2 ...]
예: python3 inspect_char.py 1 1 9 21 26 28
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fmt_character(c):
    sex = c["sex"]
    b = c["body"]
    m = c["memory"]
    ident = c["identity"]
    k = c["korea"]
    labels = " / ".join(c["post_hoc_label"])

    lines = []
    lines.append(f"━━━ #{c['id']:02d} {sex} · {labels} ━━━")

    # Body 핵심
    face = b["face_attractiveness"]
    bc = b["body_composition"]
    si = b["self_image"]
    lines.append(f"[body] {b['height_cm']:.0f}cm BMI{bc['bmi']} 매력{face['absolute_score']}/rank{face['sex_rank']} "
                 f"| 얼굴 {b['face_features']['shape']}, {b['face_features']['eyelid']}, "
                 f"비대칭{b['face_features']['asymmetry_mm']}mm")
    if sex == "M":
        sc = b["sex_characteristics"]
        lines.append(f"       성기 {sc['penis_length_cm']}cm × {sc['penis_girth_cm']}cm, {sc['foreskin']}, {sc['erectile_function']}")
    else:
        sc = b["sex_characteristics"]
        lines.append(f"       가슴 {sc['breast_cup']} ({sc['breast_asymmetry']}), 생리 {sc['menstrual']['cycle_regularity']}/{sc['menstrual']['pain_severity']}")
    lines.append(f"       자기 이미지: 얼굴={si['face']}, 몸={si['body']}, 성기={si['genital']}, 집중={si['focused_concern']}")
    if b["chronic_health"]:
        ch = ", ".join(f"{x['condition']}({x['severity']})" for x in b["chronic_health"])
        lines.append(f"       만성: {ch}")
    lines.append(f"       수면: {b['sleep']['duration_hours']}h {b['sleep']['chronotype']} / {b['sleep']['current_debt']}, 불면={b['sleep']['insomnia']}")
    if b["skin_hair"]["scars"]:
        lines.append(f"       흉터: {b['skin_hair']['scars']}")

    # Memory 핵심
    ace = m["ace"]
    lines.append(f"[memory] ACE={ace['total']} {ace['categories']}")
    if m["csa"]:
        csa = m["csa"]
        lines.append(f"         ✱ CSA: {csa['first_age']} / {csa['perpetrator']} / {csa['frequency']} / {csa['physical_intensity']}")
        lines.append(f"           채널={csa['primary_sensory_channel']}, 처리={csa['narrative_processing']}, 공개={csa['disclosure']}")
    pl = m["parental_loss"]
    lines.append(f"         가족구조: {pl['status']}")
    ff = m["formative_family"]
    lines.append(f"         가정: SES {ff['ses_quintile']}, 부 {ff['father_occupation']}, 모 {ff['mother_employment']}, {ff['sibling_structure']}, {ff['economic_stability']}, 분위기={ff['emotional_climate']}")
    pv = m["parent_voice"]
    lines.append(f"         부모 음성: 어머니={pv['mother_pattern']} / 아버지={pv['father_pattern']} / {pv['consistency']} / 압력={pv['intergenerational_pressure']}")
    att = m["attachment"]
    lines.append(f"         애착: {att['style']} (불안{att['anxiety']}/회피{att['avoidance']}, {att['threshold']})")
    bul = m["bullying"]
    lines.append(f"         학폭: 피해={bul['victim']}, 가해={bul['perpetrator']}, {bul['form'] or '없음'}, {bul['dual_role']}")
    reflex = m["default_reflex"]
    lines.append(f"         반사: {reflex['primary']} (+{reflex['secondary']}) / {reflex['threshold']} / {reflex['polyvagal']}")
    if m["embedded_sentences"]:
        lines.append("         박힌 문장:")
        for s in m["embedded_sentences"]:
            lines.append(f"           · {s['speaker']}: {s['message_type']} → {s['trigger']} ({s['consciousness']})")
    if m["embedded_reactions"]:
        lines.append("         박힌 반응:")
        for r in m["embedded_reactions"]:
            lines.append(f"           · {r['target']} — {r['reaction']} / {r['reactor']} @ {r['age']} (before: {r['self_image_before']}, rupture: {r['rupture_depth']})")
    if m["trauma_trigger"]:
        lines.append("         트라우마 트리거:")
        for t in m["trauma_trigger"]:
            lines.append(f"           · {t['channel']} | {t['intensity']} | {t['consciousness']}")

    # Identity 핵심
    cog = ident["cognitive"]
    lines.append(f"[identity] IQ={cog['iq']}, {cog['strength']} / {cog['weakness']}, 학업={cog['academic_performance']}, 메타={cog['metacognition']}, 사고={cog['thinking_style']}, 호기심={cog['curiosity']}")
    sx = ident["sexuality"]
    fn = sx["function"]
    lines.append(f"           성: {sx['orientation']} / out={sx['out_status']} / 경험={sx['experience']} / 첫={sx['first_age']}")
    lines.append(f"           욕망: {sx['desire_intensity']}, 결={sx['desire_grain']}, 기능={fn['arousal']}/{fn['performance']}/{fn['satisfaction']}, consent={sx['consent_marker']}")
    if sx["taboos"]:
        lines.append(f"           금기: {sx['taboos']}")
    impA = ident["impulse_footprint"]["A_impulse"]
    impB = ident["impulse_footprint"]["B_footprint"]
    subs = impA["substances"]
    lines.append(f"           충동/중독: 디지털 {impA['digital_hours']}h ({impA['compulsion']}), 술={subs['alcohol']}, 담배={subs['smoking']}, 카페인={subs['caffeine']}, 기타={subs['other']}")
    lines.append(f"                     식={impA['eating_impulse']}, 통제={impA['impulse_control']}, 보상={impA['reward_sensitivity']}, 회피={impA['escape_default']}, 자각={impA['self_awareness']}")
    lines.append(f"           폰 스냅샷: 일기={impB['journal_tone']}, SNS={impB['sns_public_face']}, 공사 간극={impB['private_vs_public_gap']}")
    lines.append(f"                     커뮤={impB['communities']}, 게임={impB['games']}")
    lines.append(f"                     검색={impB['recent_search']}")

    # Korea 핵심 (나이 분기 지원)
    age = c.get("age")
    ed = k["education"]
    if age is not None and age <= 18:
        lines.append(f"[korea] 학력: {ed.get('current_status', '?')} / {ed.get('school_type', '?')}, 성적={ed.get('academic_performance', '?')}, 사교육={ed.get('private_education', '?')}")
        lines.append(f"         부모 압력={ed.get('parental_pressure', '?')}")
    elif age is not None and age >= 26:
        lines.append(f"[korea] 학력: {ed.get('final_education', '?')} / 과거 {ed.get('university_tier_past', '?')} ({ed.get('major_past', '?')}), 현재={ed.get('current_status', '?')}")
        lines.append(f"         자기 학력관: {ed.get('academic_self_concept', '?')}")
    else:
        lines.append(f"[korea] 학력: {ed.get('high_school', '?')} → 수능{ed.get('suneung_grade', '?')} → {ed.get('university_tier', '?')} ({ed.get('major', '?')}), 재수={ed.get('retake', '?')}, 사교육={ed.get('private_education', '?')}")
        lines.append(f"         자기 학력관: {ed.get('academic_self_concept', '?')}, 부모 압력={ed.get('parental_pressure', '?')}")
    occ = k.get("occupation")
    if occ:
        lines.append(f"         직업: {occ}")
    app = k["appearance_experience"]
    lines.append(f"         외모: 차별={app['discrimination_frequency']} ({app['discrimination_domain']}), 관리={app['management_level']}, 성형={app['cosmetic_surgery']}, 다이어트={app['diet_history']}")
    lines.append(f"                lookism={app['lookism_internalization']}, capital={app['capital_awareness']}")
    rv = k["region_voice"]
    lines.append(f"         지역/정치: {rv['birth_region']} → {rv['residence_match']}, 억양={rv['accent_intensity']} ({rv['accent_self_conscious']})")
    lines.append(f"                     가족 정치={rv['family_politics']} → 본인={rv['personal_politics']} | 종교 가족={rv['family_religion']} → 본인={rv['personal_religion']} | 지역 차별={rv['regional_discrimination']}")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 inspect_char.py <seed> <id1> [id2 ...]", file=sys.stderr)
        sys.exit(1)
    seed = int(sys.argv[1])
    ids = [int(x) for x in sys.argv[2:]]
    data = json.loads((ROOT / "runs" / f"seed_{seed:03d}.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in data["characters"]}
    for cid in ids:
        c = by_id.get(cid)
        if not c:
            print(f"id={cid} 없음", file=sys.stderr)
            continue
        print(fmt_character(c))
        print()


if __name__ == "__main__":
    main()
