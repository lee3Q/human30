#!/usr/bin/env python3
"""30p 시드 굴림 — 표준 라이브러리만 사용 (외부 패키지 0).

Usage:
    python3 generate_seed.py <seed_number>

입력: ../tables/{body,memory,identity,korea}.json + ../data/personas.json
출력: ../runs/seed_{NNN}.json

재현성: random.seed(N)으로 비트 단위 고정. 같은 시드 = 완전히 같은 결과물.
공급망 방어: stdlib만 사용 (json, random, math, sys, pathlib, datetime).
"""

import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLES_DIR = ROOT / "tables"
RUNS_DIR = ROOT / "runs"
DATA_DIR = ROOT / "data"


# ---------------- sampling primitives ----------------

def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def rnorm(mean, sd, clip_range=None, ndigits=1):
    v = random.gauss(mean, sd)
    if clip_range:
        v = clamp(v, clip_range[0], clip_range[1])
    return round(v, ndigits)


def rcat(values, weights=None):
    if not weights:
        return random.choice(values)
    return random.choices(values, weights=weights, k=1)[0]


def rpoisson(lam):
    """Knuth's algorithm — stdlib only."""
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= L:
            return k - 1


def pick_weights(spec, sex=None):
    if sex and f"weights_{sex}" in spec:
        return spec[f"weights_{sex}"]
    return spec.get("weights")


def sample_pool(pool, n, exclude=None):
    if exclude:
        pool = [x for x in pool if x not in exclude]
    n = max(0, min(n, len(pool)))
    if n == 0:
        return []
    return random.sample(pool, n)


# ---------------- body layer ----------------

