#!/usr/bin/env python3
"""인간군상 차트 카드 생성기 — 자연어, 서열 포함. stdlib only. 토큰 0.

사용:
    python3 scripts/card.py <seed> <id1> [id2 ...]
    python3 scripts/card.py 1 9
    python3 scripts/card.py 1 all      # 30명 전체

출력: 의학 차트 카드 스타일의 자연어 프로필.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---------------- 서열 계산 ----------------

def compute_rankings(chars):
    """전체 30명에 대한 지표별 서열. 반환: {id: {metric: (rank, total, value)}}"""
    n = len(chars)
    metrics = {
        "height": [(c["id"], c["body"]["height_cm"]) for c in chars],
        "iq": [(c["id"], c["identity"]["cognitive"]["iq"]) for c in chars],
        "ace": [(c["id"], c["memory"]["ace"]["total"]) for c in chars],
        "bmi": [(c["id"], c["body"]["body_composition"]["bmi"]) for c in chars],
        "digital": [(c["id"], c["identity"]["impulse_footprint"]["A_impulse"]["digital_hours"]) for c in chars],
        "sleep": [(c["id"], c["body"]["sleep"]["duration_hours"]) for c in chars],
        "grip": [(c["id"], c["body"]["body_composition"]["grip_kg"]) for c in chars],
    }
    out = {c["id"]: {} for c in chars}
    for name, data in metrics.items():
        data.sort(key=lambda x: -x[1])  # 내림차순
        for rank, (cid, val) in enumerate(data, 1):
            out[cid][name] = (rank, n, val)
    return out


def rank_bar(rank, total):
    """상위 N% 표기. '상위 20%', '하위 30%' 등."""
    pct = (rank / total) * 100
    if pct <= 20:
        return f"상위 {int(pct)}%"
    if pct <= 40:
        return f"상위 {int(pct)}%"
    if pct <= 60:
        return "중위권"
    if pct <= 80:
        return f"하위 {100 - int(pct)}%"
    return f"하위 {100 - int(pct)}%"


def bmi_label(bmi):
    if bmi < 18.5:
        return "저체중"
    if bmi < 23:
        return "정상"
    if bmi < 25:
        return "과체중 경계"
    if bmi < 30:
        return "과체중"
    return "비만"


def iq_label(iq):
    if iq < 70:
        return "경계선 이하"
    if iq < 85:
        return "평균 하"
    if iq < 115:
        return "평균"
    if iq < 130:
        return "평균 상"
    if iq < 145:
        return "우수"
    return "최상위"


def sleep_label(h):
    if h < 5:
        return "심각한 수면 부족"
    if h < 6.5:
        return "부족"
    if h < 8:
        return "평균"
    if h < 9:
        return "충분"
    return "과다"


# ---------------- 유틸 ----------------

def join_or_none(items, sep=", ", none_text="없음"):
    if not items:
        return none_text
    return sep.join(items)


def indent(text, level=1):
    prefix = "    " * level
    return "\n".join(prefix + line for line in text.split("\n"))


# ---------------- 섹션 렌더러 ----------------

def render_header(c):
    sex_k = "남" if c["sex"] == "M" else "여"
    region = c["korea"]["region_voice"]["birth_region"]
    labels = " · ".join(c["post_hoc_label"])
    bar = "━" * 60
    return (
        f"{bar}\n"
        f"  #{c['id']:02d}  ·  {sex_k}  ·  20세  ·  {region} 출생\n"
        f"  {labels}\n"
        f"{bar}"
    )


def render_rankings(c, rk):
    """서열표 — 30명 중."""
    r = rk[c["id"]]
    sex_rank = c["body"]["face_attractiveness"]["sex_rank"]
    sex_label = "남" if c["sex"] == "M" else "여"

    lines = ["┌─ 서열표 (30명 중) ─────────────────────────────────────┐"]
    lines.append(f"│  키        {r['height'][2]:.1f}cm    {r['height'][0]:2d}/30위  ({rank_bar(r['height'][0], 30)})")
    lines.append(f"│  IQ        {r['iq'][2]}       {r['iq'][0]:2d}/30위  ({iq_label(r['iq'][2])})")
    lines.append(f"│  매력      {c['body']['face_attractiveness']['absolute_score']}/10      {sex_label} {sex_rank}/15위")
    lines.append(f"│  ACE 누적  {r['ace'][2]}점      {r['ace'][0]:2d}/30위  (높을수록 상위)")
    lines.append(f"│  BMI       {r['bmi'][2]}    {r['bmi'][0]:2d}/30위  ({bmi_label(r['bmi'][2])})")
    lines.append(f"│  악력      {r['grip'][2]}kg    {r['grip'][0]:2d}/30위")
    lines.append(f"│  수면      {r['sleep'][2]}h    {r['sleep'][0]:2d}/30위  ({sleep_label(r['sleep'][2])})")
    lines.append(f"│  디지털    {r['digital'][2]}h/일  {r['digital'][0]:2d}/30위")
    lines.append("└────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_body(c):
    b = c["body"]
    bc = b["body_composition"]
    ff = b["face_features"]
    sh = b["skin_hair"]
    sc = b["sex_characteristics"]
    si = b["self_image"]
    vo = b["vocal"]
    se = b["sensory"]

    lines = ["■ 신체"]
    lines.append(f"  키 {b['height_cm']:.1f}cm, 체중 비율 BMI {bc['bmi']} ({bmi_label(bc['bmi'])}), 근육 {bc['muscle_mass']}, 악력 {bc['grip_kg']}kg.")
    whr_shr = bc.get('shr') or bc.get('whr')
    whr_shr_label = "어깨-엉덩이비" if c['sex'] == 'M' else "허리-엉덩이비"
    lines.append(f"  허리 {bc['waist_cm']}cm, {whr_shr_label} {whr_shr}.")

    lines.append(f"  얼굴: {ff['shape']}, {ff['eyelid']}, 콧날 {ff['nose_bridge']}, 치아 {ff['teeth']}, 비대칭 {ff['asymmetry_mm']}mm.")
    if ff["marks"]:
        lines.append(f"  얼굴의 표식: {', '.join(ff['marks'])}.")
    if ff["early_hair_recession"] != "없음":
        lines.append(f"  탈모 진행: {ff['early_hair_recession']}.")

    lines.append(f"  피부 {sh['skin_type']}, 톤 {sh['skin_tone']}, 머릿결 {sh['hair_texture']} ({sh['hair_density']}).")
    if sh["scars"]:
        lines.append(f"  흉터: {', '.join(sh['scars'])}.")
    if sh["tattoos"] != "없음":
        lines.append(f"  문신: {sh['tattoos']}.")

    lines.append(f"  목소리: {vo['pitch_hz']}Hz, 볼륨 {vo['volume']}, 말속도 {vo['speech_rate']}.")
    if vo["quirks"]:
        lines.append(f"  음성 특이점: {', '.join(vo['quirks'])}.")
    lines.append(f"  시력: {se['visual_acuity']}, {se['correction']}.")

    lines.append("")
    lines.append("  성적 신체:")
    if c["sex"] == "M":
        lines.append(f"    음경 발기 길이 {sc['penis_length_cm']}cm, 둘레 {sc['penis_girth_cm']}cm. {sc['foreskin']}.")
        lines.append(f"    형태 특이점: {', '.join(sc['shape_notes'])}. 발기 기능 {sc['erectile_function']}.")
    else:
        lines.append(f"    가슴 컵 {sc['breast_cup']} ({sc['breast_asymmetry']}).")
        lines.append(f"    유두/유륜 특징: {', '.join(sc['nipple_features'])}.")
        lines.append(f"    소음순 {sc['labia_minora']}, 외음부 색 {sc['vulva_color']}.")
        lines.append(f"    생리 {sc['menstrual']['cycle_regularity']}, 통증 {sc['menstrual']['pain_severity']}.")
    hair = sc["body_hair"]
    lines.append(f"    체모: 음모 {hair['pubic']}, 다리 {hair['leg']}, 가슴 {hair['chest']}, 겨드랑이 {hair['underarm']}.")
    lines.append(f"    체취 수준: {sc['body_odor']}.")

    lines.append("")
    lines.append("  자기 이미지:")
    lines.append(f"    얼굴 만족도 {si['face']}, 체형 만족도 {si['body']}, 성기 자기 인식 {si['genital']}.")
    if si["focused_concern"]:
        lines.append(f"    거울 앞에서 집중하는 영역: {', '.join(si['focused_concern'])}.")
    else:
        lines.append("    특별히 집중하는 신체 영역 없음.")

    return "\n".join(lines)


def render_chronic(c):
    ch = c["body"]["chronic_health"]
    lines = ["■ 개인 병력"]
    if not ch:
        lines.append("  만성 질환 기록 없음.")
    else:
        for x in ch:
            lines.append(f"  · {x['condition']} — {x['severity']}")
    sl = c["body"]["sleep"]
    lines.append("")
    lines.append(f"  수면: 평균 {sl['duration_hours']}시간, {sl['chronotype']}, 현재 상태 {sl['current_debt']}, 불면 {sl['insomnia']}.")
    return "\n".join(lines)


def render_family(c):
    ff = c["memory"]["formative_family"]
    pv = c["memory"]["parent_voice"]
    pl = c["memory"]["parental_loss"]

    lines = ["■ 가정·성장 배경"]
    lines.append(f"  SES {ff['ses_quintile']}. 아버지 {ff['father_occupation']}, 어머니 {ff['mother_employment']}. {ff['sibling_structure']}.")
    lines.append(f"  유년기 경제 상태: {ff['economic_stability']}. 거주 이동 {ff['residence_changes']}.")
    lines.append(f"  가정 정서 분위기: {ff['emotional_climate']}.")
    lines.append("")
    lines.append(f"  가족 구조: {pl['status']}.")
    if pl.get("event_age"):
        lines.append(f"    사건 시기: {pl['event_age']}. 이후 양육자: {pl['caregiver_after']}.")
        lines.append(f"    부재 부모 접촉: {pl['contact_with_absent']}. 설명 방식: {pl['narrative']}.")
    lines.append("")
    lines.append(f"  어머니 패턴: {pv['mother_pattern']}")
    lines.append(f"  아버지 패턴: {pv['father_pattern']}")
    lines.append(f"  부모 일관성: {pv['consistency']}")
    lines.append(f"  세대 간 압력: {pv['intergenerational_pressure']}. 전달 방식: {pv['transmission']}.")
    return "\n".join(lines)


def render_trauma(c):
    m = c["memory"]
    ace = m["ace"]
    csa = m["csa"]
    bul = m["bullying"]
    att = m["attachment"]
    reflex = m["default_reflex"]
    sent = m["embedded_sentences"]
    react = m["embedded_reactions"]
    trig = m["trauma_trigger"]

    lines = ["■ 트라우마·기억"]
    lines.append(f"  ACE(부정적 아동기 경험) 누적: {ace['total']}점.")
    if ace["categories"]:
        lines.append(f"  카테고리: {', '.join(ace['categories'])}.")
        if ace["primary"]:
            lines.append(f"  주요 양상: {ace['primary']}.")
    else:
        lines.append("  구체적 카테고리 기록 없음.")

    lines.append("")
    if csa:
        lines.append(f"  ⚠ 아동기 성학대 기록:")
        lines.append(f"    발생 시기: {csa['first_age']}")
        lines.append(f"    가해자: {csa['perpetrator']}")
        lines.append(f"    빈도: {csa['frequency']}")
        lines.append(f"    강도: {csa['physical_intensity']}")
        lines.append(f"    주 감각 채널: {csa['primary_sensory_channel']}")
        lines.append(f"    서사 처리: {csa['narrative_processing']}")
        lines.append(f"    공개 여부: {csa['disclosure']}")
    else:
        lines.append("  아동기 성학대 기록 없음.")

    lines.append("")
    lines.append(f"  학교 폭력 이력:")
    lines.append(f"    피해: {bul['victim']} / 가해: {bul['perpetrator']} / 방관: {bul['bystander']}")
    if bul.get("form"):
        lines.append(f"    주된 형태: {bul['form']}. 정점 시기: {bul['peak_period']}. 역할 전환: {bul['dual_role']}.")
    else:
        lines.append(f"    역할 전환: {bul['dual_role']}.")

    lines.append("")
    lines.append(f"  애착 유형: {att['style']} (불안 {att['anxiety']}/5, 회피 {att['avoidance']}/5, 임계 {att['threshold']}).")
    lines.append(f"  기본 위협 반사: {reflex['primary']}" + (f" (+{reflex['secondary']})" if reflex['secondary'] != '없음' else ''))
    lines.append(f"    임계: {reflex['threshold']}. 폴리바갈 기본: {reflex['polyvagal']}.")
    if reflex.get("signature"):
        lines.append(f"    외부 관찰 신호: {reflex['signature']}.")

    if sent:
        lines.append("")
        lines.append("  내면에 박힌 문장 (특정 상황에서 자동 재생):")
        for s in sent:
            lines.append(f"    · {s['speaker']}의 \"{s['message_type']}\" — {s['trigger']}에서 재생 ({s['consciousness']})")

    if react:
        lines.append("")
        lines.append("  변곡점이 된 타인의 반응:")
        for r in react:
            lines.append(f"    · {r['age']}, {r['reactor']}이(가) {r['target']}에 대해 {r['reaction']}")
            lines.append(f"      사건 전 자기 이미지: {r['self_image_before']} → 균열: {r['rupture_depth']}")
            lines.append(f"      처리: {r['processing']}")

    if trig:
        lines.append("")
        lines.append("  트라우마 트리거 채널:")
        for t in trig:
            lines.append(f"    · {t['channel']} — 반응 {t['intensity']}, 인지 상태: {t['consciousness']}")

    return "\n".join(lines)


def render_cognitive(c, rk):
    cog = c["identity"]["cognitive"]
    r_iq = rk[c["id"]]["iq"]
    lines = ["■ 인지 능력"]
    lines.append(f"  추정 IQ {cog['iq']} ({iq_label(cog['iq'])}, 30명 중 {r_iq[0]}위).")
    lines.append(f"  우세 결: {cog['strength']}. 약한 결: {cog['weakness']}.")
    lines.append(f"  학업 수행: {cog['academic_performance']}. 메타인지: {cog['metacognition']}.")
    lines.append(f"  사고 스타일: {cog['thinking_style']}. 지적 호기심: {cog['curiosity']}.")
    return "\n".join(lines)


def render_sexuality(c):
    s = c["identity"]["sexuality"]
    fn = s["function"]
    lines = ["■ 성·욕망"]
    lines.append(f"  지향: {s['orientation']}.")
    if s["out_status"] != "해당 없음 (이성애)":
        lines.append(f"  공개 상태: {s['out_status']}.")
    lines.append(f"  경험: {s['experience']}. 첫 경험 시기: {s['first_age']}.")
    lines.append(f"  욕망 강도: {s['desire_intensity']}. 욕망의 결: {s['desire_grain']}.")
    if s["taboos"]:
        lines.append(f"  내면 금기: {', '.join(s['taboos'])}.")
    lines.append(f"  성 기능: 각성 {fn['arousal']}, 수행 {fn['performance']}, 만족 {fn['satisfaction']}.")
    lines.append(f"  동의 이력: {s['consent_marker']}.")
    return "\n".join(lines)


def render_impulse(c, rk):
    imp = c["identity"]["impulse_footprint"]
    a = imp["A_impulse"]
    b = imp["B_footprint"]
    r_dig = rk[c["id"]]["digital"]
    subs = a["substances"]

    lines = ["■ 충동·중독"]
    lines.append(f"  스마트폰 하루 {a['digital_hours']}시간 (30명 중 {r_dig[0]}위), 통제 수준: {a['compulsion']}.")
    lines.append(f"  주 플랫폼: {', '.join(a['platforms'])}.")
    lines.append(f"  음주 {subs['alcohol']}, 흡연 {subs['smoking']}, 카페인 {subs['caffeine']}, 기타 {subs['other']}.")
    lines.append(f"  식이 패턴: {a['eating_impulse']}. 충동 통제: {a['impulse_control']}. 보상 민감도: {a['reward_sensitivity']}.")
    lines.append(f"  스트레스 회피 경로: {a['escape_default']}. 자기 인식: {a['self_awareness']}.")

    lines.append("")
    lines.append("■ 사적 디지털 발자국")
    if b["games"]:
        lines.append(f"  자주 하는 게임: {', '.join(b['games'])}")
    lines.append(f"  일기·메모 톤: {b['journal_tone']}")
    lines.append(f"  SNS 공적 얼굴: {b['sns_public_face']}")
    lines.append(f"  공적/사적 자기의 간극: {b['private_vs_public_gap']}")
    if b["communities"]:
        lines.append(f"  자주 가는 커뮤니티: {', '.join(b['communities'])}")
    lines.append(f"  플레이리스트: {b['playlist']}")
    if b["album_theme"]:
        lines.append(f"  사진첩 테마: {', '.join(b['album_theme'])}")
    if b["recent_search"]:
        lines.append(f"  최근 검색: {', '.join(b['recent_search'])}")
    if b["bookmarks"]:
        lines.append(f"  북마크·구독: {', '.join(b['bookmarks'])}")

    return "\n".join(lines)


def render_korea(c):
    k = c["korea"]
    ed = k["education"]
    ap = k["appearance_experience"]
    rv = k["region_voice"]

    lines = ["■ 한국 사회 맥락"]
    lines.append(f"  학력 궤적: {ed['high_school']} → 수능 {ed['suneung_grade']} → {ed['university_tier']} ({ed['major']}).")
    lines.append(f"    재수 경험: {ed['retake']}. 사교육 강도: {ed['private_education']}.")
    lines.append(f"    학업 자기 인식: {ed['academic_self_concept']}. 부모 압력: {ed['parental_pressure']}.")
    lines.append("")
    lines.append(f"  외모 차별 경험: {ap['discrimination_frequency']}.")
    if ap["discrimination_domain"]:
        lines.append(f"    차별 영역: {', '.join(ap['discrimination_domain'])}.")
    lines.append(f"    관리 수준: {ap['management_level']}. 성형 이력: {ap['cosmetic_surgery']}. 다이어트 이력: {ap['diet_history']}.")
    lines.append(f"    Lookism 내면화: {ap['lookism_internalization']}. 외모 자본 인식: {ap['capital_awareness']}.")
    lines.append("")
    lines.append(f"  출생/거주: {rv['birth_region']} → {rv['residence_match']}.")
    lines.append(f"  억양: {rv['accent_intensity']} ({rv['accent_self_conscious']}).")
    lines.append(f"  가족 정치: {rv['family_politics']} → 본인: {rv['personal_politics']}.")
    lines.append(f"  가족 종교: {rv['family_religion']} → 본인: {rv['personal_religion']}.")
    lines.append(f"  지역 차별 경험: {rv['regional_discrimination']}.")
    return "\n".join(lines)


def render_summary(c, rk):
    """rule-based 한 문단 자연어 요약."""
    r = rk[c["id"]]
    sex_k = "남" if c["sex"] == "M" else "여"
    ace = c["memory"]["ace"]["total"]
    iq = c["identity"]["cognitive"]["iq"]
    att = c["memory"]["attachment"]["style"]
    reflex = c["memory"]["default_reflex"]["primary"]
    tier = c["korea"]["education"]["university_tier"]
    self_concept = c["korea"]["education"]["academic_self_concept"]

    beats = []
    beats.append(f"20세 {sex_k}, 키 {r['height'][2]:.0f}cm, IQ {iq}({iq_label(iq)})")
    beats.append(f"ACE {ace}점")
    beats.append(f"애착은 {att}")
    beats.append(f"위협 반사는 {reflex}")
    beats.append(f"현재 {tier}")
    beats.append(f"학업 자기 인식 {self_concept}")

    extras = []
    if c["memory"]["csa"]:
        extras.append("아동기 성학대 과거")
    if ace >= 4:
        extras.append("고ACE")
    if iq >= 130:
        extras.append("최상위 인지")
    if "임상" in c["identity"]["impulse_footprint"]["A_impulse"]["compulsion"]:
        extras.append("디지털 임상 수준")
    if c["identity"]["sexuality"]["desire_intensity"] == "거의 없음 (무성애 또는 억제)":
        extras.append("욕망 억제")
    if "자살" in c["identity"]["impulse_footprint"]["B_footprint"]["journal_tone"]:
        extras.append("일기에 자살 사고")
    if "스토킹" in " ".join(c["identity"]["impulse_footprint"]["B_footprint"]["recent_search"]):
        extras.append("스토킹 검색 이력")
    concerns = c["body"]["self_image"]["focused_concern"]
    if len(concerns) >= 3:
        extras.append(f"자기 의식 집중점 {len(concerns)}개")

    summary = " · ".join(beats) + "."
    if extras:
        summary += " 특이 신호: " + ", ".join(extras) + "."

    return "■ 종합 한 줄\n  " + summary


# ---------------- 스토리화 섹션 (rule-based narrative) ----------------

def render_narrative(c, rk):
    """조건부 문장 템플릿으로 한 문단 스토리 조립.
    규칙: 필드 값을 읽고 그에 맞는 문장을 이어 붙임. LLM 호출 없음. 토큰 0.
    """
    r = rk[c["id"]]
    sex_k = "남성" if c["sex"] == "M" else "여성"
    b = c["body"]
    m = c["memory"]
    ident = c["identity"]
    kor = c["korea"]

    sentences = []

    # --- 도입: 외적 인상 ---
    height = b["height_cm"]
    face_score = b["face_attractiveness"]["absolute_score"]
    face_rank = b["face_attractiveness"]["sex_rank"]
    bmi = b["body_composition"]["bmi"]
    bmi_desc = bmi_label(bmi)

    if face_rank <= 3:
        face_desc = f"동성 15명 중 {face_rank}위로 꼽히는 상위권 외모"
    elif face_rank <= 5:
        face_desc = f"상위권({face_rank}/15)의 눈에 띄는 외모"
    elif face_rank <= 10:
        face_desc = f"중간 정도({face_rank}/15)의 외모"
    else:
        face_desc = f"외모 {face_rank}/15위, 눈에 띄지 않는 편"

    sentences.append(
        f"20세 {sex_k}. 키 {height:.0f}cm (전체 {r['height'][0]}/30위), "
        f"{bmi_desc} 체형, {face_desc}."
    )

    # --- 가정 배경 ---
    ses = m["formative_family"]["ses_quintile"]
    stability = m["formative_family"]["economic_stability"]
    climate = m["formative_family"]["emotional_climate"]
    pl_status = m["parental_loss"]["status"]
    mother = m["parent_voice"]["mother_pattern"]
    father = m["parent_voice"]["father_pattern"]

    if "1분위" in ses or "2분위" in ses or "만성 빈곤" in stability:
        econ_line = f"{ses} 가정에서 {stability} 상태로 자람"
    elif "5분위" in ses or "풍요" in stability:
        econ_line = f"{ses}의 {stability}한 환경에서 자람"
    else:
        econ_line = f"{ses} 가정, 경제는 {stability}"

    family_line = f"{econ_line}. {pl_status}"
    if "이혼" in pl_status or "사별" in pl_status or "사실상 부재" in pl_status:
        if m["parental_loss"].get("event_age"):
            family_line += f" ({m['parental_loss']['event_age']} 시기)"
    sentences.append(family_line + ".")

    parent_line = f"어머니는 {mother}, 아버지는 {father}"
    if climate in ("정서 표현 전면 금기", "정서 표현 금기 (특정 감정만)"):
        parent_line += f". 가정 분위기는 {climate} — 속마음을 꺼내는 법을 배우지 못함"
    elif climate == "예측 불가 (상황별 폭발)":
        parent_line += f". 가정 분위기는 {climate} — 부모 기분을 읽는 것이 생존 기술이 됨"
    elif climate == "공허·무관심":
        parent_line += f". 가정은 공허·무관심 — 혼자 자란 감각이 디폴트"
    elif climate == "정서 표현 자유":
        parent_line += ". 정서 표현은 자유로운 편"
    sentences.append(parent_line + ".")

    # --- 트라우마 ---
    ace_n = m["ace"]["total"]
    if m["csa"]:
        csa = m["csa"]
        csa_line = (
            f"{csa['first_age']}에 {csa['perpetrator']}으로부터 {csa['frequency']}의 성학대를 경험. "
            f"주된 감각 채널은 {csa['primary_sensory_channel']}. "
            f"사건은 {csa['narrative_processing']} 상태이며, {csa['disclosure']}"
        )
        sentences.append(csa_line + ".")

    if ace_n >= 4:
        sentences.append(
            f"ACE 누적 {ace_n}점(30명 중 {r['ace'][0]}위)으로 아동기 부정 경험이 극단에 가깝다."
        )
    elif ace_n >= 2:
        cats = ", ".join(m["ace"]["categories"][:3])
        sentences.append(f"ACE {ace_n}점 — {cats} 경험.")

    bul = m["bullying"]
    if bul["victim"] not in ("없음",):
        if bul["perpetrator"] not in ("없음",):
            sentences.append(f"학교 폭력은 {bul['victim']} 피해 + {bul['perpetrator']} 가해의 복합 역할이었고, 역할 전환 양상은 {bul['dual_role']}.")
        else:
            sentences.append(f"학교에서 {bul['victim']} 피해를 겪음 ({bul['form'] or '형태 불명'}).")

    # --- 인지 ---
    cog = ident["cognitive"]
    iq = cog["iq"]
    iq_rank = r["iq"][0]
    meta = cog["metacognition"]
    curiosity = cog["curiosity"]

    if iq >= 130:
        iq_line = f"인지 능력은 상위권(IQ {iq}, 30명 중 {iq_rank}위)"
    elif iq >= 115:
        iq_line = f"평균 이상의 인지 능력(IQ {iq})"
    elif iq >= 85:
        iq_line = f"평균 범위의 인지 능력(IQ {iq})"
    else:
        iq_line = f"평균 이하의 인지 능력(IQ {iq})"

    if "과대" in meta:
        iq_line += "이지만 자기 능력을 실제보다 높게 평가하는 경향"
    elif "과소" in meta:
        iq_line += "이지만 자기 능력을 실제보다 낮게 평가해 멈추는 경향"
    elif "강함" in meta:
        iq_line += "이며 메타인지가 강해 자기 사고 과정을 추적함"
    elif "평가 불가" in meta:
        iq_line += "이지만 자기를 객관화하는 감각이 부재"
    sentences.append(iq_line + ".")

    # --- 학력 ---
    ed = kor["education"]
    tier = ed["university_tier"]
    self_concept = ed["academic_self_concept"]
    grade = ed["suneung_grade"]
    retake = ed["retake"]

    edu_line = f"학력 궤적은 {ed['high_school']} → 수능 {grade} → {tier} ({ed['major']})"
    if retake != "재수 없음":
        edu_line += f", {retake}"
    sentences.append(edu_line + ".")

    if "패배자" in self_concept:
        sentences.append("학업 자기 인식은 패배자 정체성으로 굳어진 상태.")
    elif "엘리트" in self_concept:
        sentences.append("학업에서 자기를 엘리트로 정체화하고 있음.")
    elif "낮음" in self_concept or "체념" in self_concept:
        sentences.append("학업에 대해서는 회피·체념으로 물러서 있음.")

    # --- 성·욕망 ---
    sx = ident["sexuality"]
    orient = sx["orientation"]
    exp = sx["experience"]
    desire = sx["desire_intensity"]
    grain = sx["desire_grain"]
    fn = sx["function"]

    sex_line = ""
    if "이성애" not in orient or "우세" in orient:
        sex_line = f"성적 지향은 {orient}"
        if sx["out_status"] not in ("해당 없음 (이성애)", "해당 없음"):
            sex_line += f" ({sx['out_status']} 상태)"
        sex_line += ". "

    if "없음" in exp:
        sex_line += f"성 경험은 {exp}"
    else:
        sex_line += f"경험은 {exp}"

    if "거의 없음" in desire:
        sex_line += "이며 욕망은 거의 없거나 억제된 상태"
    elif "압도적" in desire:
        sex_line += "이고 욕망은 압도적 수준"
    elif "높음" in desire:
        sex_line += "이고 욕망은 높은 편"
    sex_line += f", 결은 {grain}."
    sentences.append(sex_line)

    if "심각한 어려움" in fn["performance"] or "불만" in fn["satisfaction"]:
        sentences.append(
            f"성 기능은 각성 {fn['arousal']}, 수행 {fn['performance']}, 만족 {fn['satisfaction']}으로 결이 꼬여 있다."
        )

    if sx["taboos"]:
        taboo_count = len(sx["taboos"])
        sentences.append(
            f"내면의 성 금기가 {taboo_count}개 박혀 있음: {', '.join(sx['taboos'])}."
        )

    # --- 애착·반사 ---
    att = m["attachment"]
    reflex = m["default_reflex"]
    att_style = att["style"]
    att_line = f"애착 유형은 {att_style}"
    if att["anxiety"] >= 4:
        att_line += f", 불안 차원이 매우 높음({att['anxiety']}/5)"
    if att["avoidance"] >= 4:
        att_line += f", 회피 차원이 매우 높음({att['avoidance']}/5)"
    att_line += f". 위협 감지 시 기본 반사는 {reflex['primary']}, {reflex['polyvagal']} 상태가 디폴트."
    sentences.append(att_line)

    # --- 충동·디지털 ---
    impA = ident["impulse_footprint"]["A_impulse"]
    impB = ident["impulse_footprint"]["B_footprint"]
    digital_h = impA["digital_hours"]
    compulsion = impA["compulsion"]
    escape = impA["escape_default"]

    dig_line = f"스마트폰 하루 {digital_h}시간"
    if "임상" in compulsion:
        dig_line += " (임상 수준, 일상 기능 저하)"
    elif "매우 높음" in compulsion:
        dig_line += " (10분마다 확인 수준)"
    dig_line += f", 스트레스 회피 경로는 {escape}."
    sentences.append(dig_line)

    # 발자국 중 위험 신호
    warnings = []
    if "자살" in impB["journal_tone"]:
        warnings.append("일기 또는 메모에 자살 사고·유서 초안")
    if "자학" in impB["journal_tone"]:
        warnings.append("자학·자책 메모")
    if any("자살" in s for s in impB["recent_search"]):
        warnings.append("최근 자살 방법 검색 흔적")
    if any("스토킹" in s for s in impB["recent_search"]):
        warnings.append("특정 인물 스토킹성 검색")
    if any("자해흔" in t for t in impB["album_theme"]):
        warnings.append("사진첩에 자해흔 비밀 보관")
    if "부계정 운영" in impB["private_vs_public_gap"]:
        warnings.append("본계정 페르소나 아래 부계정에 속마음 분리 운영")
    elif "강한 이중성" in impB["private_vs_public_gap"]:
        warnings.append("공적 자기와 속마음이 완전히 다름")
    if warnings:
        sentences.append("위험·격차 신호: " + "; ".join(warnings) + ".")

    # --- 박힌 문장 ---
    if m["embedded_sentences"]:
        s_count = len(m["embedded_sentences"])
        first = m["embedded_sentences"][0]
        sentences.append(
            f"내면에는 {s_count}개의 박힌 문장이 있으며 특히 {first['speaker']}의 '{first['message_type']}'이 "
            f"{first['trigger']}에서 자동 재생됨."
        )

    # --- 박힌 반응 (M11) ---
    if m["embedded_reactions"]:
        reaction = m["embedded_reactions"][0]
        sentences.append(
            f"변곡점이 된 사건: {reaction['age']}에 {reaction['reactor']}이(가) {reaction['target']}에 대해 "
            f"{reaction['reaction']}. 사건 전 자기 이미지는 {reaction['self_image_before']}이었고 "
            f"{reaction['rupture_depth']} 수준의 흔적이 남음."
        )

    # --- 한국 맥락 ---
    rv = kor["region_voice"]
    ap = kor["appearance_experience"]

    if rv["regional_discrimination"] not in ("없음 (해당 안 됨·기억 없음)", "농담 수준"):
        sentences.append(f"출신 지역({rv['birth_region']})으로 인한 차별 경험이 {rv['regional_discrimination']}.")

    if ap["discrimination_frequency"] in ("반복적 (월 단위)", "만성 (일상 차별)"):
        sentences.append(f"외모 관련 차별 경험은 {ap['discrimination_frequency']} 수준으로, 주로 {', '.join(ap['discrimination_domain'][:3])}에서 일어남.")

    if ap["cosmetic_surgery"] not in ("없음",):
        sentences.append(f"성형 이력은 {ap['cosmetic_surgery']}.")

    # --- 겉/속 격차 해석 ---
    surface = []
    depth = []
    if face_rank <= 5:
        surface.append(f"외모 {face_rank}위")
    if iq >= 125:
        surface.append(f"IQ {iq}")
    if height >= 178 and c["sex"] == "M":
        surface.append(f"키 {height:.0f}cm")
    if height >= 167 and c["sex"] == "F":
        surface.append(f"키 {height:.0f}cm")
    if "SKY" in tier or "성균관" in tier:
        surface.append(tier.split(" ")[0] if "SKY" in tier else "상위권 대학")

    if ace_n >= 4:
        depth.append("고ACE")
    if m["csa"]:
        depth.append("성학대 과거")
    if "패배자" in self_concept:
        depth.append("학업 패배자 정체성")
    if "심각한 어려움" in fn["performance"]:
        depth.append("성기능 심각 어려움")
    if any("자살" in s for s in impB["recent_search"]) or "자살" in impB["journal_tone"]:
        depth.append("자살 검색/사고")
    if any("자해흔" in t for t in impB["album_theme"]):
        depth.append("자해흔 비밀 사진")

    if surface and depth:
        sentences.append(
            f"겉(↑{' · '.join(surface)})과 속(↓{' · '.join(depth)}) 사이의 격차가 이 캐릭터의 작동 핵심."
        )

    # 조립
    narrative = "\n  ".join(sentences)
    return "■ 스토리\n  " + narrative


# ---------------- 카드 조립 ----------------

def make_card(c, rk):
    parts = [
        render_header(c),
        "",
        render_rankings(c, rk),
        "",
        render_body(c),
        "",
        render_chronic(c),
        "",
        render_family(c),
        "",
        render_trauma(c),
        "",
        render_cognitive(c, rk),
        "",
        render_sexuality(c),
        "",
        render_impulse(c, rk),
        "",
        render_korea(c),
        "",
        render_summary(c, rk),
        "",
        render_narrative(c, rk),
        "",
    ]
    return "\n".join(parts)


# ---------------- main ----------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/card.py <seed> <id1> [id2 ...|all]", file=sys.stderr)
        sys.exit(1)
    seed = int(sys.argv[1])
    ids_arg = sys.argv[2:]

    data = json.loads((ROOT / "runs" / f"seed_{seed:03d}.json").read_text(encoding="utf-8"))
    chars = data["characters"]
    rk = compute_rankings(chars)
    by_id = {c["id"]: c for c in chars}

    if ids_arg == ["all"]:
        target_ids = [c["id"] for c in chars]
    else:
        target_ids = [int(x) for x in ids_arg]

    for cid in target_ids:
        c = by_id.get(cid)
        if not c:
            print(f"id={cid} 없음", file=sys.stderr)
            continue
        print(make_card(c, rk))
        print()


if __name__ == "__main__":
    main()