def roll_body(tables, sex):
    b = tables["body"]["tables"]
    out = {}

    # B1 height
    h = b["B1_height"]["distributions"][sex]
    out["height_cm"] = rnorm(h["mean"], h["sd"], h["clip"])

    # B2 face attractiveness (rank filled post-hoc)
    b2 = b["B2_face_attractiveness"]["distributions"]["absolute_score"]
    score = int(round(clamp(random.gauss(b2["mean"], b2["sd"]), b2["clip"][0], b2["clip"][1])))
    out["face_attractiveness"] = {"absolute_score": score, "sex_rank": None}

    # B3 body composition
    b3 = b["B3_body_composition"]["fields"]
    bmi_s = b3["bmi"][sex]
    grip_s = b3["grip_strength_kg"][sex]
    waist_s = b3["waist_cm"][sex]
    bc = {
        "bmi": rnorm(bmi_s["mean"], bmi_s["sd"], bmi_s["clip"]),
        "muscle_mass": rcat(b3["muscle_mass"]["levels"], pick_weights(b3["muscle_mass"], sex)),
        "grip_kg": int(round(rnorm(grip_s["mean"], grip_s["sd"], grip_s["clip"], 0))),
        "waist_cm": int(round(rnorm(waist_s["mean"], waist_s["sd"], waist_s["clip"], 0))),
    }
    if sex == "F":
        whr = b3["whr_female"]
        bc["whr"] = rnorm(whr["mean"], whr["sd"], whr["clip"], 2)
    else:
        shr = b3["shr_male"]
        bc["shr"] = rnorm(shr["mean"], shr["sd"], shr["clip"], 2)
    out["body_composition"] = bc

    # B4 face features
    b4 = b["B4_face_features"]["fields"]
    marks_n = rpoisson(b4["marks"]["count_dist"]["lambda"])
    out["face_features"] = {
        "shape": rcat(b4["face_shape"]["values"], b4["face_shape"]["weights"]),
        "eyelid": rcat(b4["eyelid"]["values"], b4["eyelid"]["weights"]),
        "nose_bridge": rcat(b4["nose_bridge"]["levels"], b4["nose_bridge"]["weights"]),
        "teeth": rcat(b4["teeth"]["values"], b4["teeth"]["weights"]),
        "asymmetry_mm": rnorm(b4["asymmetry_mm"]["mean"], b4["asymmetry_mm"]["sd"], b4["asymmetry_mm"]["clip"], 1),
        "marks": sample_pool(b4["marks"]["pool"], marks_n, exclude={"없음"}),
        "early_hair_recession": rcat(b4["early_hair_recession"]["values"], pick_weights(b4["early_hair_recession"], sex)),
    }

    # B5 sex characteristics
    b5 = b["B5_sex_characteristics"]
    sc = {}
    if sex == "M":
        fm = b5["fields_M"]
        sc["penis_length_cm"] = rnorm(fm["penis_length_erect_cm"]["mean"], fm["penis_length_erect_cm"]["sd"], fm["penis_length_erect_cm"]["clip"], 1)
        sc["penis_girth_cm"] = rnorm(fm["penis_girth_cm"]["mean"], fm["penis_girth_cm"]["sd"], fm["penis_girth_cm"]["clip"], 1)
        sc["foreskin"] = rcat(fm["foreskin"]["values"], fm["foreskin"]["weights"])
        shape_cnt_spec = fm["penis_shape_notes"]["count_dist"]
        n_shapes = rcat(shape_cnt_spec["values"], shape_cnt_spec["weights"])
        if n_shapes == 0:
            sc["shape_notes"] = ["곧음"]
        else:
            sc["shape_notes"] = sample_pool(fm["penis_shape_notes"]["pool"], n_shapes, exclude={"특이 없음", "곧음"}) or ["곧음"]
        sc["erectile_function"] = rcat(fm["erectile_function"]["levels"], fm["erectile_function"]["weights"])
    else:
        ff = b5["fields_F"]
        sc["breast_cup"] = rcat(ff["breast_cup"]["values"], ff["breast_cup"]["weights"])
        sc["breast_asymmetry"] = rcat(ff["breast_asymmetry"]["levels"], ff["breast_asymmetry"]["weights"])
        n_nip = rpoisson(ff["nipple_features"]["count_dist"]["lambda"])
        sc["nipple_features"] = sample_pool(ff["nipple_features"]["pool"], max(1, n_nip))
        sc["labia_minora"] = rcat(ff["labia_minora"]["values"], ff["labia_minora"]["weights"])
        sc["vulva_color"] = rcat(ff["vulva_color"]["levels"], ff["vulva_color"]["weights"])
        m = ff["menstrual"]
        sc["menstrual"] = {
            "cycle_regularity": rcat(m["cycle_regularity"]["values"], m["cycle_regularity"]["weights"]),
            "pain_severity": rcat(m["pain_severity"]["levels"], m["pain_severity"]["weights"]),
        }
    fc = b5["fields_common"]
    bh = fc["body_hair_density"]
    sc["body_hair"] = {
        "pubic": rcat(bh["pubic"]["levels"], bh["pubic"]["weights"]),
        "leg": rcat(bh["leg"]["levels"], pick_weights(bh["leg"], sex)),
        "chest": rcat(bh["chest"]["levels"], pick_weights(bh["chest"], sex)),
        "underarm": rcat(bh["underarm"]["levels"], bh["underarm"]["weights"]),
    }
    sc["body_odor"] = rcat(fc["body_odor_level"]["levels"], fc["body_odor_level"]["weights"])
    out["sex_characteristics"] = sc

    # B5b self image (성별 분리 pool — 남녀 공통 + 성별 전용)
    b5b = b["B5b_self_image"]["fields"]
    fc_spec = b5b["focused_concern"]
    n_concern = rpoisson(fc_spec["count_dist"]["lambda"])
    # 0.2: type == "list_sample_sex_split" 사용. 이전 공통 pool도 fallback으로 지원.
    if "pool_common" in fc_spec:
        concern_pool = list(fc_spec["pool_common"]) + list(fc_spec.get(f"pool_{sex}", []))
    else:
        concern_pool = fc_spec["pool"]
    out["self_image"] = {
        "face": rcat(b5b["face_satisfaction"]["levels"], b5b["face_satisfaction"]["weights"]),
        "body": rcat(b5b["body_satisfaction"]["levels"], b5b["body_satisfaction"]["weights"]),
        "genital": rcat(b5b["genital_self_image"]["levels"], b5b["genital_self_image"]["weights"]),
        "focused_concern": sample_pool(concern_pool, n_concern, exclude={"없음"}),
    }

    # B6 chronic health (성별 필터: "F only" / "M only")
    b6 = b["B6_chronic_health"]
    n_chronic = rcat(b6["count_dist"]["values"], b6["count_dist"]["weights"])
    pool_items = []
    for cond, info in b6["pool"].items():
        if "F only" in cond and sex != "F":
            continue
        if "M only" in cond and sex != "M":
            continue
        pool_items.append((cond, info))
    chronics = []
    if n_chronic > 0 and pool_items:
        # weighted sample without replacement by prevalence
        remaining = list(pool_items)
        for _ in range(n_chronic):
            if not remaining:
                break
            weights = [info["prevalence"] for _, info in remaining]
            total_w = sum(weights)
            if total_w <= 0:
                break
            # scale so that per-draw prevalence determines inclusion probability
            idx = random.choices(range(len(remaining)), weights=weights, k=1)[0]
            cond, info = remaining.pop(idx)
            sev = random.choice(info["severity_levels"])
            clean_cond = cond.replace(" (F only)", "").replace(" (M only)", "")
            chronics.append({"condition": clean_cond, "severity": sev})
    out["chronic_health"] = chronics

    # B7 sleep
    b7 = b["B7_sleep"]["fields"]
    out["sleep"] = {
        "duration_hours": rnorm(b7["habitual_duration_hours"]["mean"], b7["habitual_duration_hours"]["sd"], b7["habitual_duration_hours"]["clip"], 1),
        "chronotype": rcat(b7["chronotype"]["values"], b7["chronotype"]["weights"]),
        "current_debt": rcat(b7["current_debt"]["levels"], b7["current_debt"]["weights"]),
        "insomnia": rcat(b7["insomnia"]["values"], b7["insomnia"]["weights"]),
    }

    # B8 sensory
    b8 = b["B8_sensory_profile"]["fields"]
    out["sensory"] = {
        "visual_acuity": rcat(b8["visual_acuity"]["values"], b8["visual_acuity"]["weights"]),
        "correction": rcat(b8["correction"]["values"], b8["correction"]["weights"]),
    }

    # B9 vocal
    b9 = b["B9_vocal"]["fields"]
    pitch_s = b9["pitch_hz"][sex]
    n_quirks = rpoisson(b9["voice_quirks"]["count_dist"]["lambda"])
    out["vocal"] = {
        "pitch_hz": int(round(rnorm(pitch_s["mean"], pitch_s["sd"], pitch_s["clip"], 0))),
        "volume": rcat(b9["volume_default"]["levels"], b9["volume_default"]["weights"]),
        "speech_rate": rcat(b9["speech_rate"]["levels"], b9["speech_rate"]["weights"]),
        "quirks": sample_pool(b9["voice_quirks"]["pool"], n_quirks, exclude={"없음"}),
    }

    # B10 skin hair
    b10 = b["B10_skin_hair"]["fields"]
    n_scars = rpoisson(b10["visible_scars"]["count_dist"]["lambda"])
    out["skin_hair"] = {
        "skin_type": rcat(b10["skin_type"]["values"], b10["skin_type"]["weights"]),
        "skin_tone": rcat(b10["skin_tone"]["levels"], b10["skin_tone"]["weights"]),
        "scars": sample_pool(b10["visible_scars"]["pool"], n_scars, exclude={"없음"}),
        "hair_density": rcat(b10["hair_density"]["levels"], b10["hair_density"]["weights"]),
        "hair_texture": rcat(b10["hair_texture"]["values"], b10["hair_texture"]["weights"]),
        "tattoos": rcat(b10["tattoos"]["values"], b10["tattoos"]["weights"]),
    }

    return out


# ---------------- memory layer ----------------

REFLEX_SIGNATURE = {
    "대결형": "즉각 대응·말 빨라짐·표정 굳음",
    "도피형": "화제 전환·자리 이동·시계 봄",
    "얼어붙음형": "표정 사라짐·눈 초점 흐려짐·말 안 함",
    "과잉 사회성형": "자동 사과·과잉 동의·웃음·상대 기분 살핌",
    "균형·차분형": "판단이 먼저 작동·호흡 유지·창문(window of tolerance) 안",
}


def roll_resources(tables):
    """M12_resources 굴림 — 자원·회복 5필드."""
    m12 = tables["memory"]["tables"]["M12_resources"]["fields"]

    sn = m12["support_network"]
    support = rcat(sn["values"], sn["weights"])

    cr = m12["coping_repertoire"]
    n_coping = max(1, rpoisson(cr["count_dist"]["lambda"]))
    coping = sample_pool(cr["pool"], n_coping)

    ms = m12["meaning_source"]
    n_meaning = rcat(ms["count_dist"]["values"], ms["count_dist"]["weights"])
    meaning = sample_pool(ms["pool"], n_meaning)

    rm = m12["positive_role_model"]
    role_model = rcat(rm["values"], rm["weights"])

    se = m12["self_efficacy"]
    efficacy = rcat(se["values"], se["weights"])

    return {
        "support_network": support,
        "coping": coping,
        "meaning_source": meaning,
        "positive_role_model": role_model,
        "self_efficacy": efficacy,
    }


def roll_memory(tables, sex):
    m = tables["memory"]["tables"]
    out = {}

    # M9 formative family (먼저)
    m9 = m["M9_formative_family"]["fields"]
    ff_out = {
        "ses_quintile": rcat(m9["ses_quintile"]["values"], m9["ses_quintile"]["weights"]),
        "father_occupation": rcat(m9["father_occupation_category"]["values"], m9["father_occupation_category"]["weights"]),
        "mother_employment": rcat(m9["mother_employment"]["values"], m9["mother_employment"]["weights"]),
        "sibling_structure": rcat(m9["sibling_structure"]["values"], m9["sibling_structure"]["weights"]),
        "economic_stability": rcat(m9["economic_stability_during_childhood"]["values"], m9["economic_stability_during_childhood"]["weights"]),
        "residence_changes": rcat(m9["residence_changes_count"]["values"], m9["residence_changes_count"]["weights"]),
        "emotional_climate": rcat(m9["family_emotional_climate"]["values"], m9["family_emotional_climate"]["weights"]),
    }

    # M2 CSA 먼저 결정 (ACE 카테고리와 연결하기 위해)
    m2 = m["M2_childhood_sexual_abuse"]
    csa_yes = random.random() < m2["prevalence"][sex]["yes"]

    # M1 ACE — M2 발생 여부를 반영
    m1 = m["M1_ace_cumulative"]["fields"]
    total_raw = rcat(m1["total_score_distribution"]["values"], m1["total_score_distribution"]["weights"])
    if total_raw == "5+":
        total = random.randint(5, 8)
    else:
        total = int(total_raw)
    categories_all = m1["categories"]["items"]
    sexual_cat = next((c for c in categories_all if "성적 학대" in c), None)
    non_sexual = [c for c in categories_all if c != sexual_cat]

    if csa_yes:
        # 성적 학대 강제 포함, 나머지는 non-sexual에서 total-1 샘플. total 최소 1 보장
        total = max(total, 1)
        rest = sample_pool(non_sexual, total - 1) if total > 1 else []
        ace_cats = [sexual_cat] + rest if sexual_cat else rest
    else:
        # 성적 학대 배제
        ace_cats = sample_pool(non_sexual, total) if total > 0 else []

    primary = rcat(m1["primary_category_when_present"]["values"], m1["primary_category_when_present"]["weights"]) if total > 0 else None
    ace_out = {"categories": ace_cats, "total": total, "primary": primary}

    # M3 parental loss
    m3 = m["M3_parental_loss"]["fields"]
    pl_status = rcat(m3["parental_status"]["values"], m3["parental_status"]["weights"])
    pl_out = {"status": pl_status}
    stable_statuses = {"양친 동거 안정", "양친 동거 불화 만성"}
    if pl_status not in stable_statuses:
        pl_out["event_age"] = rcat(m3["event_age_when_present"]["values"], m3["event_age_when_present"]["weights"])
        pl_out["caregiver_after"] = rcat(m3["primary_caregiver_after"]["values"], m3["primary_caregiver_after"]["weights"])
        pl_out["contact_with_absent"] = rcat(m3["contact_with_absent_parent"]["values"], m3["contact_with_absent_parent"]["weights"])
        pl_out["narrative"] = rcat(m3["narrative_around_loss"]["values"], m3["narrative_around_loss"]["weights"])

    # M2 CSA 상세 — csa_yes는 위에서 이미 결정됨
    csa_out = None
    if csa_yes:
        f = m2["fields_when_present"]
        csa_out = {
            "first_age": rcat(f["first_event_age"]["values"], f["first_event_age"]["weights"]),
            "perpetrator": rcat(f["perpetrator_relation"]["values"], f["perpetrator_relation"]["weights"]),
            "frequency": rcat(f["frequency_pattern"]["values"], f["frequency_pattern"]["weights"]),
            "physical_intensity": rcat(f["physical_intensity"]["levels"], f["physical_intensity"]["weights"]),
            "primary_sensory_channel": rcat(f["primary_sensory_channel"]["values"], f["primary_sensory_channel"]["weights"]),
            "narrative_processing": rcat(f["narrative_processing"]["values"], f["narrative_processing"]["weights"]),
            "disclosure": rcat(f["disclosure_history"]["values"], f["disclosure_history"]["weights"]),
        }

    # M4 bullying
    m4 = m["M4_bullying_history"]["fields"]
    victim = rcat(m4["victim_role"]["values"], m4["victim_role"]["weights"])
    perp = rcat(m4["perpetrator_role"]["values"], m4["perpetrator_role"]["weights"])
    bystander = rcat(m4["bystander_role"]["values"], m4["bystander_role"]["weights"])
    has_bullying = (victim != "없음" or perp != "없음")
    bullying_out = {
        "victim": victim,
        "perpetrator": perp,
        "bystander": bystander,
        "peak_period": rcat(m4["peak_period"]["values"], m4["peak_period"]["weights"]) if has_bullying else None,
        "form": rcat(m4["primary_form_when_present"]["values"], m4["primary_form_when_present"]["weights"]) if has_bullying else None,
        "dual_role": rcat(m4["dual_role_transition"]["values"], m4["dual_role_transition"]["weights"]),
    }

    # M5 attachment
    m5 = m["M5_attachment_style"]["fields"]
    att_out = {
        "style": rcat(m5["style"]["values"], m5["style"]["weights"]),
        "anxiety": rcat([1, 2, 3, 4, 5], m5["anxiety_dimension"]["weights"]),
        "avoidance": rcat([1, 2, 3, 4, 5], m5["avoidance_dimension"]["weights"]),
        "threshold": rcat(m5["trigger_threshold"]["levels"], m5["trigger_threshold"]["weights"]),
    }

    # M10 parent voice
    m10 = m["M10_parent_voice"]["fields"]
    pv_out = {
        "mother_pattern": rcat(m10["mother_pattern"]["values"], m10["mother_pattern"]["weights"]),
        "father_pattern": rcat(m10["father_pattern"]["values"], m10["father_pattern"]["weights"]),
        "consistency": rcat(m10["consistency_between_parents"]["levels"], m10["consistency_between_parents"]["weights"]),
        "intergenerational_pressure": rcat(m10["intergenerational_pressure"]["values"], m10["intergenerational_pressure"]["weights"]),
        "transmission": rcat(m10["transmission_mechanism"]["values"], m10["transmission_mechanism"]["weights"]),
    }

    # M6 embedded sentences
    m6 = m["M6_embedded_sentences"]["fields"]
    n_sent = rcat(m6["count"]["values"], m6["count"]["weights"])
    sentences = []
    for _ in range(n_sent):
        sentences.append({
            "speaker": rcat(m6["speaker_categories"]["values"], m6["speaker_categories"]["weights"]),
            "message_type": rcat(m6["message_type"]["values"], m6["message_type"]["weights"]),
            "trigger": rcat(m6["activation_trigger"]["values"], m6["activation_trigger"]["weights"]),
            "consciousness": rcat(m6["consciousness_of_sentence"]["values"], m6["consciousness_of_sentence"]["weights"]),
        })

    # M11 embedded reactions
    m11 = m["M11_embedded_reactions"]["fields"]
    n_react = rcat(m11["count"]["values"], m11["count"]["weights"])
    reactions = []
    for _ in range(n_react):
        reactions.append({
            "target": rcat(m11["target_attribute_per_event"]["values"], m11["target_attribute_per_event"]["weights"]),
            "reaction": rcat(m11["reaction_modality_per_event"]["values"], m11["reaction_modality_per_event"]["weights"]),
            "reactor": rcat(m11["reactor_relation_per_event"]["values"], m11["reactor_relation_per_event"]["weights"]),
            "age": rcat(m11["event_age_per_event"]["values"], m11["event_age_per_event"]["weights"]),
            "self_image_before": rcat(m11["self_image_before"]["levels"], m11["self_image_before"]["weights"]),
            "rupture_depth": rcat(m11["rupture_depth"]["levels"], m11["rupture_depth"]["weights"]),
            "processing": rcat(m11["narrative_processing"]["values"], m11["narrative_processing"]["weights"]),
        })

    # M7 trauma trigger (M2 발생이면 최소 1 보장)
    m7 = m["M7_trauma_trigger_channel"]["fields"]
    n_triggers = rcat(m7["active_channels_count"]["values"], m7["active_channels_count"]["weights"])
    if csa_yes and n_triggers == 0:
        n_triggers = 1
    triggers = []
    for _ in range(n_triggers):
        triggers.append({
            "channel": rcat(m7["channel_per_slot"]["values"], m7["channel_per_slot"]["weights"]),
            "intensity": rcat(m7["response_intensity"]["levels"], m7["response_intensity"]["weights"]),
            "consciousness": rcat(m7["consciousness_of_link"]["values"], m7["consciousness_of_link"]["weights"]),
        })

    # M8 default reflex
    m8 = m["M8_default_reflex"]["fields"]
    primary_reflex = rcat(m8["primary_reflex"]["values"], m8["primary_reflex"]["weights"])
    reflex_out = {
        "primary": primary_reflex,
        "secondary": rcat(m8["secondary_reflex"]["values"], m8["secondary_reflex"]["weights"]),
        "threshold": rcat(m8["activation_threshold"]["levels"], m8["activation_threshold"]["weights"]),
        "polyvagal": rcat(m8["polyvagal_default_state"]["values"], m8["polyvagal_default_state"]["weights"]),
        "signature": REFLEX_SIGNATURE.get(primary_reflex, ""),
    }

    out["ace"] = ace_out
    out["csa"] = csa_out
    out["parental_loss"] = pl_out
    out["bullying"] = bullying_out
    out["attachment"] = att_out
    out["embedded_sentences"] = sentences
    out["embedded_reactions"] = reactions
    out["trauma_trigger"] = triggers
    out["default_reflex"] = reflex_out
    out["formative_family"] = ff_out
    out["parent_voice"] = pv_out
    out["resources"] = roll_resources(tables)
    return out


# ---------------- identity layer ----------------

def roll_identity(tables, sex):
    i = tables["identity"]["tables"]
    out = {}

    i1 = i["I1_cognitive_ability"]["fields"]
    g = i1["g_iq_estimate"]
    out["cognitive"] = {
        "iq": int(round(rnorm(g["mean"], g["sd"], g["clip"], 0))),
        "strength": rcat(i1["cognitive_profile_strength"]["values"], i1["cognitive_profile_strength"]["weights"]),
        "weakness": rcat(i1["cognitive_profile_weakness"]["values"], i1["cognitive_profile_weakness"]["weights"]),
        "academic_performance": rcat(i1["academic_performance_level"]["levels"], i1["academic_performance_level"]["weights"]),
        "metacognition": rcat(i1["metacognition"]["levels"], i1["metacognition"]["weights"]),
        "thinking_style": rcat(i1["thinking_style"]["values"], i1["thinking_style"]["weights"]),
        "curiosity": rcat(i1["intellectual_curiosity"]["levels"], i1["intellectual_curiosity"]["weights"]),
    }

    i2 = i["I2_sexuality"]["fields"]
    n_taboo = rpoisson(i2["internalized_taboos"]["count_dist"]["lambda"])
    fc = i2["function_satisfaction"]
    out["sexuality"] = {
        "orientation": rcat(i2["orientation"]["values"], i2["orientation"]["weights"]),
        "out_status": rcat(i2["out_status"]["values"], i2["out_status"]["weights"]),
        "experience": rcat(i2["experience_status"]["values"], i2["experience_status"]["weights"]),
        "first_age": rcat(i2["first_experience_age"]["values"], i2["first_experience_age"]["weights"]),
        "desire_intensity": rcat(i2["desire_intensity"]["levels"], i2["desire_intensity"]["weights"]),
        "desire_grain": rcat(i2["desire_pattern_grain"]["values"], i2["desire_pattern_grain"]["weights"]),
        "taboos": sample_pool(i2["internalized_taboos"]["pool"], n_taboo),
        "function": {
            "arousal": rcat(fc["arousal"]["levels"], fc["arousal"]["weights"]),
            "performance": rcat(fc["performance"]["levels"], fc["performance"]["weights"]),
            "satisfaction": rcat(fc["satisfaction"]["levels"], fc["satisfaction"]["weights"]),
        },
        "consent_marker": rcat(i2["consent_history_marker"]["values"], i2["consent_history_marker"]["weights"]),
    }

    i3 = i["I3_impulse_and_footprint"]
    a = i3["fields_A_impulse_addiction"]
    b = i3["fields_B_digital_footprint_snapshot"]

    n_platforms = max(1, rpoisson(a["primary_platform_mix"]["count_dist"]["lambda"]))
    platforms = sample_pool(a["primary_platform_mix"]["pool"], n_platforms)

    smoking_spec = a["substance_patterns"]["smoking"]
    n_games = rpoisson(b["favorite_games_snapshot"]["count_dist"]["lambda"])
    n_comm = rpoisson(b["frequent_communities"]["count_dist"]["lambda"])
    n_album = rpoisson(b["photo_album_theme"]["count_dist"]["lambda"])
    n_search = rpoisson(b["recent_search_pattern"]["count_dist"]["lambda"])
    n_bm = rpoisson(b["bookmarks_and_subscriptions"]["count_dist"]["lambda"])

    # B_footprint: sns_public_face ↔ private_vs_public_gap 충돌 보정
    # "부계정 운영"이면 본계정이 있어야 함 → "계정 없음·비공개" 금지
    sns_face = rcat(b["sns_public_face"]["values"], b["sns_public_face"]["weights"])
    private_gap = rcat(b["private_vs_public_gap"]["levels"], b["private_vs_public_gap"]["weights"])
    if "부계정" in private_gap and sns_face == "계정 없음·비공개":
        non_none_vals = [v for v in b["sns_public_face"]["values"] if v != "계정 없음·비공개"]
        non_none_ws = [w for v, w in zip(b["sns_public_face"]["values"], b["sns_public_face"]["weights"]) if v != "계정 없음·비공개"]
        sns_face = rcat(non_none_vals, non_none_ws)

    out["impulse_footprint"] = {
        "A_impulse": {
            "digital_hours": rnorm(a["digital_consumption_daily_hours"]["mean"], a["digital_consumption_daily_hours"]["sd"], a["digital_consumption_daily_hours"]["clip"], 1),
            "platforms": platforms,
            "compulsion": rcat(a["digital_compulsion_level"]["levels"], a["digital_compulsion_level"]["weights"]),
            "substances": {
                "alcohol": rcat(a["substance_patterns"]["alcohol"]["levels"], a["substance_patterns"]["alcohol"]["weights"]),
                "smoking": rcat(smoking_spec["values"], pick_weights(smoking_spec, sex)),
                "caffeine": rcat(a["substance_patterns"]["caffeine"]["levels"], a["substance_patterns"]["caffeine"]["weights"]),
                "other": rcat(a["substance_patterns"]["cannabis_or_others"]["values"], a["substance_patterns"]["cannabis_or_others"]["weights"]),
            },
            "eating_impulse": rcat(a["eating_impulse_pattern"]["values"], a["eating_impulse_pattern"]["weights"]),
            "impulse_control": rcat(a["impulse_control_general"]["levels"], a["impulse_control_general"]["weights"]),
            "reward_sensitivity": rcat(a["reward_sensitivity"]["levels"], a["reward_sensitivity"]["weights"]),
            "escape_default": rcat(a["escape_default"]["values"], a["escape_default"]["weights"]),
            "self_awareness": rcat(a["self_awareness_of_pattern"]["values"], a["self_awareness_of_pattern"]["weights"]),
        },
        "B_footprint": {
            "games": sample_pool(b["favorite_games_snapshot"]["pool"], n_games, exclude={"플레이 안 함"}),
            "journal_tone": rcat(b["journal_or_notes_tone"]["values"], b["journal_or_notes_tone"]["weights"]),
            "sns_public_face": sns_face,
            "private_vs_public_gap": private_gap,
            "communities": sample_pool(b["frequent_communities"]["pool"], n_comm, exclude={"커뮤니티 비활성"}),
            "playlist": rcat(b["playlist_tone"]["values"], b["playlist_tone"]["weights"]),
            "album_theme": sample_pool(b["photo_album_theme"]["pool"], n_album),
            "recent_search": sample_pool(b["recent_search_pattern"]["pool"], n_search),
            "bookmarks": sample_pool(b["bookmarks_and_subscriptions"]["pool"], n_bm, exclude={"없음 (관심사 없음)"}),
        },
    }
    return out


# ---------------- korea layer ----------------

# 대학 tier별 허용 수능 등급 (정시 기준 근사. 고교 유형과 무관 — 마이스터고 출신도 정시 1등급이면 의대 가능)
TIER_ALLOWED_GRADES = {
    "SKY (서울대·고려대·연세대)": ["1등급", "2등급"],
    "성균관·한양·중앙·경희·서강·이화 등": ["1등급", "2등급", "3등급"],
    "in서울 (그 외)": ["2등급", "3등급", "4등급"],
    "지방 거점 국립대": ["3등급", "4등급", "5등급"],
    "지방 사립": ["4등급", "5등급", "6등급"],
    "전문대": ["5등급", "6등급", "7등급"],
    "고졸": ["5등급", "6등급", "7등급", "8~9등급", "응시 안 함"],
    "재수 중·휴학 중": ["3등급", "4등급", "5등급", "6등급"],
    "입학 후 자퇴": ["2등급", "3등급", "4등급", "5등급"],
}

# 의·치·약·수의는 수능 1등급 상위권 대학만
MAJOR_TIER_RESTRICTION = {
    "의·치·약·수의": {"SKY (서울대·고려대·연세대)", "성균관·한양·중앙·경희·서강·이화 등"},
}


def roll_korea(tables, sex, age, slot_region=None):
    k = tables["korea"]["tables"]
    k2 = k["K2_korea_appearance_experience"]["fields"]
    k3 = k["K3_korea_region_voice"]["fields"]

    # age bracket 결정
    if age <= 18:
        bracket = "16_18"
    elif age <= 25:
        bracket = "19_25"
    else:
        bracket = "26_35"

    k1 = k["K1_korea_education"]["by_age"][bracket]["fields"]

    if bracket == "16_18":
        education = {
            "current_status": rcat(k1["current_status"]["values"], k1["current_status"]["weights"]),
            "school_type": rcat(k1["school_type"]["values"], k1["school_type"]["weights"]),
            "academic_performance": rcat(k1["academic_performance"]["levels"], k1["academic_performance"]["weights"]),
            "private_education": rcat(k1["private_education"]["levels"], k1["private_education"]["weights"]),
            "parental_pressure": rcat(k1["parental_pressure"]["levels"], k1["parental_pressure"]["weights"]),
        }
    elif bracket == "19_25":
        # 1) tier 먼저 (전체 분포 유지)
        tier = rcat(k1["university_tier"]["values"], k1["university_tier"]["weights"])

        # 2) tier에 맞는 수능 등급 재샘플
        allowed = TIER_ALLOWED_GRADES.get(tier, k1["suneung_grade_average"]["values"])
        grade_vals = k1["suneung_grade_average"]["values"]
        grade_ws = k1["suneung_grade_average"]["weights"]
        filtered = [(v, w) for v, w in zip(grade_vals, grade_ws) if v in allowed]
        if filtered:
            fv, fw = zip(*filtered)
            grade = rcat(list(fv), list(fw))
        else:
            grade = rcat(grade_vals, grade_ws)

        # 3) major 샘플 — 의·치·약·수의는 상위 tier에서만 허용
        major = rcat(k1["major_category"]["values"], k1["major_category"]["weights"])
        if major in MAJOR_TIER_RESTRICTION and tier not in MAJOR_TIER_RESTRICTION[major]:
            allowed_majors_vals = [v for v in k1["major_category"]["values"] if v != major]
            allowed_majors_ws = [w for v, w in zip(k1["major_category"]["values"], k1["major_category"]["weights"]) if v != major]
            major = rcat(allowed_majors_vals, allowed_majors_ws)

        education = {
            "high_school": rcat(k1["high_school_type"]["values"], k1["high_school_type"]["weights"]),
            "suneung_grade": grade,
            "university_tier": tier,
            "major": major,
            "retake": rcat(k1["retake_status"]["values"], k1["retake_status"]["weights"]),
            "private_education": rcat(k1["private_education_intensity"]["levels"], k1["private_education_intensity"]["weights"]),
            "academic_self_concept": rcat(k1["academic_self_concept"]["levels"], k1["academic_self_concept"]["weights"]),
            "parental_pressure": rcat(k1["parental_pressure_intensity"]["levels"], k1["parental_pressure_intensity"]["weights"]),
        }
    else:  # 26_35
        education = {
            "final_education": rcat(k1["final_education"]["values"], k1["final_education"]["weights"]),
            "university_tier_past": rcat(k1["university_tier_past"]["values"], k1["university_tier_past"]["weights"]),
            "major_past": rcat(k1["major_past"]["values"], k1["major_past"]["weights"]),
            "current_status": rcat(k1["current_status"]["values"], k1["current_status"]["weights"]),
            "academic_self_concept": rcat(k1["academic_self_concept"]["levels"], k1["academic_self_concept"]["weights"]),
        }

    n_dom = rpoisson(k2["discrimination_domain"]["count_dist"]["lambda"])
    appearance = {
        "discrimination_frequency": rcat(k2["discrimination_frequency"]["values"], k2["discrimination_frequency"]["weights"]),
        "discrimination_domain": sample_pool(k2["discrimination_domain"]["pool"], n_dom),
        "management_level": rcat(k2["appearance_management_level"]["levels"], k2["appearance_management_level"]["weights"]),
        "cosmetic_surgery": rcat(k2["cosmetic_surgery_history"]["values"], k2["cosmetic_surgery_history"]["weights"]),
        "diet_history": rcat(k2["diet_history"]["values"], k2["diet_history"]["weights"]),
        "lookism_internalization": rcat(k2["lookism_internalization"]["levels"], k2["lookism_internalization"]["weights"]),
        "capital_awareness": rcat(k2["appearance_capital_awareness"]["levels"], k2["appearance_capital_awareness"]["weights"]),
    }

    birth_region = slot_region if slot_region is not None else rcat(k3["birth_region"]["values"], k3["birth_region"]["weights"])

    # 지역 차별 ↔ 출생 지역 상관: 수도권·충청·강원·제주는 차별 거의 없음,
    # 호남·조선족·북한 이탈·영남은 차별 경험 높음
    HIGH_DISCRIM_REGIONS = {
        "호남 (광주·전남·전북)",
        "조선족 (중국 동포)",
        "북한 이탈",
        "해외 출생·재외 한인",
    }
    MID_DISCRIM_REGIONS = {
        "영남 (부산·대구·울산·경남·경북)",
    }
    discrim_values = k3["regional_discrimination_experienced"]["values"]
    if birth_region in HIGH_DISCRIM_REGIONS:
        # 없음 15%, 농담 25%, 직접 30%, 반복 20%, 만성 10%
        discrim = rcat(discrim_values, [0.15, 0.25, 0.30, 0.20, 0.10])
    elif birth_region in MID_DISCRIM_REGIONS:
        # 없음 60%, 농담 25%, 직접 10%, 반복 4%, 만성 1%
        discrim = rcat(discrim_values, [0.60, 0.25, 0.10, 0.04, 0.01])
    else:
        # 수도권/충청/강원/제주: 없음 85%, 농담 12%, 직접 3%
        discrim = rcat(discrim_values, [0.85, 0.12, 0.03, 0.0, 0.0])

    region_voice = {
        "birth_region": birth_region,
        "residence_match": rcat(k3["current_residence_match"]["values"], k3["current_residence_match"]["weights"]),
        "accent_intensity": rcat(k3["accent_intensity"]["levels"], k3["accent_intensity"]["weights"]),
        "accent_self_conscious": rcat(k3["accent_self_consciousness"]["levels"], k3["accent_self_consciousness"]["weights"]),
        "family_politics": rcat(k3["family_politics"]["values"], k3["family_politics"]["weights"]),
        "personal_politics": rcat(k3["personal_politics_alignment"]["values"], k3["personal_politics_alignment"]["weights"]),
        "family_religion": rcat(k3["family_religion"]["values"], k3["family_religion"]["weights"]),
        "personal_religion": rcat(k3["personal_religion_alignment"]["values"], k3["personal_religion_alignment"]["weights"]),
        "regional_discrimination": discrim,
    }

    # K4 occupation — by_age 분기
    k4 = k["K4_occupation"]["by_age"][bracket]
    if bracket == "19_25" and "weights_M" in k4:
        weights = k4["weights_M"] if sex == "M" else k4["weights_F"]
    else:
        weights = k4["weights"]
    occupation = rcat(k4["values"], weights)

    return {
        "education": education,
        "appearance_experience": appearance,
        "region_voice": region_voice,
        "occupation": occupation,
    }


# ---------------- orchestration ----------------

# Slot region short name → korea.json birth_region full name
_SLOT_REGION_MAP = {
    "서울": "서울",
    "경기·인천 (수도권)": "경기·인천 (수도권)",
    "충청": "충청 (대전·세종 포함)",
    "호남": "호남 (광주·전남·전북)",
    "영남": "영남 (부산·대구·울산·경남·경북)",
    "강원": "강원",
    "제주": "제주",
}

# Seed 2: 일반 대중 슬롯 (17~35세, F15/M15, 지역 분포)
SLOTS_SEED_2 = [
    # (id, age, sex, region)
    (1, 17, "F", "경기·인천 (수도권)"),
    (2, 17, "M", "영남"),
    (3, 18, "F", "호남"),
    (4, 18, "M", "경기·인천 (수도권)"),
    (5, 19, "F", "충청"),
    (6, 20, "M", "서울"),
    (7, 20, "F", "영남"),
    (8, 21, "M", "서울"),
    (9, 22, "F", "호남"),
    (10, 22, "M", "영남"),
    (11, 23, "F", "서울"),
    (12, 24, "M", "서울"),
    (13, 24, "F", "영남"),
    (14, 25, "M", "경기·인천 (수도권)"),
    (15, 25, "F", "호남"),
    (16, 26, "M", "충청"),
    (17, 27, "F", "서울"),
    (18, 27, "M", "서울"),
    (19, 28, "F", "경기·인천 (수도권)"),
    (20, 28, "M", "영남"),
    (21, 29, "F", "서울"),
    (22, 29, "M", "충청"),
    (23, 30, "F", "호남"),
    (24, 30, "M", "서울"),
    (25, 31, "F", "경기·인천 (수도권)"),
    (26, 31, "M", "강원"),
    (27, 32, "M", "영남"),
    (28, 33, "F", "서울"),
    (29, 34, "M", "경기·인천 (수도권)"),
    (30, 35, "F", "호남"),
]


def roll_character(char_id, age, sex, region, tables, personas):
    body = roll_body(tables, sex)
    memory = roll_memory(tables, sex)
    identity = roll_identity(tables, sex)
    mapped_region = _SLOT_REGION_MAP.get(region, region) if region else None
    korea = roll_korea(tables, sex, age, slot_region=mapped_region)

    sampled = random.sample(personas, 2)
    labels = [f'#{p["id"]} {p["voice"]}' for p in sampled]

    char = {
        "id": char_id,
        "age": age,
        "sex": sex,
        "post_hoc_label": labels,
        "body": body,
        "memory": memory,
        "identity": identity,
        "korea": korea,
    }
    if region is not None:
        char["region"] = mapped_region
    return char


def assign_sex_list(n_total, n_M):
    ids = list(range(1, n_total + 1))
    m_ids = set(random.sample(ids, n_M))
    return ["M" if i in m_ids else "F" for i in ids]


def compute_sex_rank(characters):
    for target_sex in ("M", "F"):
        subset = [c for c in characters if c["sex"] == target_sex]
        subset.sort(key=lambda c: (-c["body"]["face_attractiveness"]["absolute_score"], c["id"]))
        for rank, c in enumerate(subset, start=1):
            c["body"]["face_attractiveness"]["sex_rank"] = rank


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_seed.py <seed_number>", file=sys.stderr)
        sys.exit(1)
    try:
        seed = int(sys.argv[1])
    except ValueError:
        print(f"Invalid seed: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)

    random.seed(seed)

    tables = {layer: json.loads((TABLES_DIR / f"{layer}.json").read_text(encoding="utf-8"))
              for layer in ("body", "memory", "identity", "korea")}
    personas = json.loads((DATA_DIR / "personas.json").read_text(encoding="utf-8"))

    # Slot-based generation: seed에 슬롯 표가 있으면 사용. 없으면 default 30 × age 20.
    if seed == 2:
        slot_list = SLOTS_SEED_2
    else:
        slot_list = [(i + 1, 20, sx, None) for i, sx in enumerate(assign_sex_list(30, 15))]

    characters = [roll_character(cid, age, sx, region, tables, personas)
                  for (cid, age, sx, region) in slot_list]
    compute_sex_rank(characters)

    kst = timezone(timedelta(hours=9))
    ages_in_slots = [s[1] for s in slot_list]
    result = {
        "seed": seed,
        "generated_at": datetime.now(kst).isoformat(timespec="seconds"),
        "constraints": {
            "sex_ratio": {"M": 15, "F": 15},
            "age_distribution": {
                "min": min(ages_in_slots),
                "max": max(ages_in_slots),
                "note": "slot-based for seed 2" if seed == 2 else "fixed 20 for other seeds",
            },
            "region": "한국 (지역 분포)",
        },
        "table_versions": {
            "body": tables["body"]["version"],
            "memory": tables["memory"]["version"],
            "identity": tables["identity"]["version"],
            "korea": tables["korea"]["version"],
        },
        "characters": characters,
        "post_generation_notes": [
            f"seed={seed}, stdlib-only Python 샘플링 (random.seed 고정, 비트 단위 재현)",
            "cross-layer 일관성: M2 발생 시 M7 최소 1채널 보장. 나머지 상관은 독립 샘플링 (첫 시드 분포 검수 목적).",
        ],
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"seed_{seed:03d}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
