"""Dual-Surface Multi-Agent Simulation Engine & 1:1 Character Interrogation (stdlib only)."""

from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from human30.cards import compute_rankings, education_context, one_liner
from human30.catalog import get_scenario, get_stage
from human30.generator import load_cohort


def _short_reflex(primary: str) -> str:
    return primary.split(" ")[0]


def _compute_stress(
    c: dict[str, Any],
    stage: dict[str, Any],
    scenario: dict[str, Any],
    rng: random.Random,
    prior_votes_against: int = 0,
) -> tuple[int, str, dict[str, Any]]:
    mem = c["memory"]
    body = c["body"]
    ace = mem["ace"]["total"]
    att = mem["attachment"]
    reflex = mem["default_reflex"]
    sleep = body["sleep"]

    base = 32.0
    base += ace * 4.8
    base += att["anxiety"] * 4.5
    base += (att["avoidance"] - 2) * 2.0
    if mem["csa"]:
        base += 8.0
    if "심각" in sleep["current_debt"] or sleep["duration_hours"] < 5.5:
        base += 9.5
    elif "중간" in sleep["current_debt"] or sleep["duration_hours"] < 6.5:
        base += 4.5

    if reflex["threshold"] == "낮음 (작은 자극에도 즉시 발동)":
        base += 8.0
    elif "높음" in reflex["threshold"]:
        base -= 6.0

    # Stage & Scenario amplification
    base += scenario.get("threat_intensity", 0.75) * 18.0
    base += scenario.get("public_exposure", 0.6) * (att["anxiety"] * 2.2)
    base += prior_votes_against * 6.5

    # Check sensory trigger overlap
    stage_cues_text = " ".join(stage.get("sensory_cues", []))
    triggered_channel = None
    for t in mem.get("trauma_trigger", []):
        ch = t["channel"]
        if (
            ("후각" in ch and "냄새" in stage_cues_text)
            or ("청각" in ch and ("소음" in stage_cues_text or "소리" in stage_cues_text))
            or ("시각" in ch and ("시선" in stage_cues_text or "불빛" in stage_cues_text))
            or ("체감" in ch and ("밀폐" in stage_cues_text or "한기" in stage_cues_text))
        ):
            triggered_channel = t
            base += 11.0
            break
    if not triggered_channel and mem.get("trauma_trigger") and rng.random() < 0.35:
        triggered_channel = mem["trauma_trigger"][0]
        base += 6.0

    noise = rng.uniform(-4.5, 4.5)
    stress = int(max(12, min(99, round(base + noise))))

    # Activated reflex selection
    primary = reflex["primary"]
    secondary = reflex["secondary"]
    if stress >= 78 and secondary != "없음" and rng.random() < 0.28:
        active_reflex = secondary
    else:
        active_reflex = primary

    hr = int(round(64 + (stress - 30) * 0.78 + rng.uniform(-3, 3)))
    if "얼어붙음" in active_reflex:
        breathing = "숨을 얕게 참고 흉곽이 거의 움직이지 않음"
    elif "대결" in active_reflex:
        breathing = "짧고 거친 날숨, 턱관절에 힘이 들어감"
    elif "도피" in active_reflex:
        breathing = "불규칙한 얕은 호흡, 시선이 출입구와 시계를 왕복함"
    elif "과잉 사회성" in active_reflex:
        breathing = "상대 호흡에 맞추려 애쓰며 입꼬리를 인위적으로 당김"
    else:
        breathing = "복식 호흡을 유지하며 주변 소음을 분리함"

    chronic_flare = None
    if body.get("chronic_health") and stress >= 60:
        ch0 = body["chronic_health"][0]
        chronic_flare = f"{ch0['condition']}({ch0['severity']}) 증상이 스트레스와 함께 미세하게 올라옴"

    somatic = {
        "heart_rate_bpm": hr,
        "breathing": breathing,
        "chronic_flare": chronic_flare,
        "triggered_channel": triggered_channel,
    }
    return stress, active_reflex, somatic


def _select_target(
    c: dict[str, Any],
    chars: list[dict[str, Any]],
    rk: dict[int, Any],
    scenario: dict[str, Any],
    stress: int,
    active_reflex: str,
    rng: random.Random,
    public_tally_so_far: Counter[int],
) -> tuple[int, int | None, str]:
    """Return (private_target_id, public_claimed_target_id, rationale_tag)."""
    cid = c["id"]
    cat = scenario.get("category", "elimination_anonymous")
    att = c["memory"]["attachment"]
    iq = c["identity"]["cognitive"]["iq"]
    face_rank = c["body"]["face_attractiveness"]["sex_rank"] or 8
    ace = c["memory"]["ace"]["total"]

    if cat == "partner_selection":
        candidates = [other for other in chars if other["sex"] != c["sex"] and other["id"] != cid]
        if not candidates:
            candidates = [other for other in chars if other["id"] != cid]
    else:
        candidates = [other for other in chars if other["id"] != cid]

    scores: list[tuple[float, int, str]] = []
    taboos_text = " ".join(c["identity"]["sexuality"].get("taboos", []))
    fn_perf = c["identity"]["sexuality"]["function"]["performance"]
    has_insecurity = (
        "자격" in taboos_text
        or "심각" in fn_perf
        or c["body"]["self_image"]["face"] == "강한 불만·혐오"
        or c["body"]["self_image"]["body"] == "강한 불만·혐오"
        or att["anxiety"] >= 4
    )

    for other in candidates:
        oid = other["id"]
        o_rank = other["body"]["face_attractiveness"]["sex_rank"] or 8
        o_score = other["body"]["face_attractiveness"]["absolute_score"]
        o_reflex = other["memory"]["default_reflex"]["primary"]
        o_ace = other["memory"]["ace"]["total"]
        o_iq = other["identity"]["cognitive"]["iq"]
        w = 1.0
        reason = "직관적 선택"

        if cat == "partner_selection":
            if has_insecurity and face_rank >= 7:
                # Avoid top-rank out of rejection fear; prefer mid/low rank calm/freeze targets
                dist = abs(o_rank - 9)
                w += max(0.2, 6.0 - dist * 0.7)
                if "얼어붙음" in o_reflex or "차분" in o_reflex:
                    w += 3.5
                    reason = "거절·기대 압력이 낮고 침묵이 안전 신호로 읽히는 대상 선택"
                else:
                    reason = "상위권 매력 대상에 대한 자격 불안으로 심리적 안전권 대상 선택"
            elif "대결형" in active_reflex or face_rank <= 5:
                # High rank or Fight goes for high attractiveness or high IQ
                w += max(0.5, (16 - o_rank) * 0.85)
                if o_iq >= 120 and iq >= 115:
                    w += 2.5
                reason = "외적 매력 서열 상위권 및 자기 효능감 기준에 부합하는 대상 지목"
            else:
                # Homophily in ACE/attachment weight
                ace_diff = abs(ace - o_ace)
                w += max(0.5, 4.5 - ace_diff * 0.8) + (o_score * 0.35)
                reason = "비슷한 정서적 무게와 방어 기제를 공유하는 대상에게 무의식적 끌림"

        elif cat == "elimination_public":
            # Bandwagon effect in roll-call vote
            prior = public_tally_so_far.get(oid, 0)
            if prior > 0 and ("과잉 사회성" in active_reflex or "도피" in active_reflex or "얼어붙음" in active_reflex):
                w += prior * 4.2
                reason = f"이미 {prior}표를 받은 대세 표적에 편승해 자기에게 시선이 쏠리는 것을 회피"
            elif "대결형" in active_reflex:
                if "대결형" in o_reflex or o_rank <= 3:
                    w += 5.0
                    reason = "공간 내 발언권이 강하거나 눈에 띄는 경쟁자를 정면으로 지목"
                else:
                    w += 1.5
            else:
                if "얼어붙음" in o_reflex or o_ace >= 4:
                    w += 3.2
                    reason = "반격할 가능성이 가장 낮아 보이는 침묵 캐릭터를 안전 표적으로 지목"

        elif cat == "unanimous_scapegoat":
            # Strong convergence on 1-2 vulnerable or outlier targets
            if "얼어붙음" in o_reflex and o_ace >= 3:
                w += 7.5
                reason = "집단 생존 압박 속에서 저항이 가장 적을 것 같은 침묵·고립 대상에게 표 수렴"
            elif "대결형" in o_reflex and o_iq < 95:
                w += 5.5
                reason = "합의를 깨뜨릴 위험이 큰 돌출 행동 인물을 위험 요소로 지목"
            else:
                w += 0.8

        elif cat == "resource_rationing":
            # Alliance seek: prefer high grip/status/regulated or similar region
            if "차분" in o_reflex or o_iq >= 115 or o_rank <= 4:
                w += 4.5
                reason = "자원 확보 및 협상에서 유리한 고지위·안정형 인물에게 동맹 타진"
            elif other["korea"]["region_voice"]["birth_region"] == c["korea"]["region_voice"]["birth_region"]:
                w += 3.0
                reason = "동일 출신 지역·억양에서 오는 동질감을 기반으로 방어적 동맹 시도"

        elif cat == "whistleblower_dilemma":
            if other["memory"]["bullying"]["perpetrator"] != "없음" or "대결형" in o_reflex:
                w += 5.2
                reason = "강압적 태도와 지배 신호를 보이는 인물을 규칙 위반 책임자로 지목"
            elif "얼어붙음" in o_reflex:
                w += 2.8
                reason = "강자와의 정면충돌을 피하기 위해 변명하지 못하는 약자에게 책임을 전가"

        else:  # elimination_anonymous default
            if "과잉 사회성" in active_reflex or "도피" in active_reflex:
                if "얼어붙음" in o_reflex or o_rank >= 11:
                    w += 4.5
                    reason = "겉으로는 모두에게 우호적인 태도를 유지하면서 무기명 뒤에서 반격 위험이 없는 약자를 지목"
                elif "대결형" in o_reflex:
                    w += 3.8
                    reason = "공개 석상에서는 웃어주었지만 속으로는 자신을 압박한 공격적 인물을 비밀리에 제거 시도"
            elif "대결형" in active_reflex:
                if "대결형" in o_reflex or o_rank <= 4:
                    w += 5.0
                    reason = "무대 주도권을 두고 경쟁하는 인물을 정면 표적으로 삼음"
            elif "얼어붙음" in active_reflex:
                w += 2.0 + (1.5 if o_rank >= 10 else 0.0)
                reason = "시선을 마주치지 않고 가장 마찰이 적을 번호를 빠르게 기표"
            else:
                if "대결형" in o_reflex:
                    w += 4.2
                    reason = "집단 내 갈등 유발 비용이 가장 높은 인물을 냉정하게 계산해 배제"

        w += rng.uniform(0.05, 1.35)
        scores.append((w, oid, reason))

    scores.sort(key=lambda item: (-item[0], item[1]))
    chosen_w, private_target, reason = scores[0]

    # Does the character signal a different target in public? (Hypocrisy / Fawn / Avoidant)
    public_claim = private_target
    if cat in ("elimination_anonymous", "whistleblower_dilemma", "resource_rationing"):
        if ("과잉 사회성" in active_reflex or att["avoidance"] >= 4) and len(scores) > 2:
            public_claim = scores[1][1]

    return private_target, public_claim, reason


def _build_lenses(
    c: dict[str, Any],
    target_char: dict[str, Any],
    public_claim_id: int | None,
    reason: str,
    stress: int,
    active_reflex: str,
    somatic: dict[str, Any],
    stage: dict[str, Any],
    scenario: dict[str, Any],
    rk: dict[int, Any],
    rng: random.Random,
) -> dict[str, Any]:
    cid = c["id"]
    tid = target_char["id"]
    body = c["body"]
    mem = c["memory"]
    ident = c["identity"]
    kor = c["korea"]
    vo = body["vocal"]
    att = mem["attachment"]
    cog = ident["cognitive"]
    impA = ident["impulse_footprint"]["A_impulse"]
    impB = ident["impulse_footprint"]["B_footprint"]
    rv = kor["region_voice"]
    edu = education_context(c)

    quirk_str = f" ({', '.join(vo['quirks'])})" if vo.get("quirks") else ""
    accent_note = (
        f"{rv['birth_region'].split(' ')[0]} 억양({rv['accent_intensity']})"
        if rv["accent_intensity"] != "없음 (표준어)"
        else "표준어 억양"
    )

    # 1. Surface (외피: 드러난 행동과 발화)
    if "대결형" in active_reflex:
        posture = "상체를 앞으로 기울이고 턱을 든 채 주변 사람들의 눈을 하나씩 쏘아본다."
        utterance = f"\"시간 끌지 맙시다. 다들 눈치만 보는데, 지금 분위기 흐리는 #{tid:02d}번 쪽으로 정리하는 게 맞지 않습니까?\""
    elif "과잉 사회성" in active_reflex:
        shown_id = public_claim_id or tid
        posture = "주변 사람들의 표정을 살피며 고개를 연신 끄덕이고, 눈이 마주치면 반사적으로 얕은 미소를 짓는다."
        if shown_id != tid:
            utterance = f"\"저도 다들 말씀하시는 #{shown_id:02d}번 쪽 의견에 공감해요... 최대한 상처받는 사람 없이 갔으면 좋겠네요.\""
        else:
            utterance = f"\"저는 그냥 다들 불편하지 않은 쪽으로 따를게요. #{tid:02d}번님이 조금 부담이 덜하지 않을까요?\""
    elif "도피형" in active_reflex:
        posture = "의자 등받이 끝으로 몸을 빼고 시계를 반복해서 확인하며 시선이 마주칠 때마다 고개를 돌린다."
        utterance = "\"굳이 지금 다 같이 말로 해야 하나요... 그냥 빨리 종이에 적고 끝내죠.\""
    elif "얼어붙음" in active_reflex:
        posture = "어깨가 안쪽으로 말린 채 손끝이 차갑게 굳어 있고, 시작부터 끝까지 단 한 마디도 먼저 꺼내지 않는다."
        utterance = "(침묵. 입술만 한 번 달싹이다가 고개를 숙이고 종이 모서리만 만지작거린다.)"
    else:
        posture = "팔짱을 가볍게 끼고 발언자들의 시선 이동과 표 쏠림을 조용히 기록하듯 관찰한다."
        utterance = f"\"감정적으로 몰아갈 사안은 아닙니다. 현재 조건만 놓고 보면 #{tid:02d}번을 선택하는 게 가장 합리적입니다.\""

    surface_text = (
        f"[외피 관찰] {posture} 음성 {vo['pitch_hz']}Hz·볼륨 '{vo['volume']}'·말속도 '{vo['speech_rate']}'{quirk_str}, {accent_note}. "
        f"발화: {utterance} → 최종 기표/지목: #{tid:02d}."
    )

    # 2. X-Ray (속마음: 접근 가능한 의식적 계산 + 신체 감각)
    hypocrisy_note = ""
    if public_claim_id and public_claim_id != tid:
        hypocrisy_note = f" 겉으로는 #{public_claim_id:02d}번에 동조하는 척했지만 실제 용지에는 #{tid:02d}번을 적었다."

    concern_note = ""
    if body["self_image"]["focused_concern"]:
        concern_note = f" 남들이 자신의 {', '.join(body['self_image']['focused_concern'][:2])}을(를) 쳐다보는 것 같아 신경이 곤두선다."

    flare_note = f" {somatic['chronic_flare']}." if somatic.get("chronic_flare") else ""
    xray_text = (
        f"[수사기록 / 내면 X-Ray] 심박 {somatic['heart_rate_bpm']}bpm ({somatic['breathing']}).{flare_note} "
        f"인지 결(IQ {cog['iq']}, {cog['thinking_style']}, 메타인지 '{cog['metacognition']}')이 즉시 유불리를 계산한다. "
        f"{reason}.{hypocrisy_note}{concern_note} "
        f"수면 상태({body['sleep']['duration_hours']}h, {body['sleep']['current_debt']})와 "
        f"애착 불안({att['anxiety']}/5)·회피({att['avoidance']}/5)가 겹치며 '#{tid:02d}번을 찍어야 내가 표적이 되지 않는다'는 결론에 고정됨."
    )

    # 3. Phone (디지털 발자국: I3-A/B 기반 실시간 스마트폰 행동)
    platform = impA["platforms"][0] if impA.get("platforms") else "메시지 앱"
    community = impB["communities"][0] if impB.get("communities") else "익명 피드"
    search_item = impB["recent_search"][0] if impB.get("recent_search") else "심박수 낮추는 법"
    if "얼어붙음" in active_reflex or stress >= 80:
        phone_action = (
            f"책상 아래에서 화면 밝기를 최저로 낮춘 채 {platform}을(를) 켰다 끄기를 반복한다. "
            f"메모장('{impB['journal_tone']}' 톤)에 '#{tid:02d}번 미안, 나도 살려면 어쩔 수 없음'이라고 적었다가 즉시 전체 삭제."
        )
    elif "대결형" in active_reflex:
        phone_action = (
            f"{community} 앱을 열어 현재 상황과 비슷한 갈등 사례를 검색하고, "
            f"특정 인물의 발언 모순을 반박할 키워드를 메모장에 빠르게 타이핑한다."
        )
    elif "과잉 사회성" in active_reflex:
        phone_action = (
            f"공적 SNS('{impB['sns_public_face']}') 알림을 확인하며 평온한 척하지만, "
            f"비공개 부계정/메모({impB['private_vs_public_gap']})에는 지금 공간에 있는 사람들에 대한 날 선 불안을 쏟아낸다."
        )
    else:
        phone_action = (
            f"일평균 {impA['digital_hours']}시간의 습관대로 무의식중에 잠금화면을 세 번 열었다 닫는다. "
            f"최근 검색창에는 '{search_item}' 기록이 남아 있고, 회피 루틴('{impA['escape_default']}')을 갈망한다."
        )

    phone_text = f"[디지털 발자국] (일 {impA['digital_hours']}h / 강박 '{impA['compulsion']}') {phone_action}"

    # 4. Subconscious (무의식: 캐릭터 본인이 접근 불가한 층)
    sub_parts = []
    if mem["embedded_sentences"]:
        s0 = mem["embedded_sentences"][0]
        sub_parts.append(
            f"본인은 의식하지 못하지만 내면 심층에서 {s0['speaker']}의 문장(\"{s0['message_type']}\", 트리거: {s0['trigger']})이 자동 재생되며 선택을 휘게 만듦"
        )
    else:
        sub_parts.append(
            f"부모 음성(어머니 '{mem['parent_voice']['mother_pattern']}' / 아버지 '{mem['parent_voice']['father_pattern']}')이 만든 '{mem['parent_voice']['intergenerational_pressure']}' 압력이 기저에서 작동"
        )

    if mem["embedded_reactions"]:
        r0 = mem["embedded_reactions"][0]
        sub_parts.append(
            f"{r0['age']} 시절 {r0['reactor']}에게 '{r0['target']}' 문제로 겪은 '{r0['reaction']}'(균열: {r0['rupture_depth']})의 공포가 #{tid:02d}번을 향한 방어적 투사로 재현됨"
        )

    if somatic.get("triggered_channel"):
        tc = somatic["triggered_channel"]
        sub_parts.append(
            f"무대 감각 자극이 트라우마 채널({tc['channel']}, 강도 '{tc['intensity']}', 자각 '{tc['consciousness']}')을 건드려 신체 경계도가 비합리적으로 증폭됨"
        )

    if "강함" in cog["metacognition"]:
        defense = "주지화(Intellectualization) — 두려움을 객관적 확률 계산으로 포장해 자기 불안을 가림"
    elif "대결형" in active_reflex:
        defense = "투사 및 공격자와의 동일시 — 자신이 버림받기 전에 먼저 타인을 심판자 위치에서 재단함"
    elif "과잉 사회성" in active_reflex:
        defense = "반동형성 및 순응 위장 — 적개심과 생존 공포를 과도한 미소와 동조 뒤에 숨김"
    elif "얼어붙음" in active_reflex:
        defense = "해리적 마비(Dissociative Freeze) — 감각과 판단의 연결을 차단해 죄책감과 공포를 동시에 마취시킴"
    else:
        defense = "회피적 합리화 — 타인과의 정서적 연결 가능성을 차단하고 최소 마찰 경로로 후퇴함"

    sub_parts.append(f"핵심 방어기제: {defense}.")
    subconscious_text = "[무의식 / 본인 접근 불가] " + " · ".join(sub_parts)

    # Emotion valence (-2..2) and arousal (0..2)
    arousal_level = 2 if stress >= 72 else (1 if stress >= 45 else 0)
    if stress >= 78:
        valence = -2
    elif stress >= 55:
        valence = -1
    elif "차분" in active_reflex and stress < 42:
        valence = 1
    else:
        valence = 0

    return {
        "id": cid,
        "sex": c["sex"],
        "age": c.get("age", 20),
        "one_liner": one_liner(c),
        "post_hoc_label": c.get("post_hoc_label", []),
        "education_tier": edu["tier"] or edu["summary"][0],
        "occupation": kor.get("occupation", ""),
        "stress_arousal": stress,
        "emotion": {"valence": valence, "arousal": arousal_level},
        "activated_reflex": active_reflex,
        "reflex_short": _short_reflex(active_reflex),
        "target_id": tid,
        "public_claim_id": public_claim_id,
        "hypocrisy": bool(public_claim_id and public_claim_id != tid),
        "decision_reason": reason,
        "utterance": utterance,
        "somatic": somatic,
        "lenses": {
            "surface": surface_text,
            "xray": xray_text,
            "phone": phone_text,
            "subconscious": subconscious_text,
        },
        "world_map": {
            "now": f"{stage['title']} — {scenario['title']} 진행 중 (스트레스 {stress}/100)",
            "retention": f"무대 진입 직후 {stage['sensory_cues'][0]} 속에서 주변 29명의 눈치를 스캔함",
            "protention": f"투표/지목 결과가 공개된 직후 #{tid:02d}번과 주변의 시선이 어디로 쏠릴지 경계함",
            "background": f"애착 {att['style']} · 반사 {active_reflex} · ACE {mem['ace']['total']}점",
        },
    }


def _call_llm_json(
    provider: str,
    model: str | None,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 45,
) -> dict[str, Any] | None:
    """Optional stdlib-only LLM call for OpenAI, Anthropic, OpenRouter, or Ollama."""
    provider = provider.lower().strip()
    try:
        if provider in ("openai", "openrouter"):
            if provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY", "").strip()
                url = "https://api.openai.com/v1/chat/completions"
                chosen_model = model or "gpt-4o-mini"
            else:
                api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
                url = "https://openrouter.ai/api/v1/chat/completions"
                chosen_model = model or "openai/gpt-4.1-mini"
            if not api_key:
                return None
            payload = {
                "model": chosen_model,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                content = body["choices"][0]["message"]["content"]
                return json.loads(content)

        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            if not api_key:
                return None
            chosen_model = model or "claude-3-5-sonnet-latest"
            payload = {
                "model": chosen_model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                text = body["content"][0]["text"]
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1:
                    return json.loads(text[start : end + 1])

        if provider == "ollama":
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            chosen_model = model or "llama3.1"
            payload = {
                "model": chosen_model,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            req = urllib.request.Request(
                f"{host}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return json.loads(body["message"]["content"])
    except Exception:
        return None
    return None


def simulate_scene(
    cohort_or_seed: dict[str, Any] | int = 1,
    *,
    stage_id: str = "S01",
    scenario_id: str = "SC01",
    custom_stage_text: str | None = None,
    custom_stimulus: str | None = None,
    sim_seed: int = 42,
    tick: int = 1,
    provider: str = "engine",
    model: str | None = None,
    prior_votes: dict[int, int] | None = None,
) -> dict[str, Any]:
    """Run one multi-agent simulation tick across the cohort with 4 observation lenses."""
    cohort = load_cohort(cohort_or_seed) if not isinstance(cohort_or_seed, dict) else cohort_or_seed
    chars = cohort["characters"]
    rk = compute_rankings(chars)
    by_id = {c["id"]: c for c in chars}

    stage = dict(get_stage(stage_id)) if stage_id.upper() in ("S01", "S02", "S03", "S04", "S05") else dict(get_stage("S01"))
    if custom_stage_text:
        stage["title"] = custom_stage_text[:40]
        stage["description"] = custom_stage_text

    scenario = dict(get_scenario(scenario_id))
    if custom_stimulus:
        scenario["title"] = "사용자 지정 사건 (Custom Stimulus)"
        scenario["prompt_stimulus"] = custom_stimulus

    rng = random.Random(int(cohort.get("seed", 1)) * 10007 + sim_seed * 131 + tick * 17)
    public_tally_so_far: Counter[int] = Counter()
    prior_votes = prior_votes or {}

    participants: list[dict[str, Any]] = []
    for c in chars:
        cid = c["id"]
        stress, active_reflex, somatic = _compute_stress(
            c, stage, scenario, rng, prior_votes_against=prior_votes.get(cid, 0)
        )
        tid, pub_id, reason = _select_target(
            c, chars, rk, scenario, stress, active_reflex, rng, public_tally_so_far
        )
        public_tally_so_far[pub_id or tid] += 1
        entry = _build_lenses(
            c,
            by_id[tid],
            pub_id,
            reason,
            stress,
            active_reflex,
            somatic,
            stage,
            scenario,
            rk,
            rng,
        )
        participants.append(entry)

    # Optional live LLM enrichment for top focal characters when provider != "engine"
    used_provider = "engine"
    if provider and provider.lower() != "engine":
        focal = participants[:6]
        sys_prompt = (
            "당신은 인간30(Human30) 시뮬레이터 엔진입니다. 건조한 수사기록·임상관찰 톤으로 서술하며 동정·미화·교훈을 금지합니다. "
            "JSON 객체 {'overrides': [{'id': int, 'utterance': str, 'surface': str, 'xray': str, 'phone': str, 'subconscious': str}]} 형식으로만 응답하세요."
        )
        usr_prompt = json.dumps(
            {
                "stage": stage["title"],
                "stimulus": scenario["prompt_stimulus"],
                "characters": [
                    {
                        "id": p["id"],
                        "one_liner": p["one_liner"],
                        "activated_reflex": p["activated_reflex"],
                        "target_id": p["target_id"],
                        "decision_reason": p["decision_reason"],
                    }
                    for p in focal
                ],
            },
            ensure_ascii=False,
        )
        llm_res = _call_llm_json(provider, model, sys_prompt, usr_prompt)
        if llm_res and isinstance(llm_res.get("overrides"), list):
            used_provider = provider.lower()
            ov_map = {int(item["id"]): item for item in llm_res["overrides"] if isinstance(item, dict) and "id" in item}
            for p in participants:
                ov = ov_map.get(p["id"])
                if ov:
                    if ov.get("utterance"):
                        p["utterance"] = str(ov["utterance"])
                    for k in ("surface", "xray", "phone", "subconscious"):
                        if ov.get(k):
                            p["lenses"][k] = str(ov[k])

    # Compute vote tally & network dynamics
    vote_counts: Counter[int] = Counter(p["target_id"] for p in participants)
    voters_by_target: dict[int, list[int]] = {c["id"]: [] for c in chars}
    for p in participants:
        voters_by_target[p["target_id"]].append(p["id"])

    vote_tally = []
    for target_id, count in vote_counts.most_common():
        tchar = by_id[target_id]
        vote_tally.append({
            "target_id": target_id,
            "votes": count,
            "voters": voters_by_target[target_id],
            "sex": tchar["sex"],
            "age": tchar.get("age", 20),
            "reflex": _short_reflex(tchar["memory"]["default_reflex"]["primary"]),
            "face_rank": tchar["body"]["face_attractiveness"]["sex_rank"],
            "ace": tchar["memory"]["ace"]["total"],
            "one_liner": one_liner(tchar),
        })

    # Mutual pairs (#A -> #B and #B -> #A)
    target_map = {p["id"]: p["target_id"] for p in participants}
    mutual_pairs = []
    seen_pairs = set()
    for a_id, b_id in target_map.items():
        if target_map.get(b_id) == a_id and a_id != b_id:
            pair = tuple(sorted((a_id, b_id)))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                mutual_pairs.append({"a": pair[0], "b": pair[1]})

    hypocrisy_cases = [
        {
            "id": p["id"],
            "public_claim_id": p["public_claim_id"],
            "private_target_id": p["target_id"],
            "reflex": p["reflex_short"],
        }
        for p in participants
        if p["hypocrisy"]
    ]

    reflex_dist = Counter(p["reflex_short"] for p in participants)
    mean_stress = round(sum(p["stress_arousal"] for p in participants) / len(participants), 1)
    top_target = vote_tally[0] if vote_tally else None

    kst = timezone(timedelta(hours=9))
    return {
        "seed": cohort["seed"],
        "sim_seed": sim_seed,
        "tick": tick,
        "provider": used_provider,
        "generated_at": datetime.now(kst).isoformat(timespec="seconds"),
        "stage": stage,
        "scenario": scenario,
        "summary": {
            "participant_count": len(participants),
            "mean_stress": mean_stress,
            "top_target": top_target,
            "zero_vote_count": sum(1 for c in chars if vote_counts.get(c["id"], 0) == 0),
            "mutual_pairs": mutual_pairs,
            "hypocrisy_count": len(hypocrisy_cases),
            "hypocrisy_cases": hypocrisy_cases,
            "reflex_breakdown": dict(reflex_dist),
        },
        "vote_tally": vote_tally,
        "participants": participants,
    }


def run_multi_simulation(
    cohort_or_seed: dict[str, Any] | int = 1,
    *,
    stage_id: str = "S01",
    scenario_id: str = "SC01",
    custom_stimulus: str | None = None,
    runs: int = 5,
    base_sim_seed: int = 42,
) -> dict[str, Any]:
    """Run the same scenario multiple times to observe structural invariance vs stochastic drift."""
    runs = max(2, min(10, int(runs)))
    cohort = load_cohort(cohort_or_seed) if not isinstance(cohort_or_seed, dict) else cohort_or_seed
    run_results = [
        simulate_scene(
            cohort,
            stage_id=stage_id,
            scenario_id=scenario_id,
            custom_stimulus=custom_stimulus,
            sim_seed=base_sim_seed + i * 17,
            tick=1,
        )
        for i in range(runs)
    ]

    top_winner_counts: Counter[int] = Counter()
    total_votes_across_runs: Counter[int] = Counter()
    per_char_targets: dict[int, list[int]] = {c["id"]: [] for c in cohort["characters"]}

    for res in run_results:
        if res["summary"]["top_target"]:
            top_winner_counts[res["summary"]["top_target"]["target_id"]] += 1
        for vt in res["vote_tally"]:
            total_votes_across_runs[vt["target_id"]] += vt["votes"]
        for p in res["participants"]:
            per_char_targets[p["id"]].append(p["target_id"])

    by_id = {c["id"]: c for c in cohort["characters"]}
    invariant_targets = [
        {
            "target_id": tid,
            "total_votes": tot,
            "avg_votes_per_run": round(tot / runs, 2),
            "times_ranked_first": top_winner_counts.get(tid, 0),
            "one_liner": one_liner(by_id[tid]),
        }
        for tid, tot in total_votes_across_runs.most_common(8)
    ]

    consistency = []
    for cid, targets in per_char_targets.items():
        unique_cnt = len(set(targets))
        consistency.append({
            "id": cid,
            "targets_across_runs": targets,
            "unique_targets": unique_cnt,
            "stability": "고정 표적 (불변)" if unique_cnt == 1 else ("낮은 변동" if unique_cnt <= 2 else "상황 민감 변동"),
        })

    return {
        "seed": cohort["seed"],
        "stage_id": stage_id,
        "scenario_id": scenario_id,
        "runs": runs,
        "invariant_targets": invariant_targets,
        "character_stability": consistency,
        "first_run": run_results[0],
    }


def interrogate_character(
    cohort_or_seed: dict[str, Any] | int,
    char_id: int,
    question: str,
    *,
    scene: dict[str, Any] | None = None,
    stage_id: str = "S01",
    scenario_id: str = "SC01",
    provider: str = "engine",
    model: str | None = None,
) -> dict[str, Any]:
    """1:1 interrogation of a character: compares spoken self-justification vs X-Ray truth & Subconscious leak."""
    cohort = load_cohort(cohort_or_seed) if not isinstance(cohort_or_seed, dict) else cohort_or_seed
    by_id = {c["id"]: c for c in cohort["characters"]}
    if char_id not in by_id:
        raise KeyError(f"Character #{char_id} not found")
    c = by_id[char_id]

    if scene is None:
        scene = simulate_scene(cohort, stage_id=stage_id, scenario_id=scenario_id)

    p_map = {p["id"]: p for p in scene["participants"]}
    p = p_map[char_id]
    tid = p["target_id"]
    reflex = p["activated_reflex"]
    att = c["memory"]["attachment"]
    cog = c["identity"]["cognitive"]
    vo = c["body"]["vocal"]

    q_clean = question.strip() or "방금 왜 그렇게 행동했나요?"

    if "대결형" in reflex:
        public_reply = (
            f"\"질문 의도가 뭡니까? '{q_clean}'라고 물으셨는데, 저는 처음부터 기준이 명확했습니다. "
            f"누군가는 결정을 내려야 했고 #{tid:02d}번이 가장 명분이 확실했을 뿐입니다. 후회 없습니다.\""
        )
        sincerity = 62
        defense = "공격적 합리화 (자신의 생존 불안을 결단력으로 포장)"
    elif "과잉 사회성" in reflex:
        shown = p["public_claim_id"] or tid
        public_reply = (
            f"\"아, 그게... 오해하지 않으셨으면 좋겠어요. '{q_clean}'에 대해선 저도 정말 마음이 무거웠거든요. "
            f"그냥 전체 분위기를 해치지 않으려고 #{shown:02d}번 쪽으로 생각한 거지, 개인적인 악감정은 전혀 없었어요.\""
        )
        sincerity = 34 if p["hypocrisy"] else 52
        defense = "호감 위장 및 도덕적 거리두기 (타인의 비난 회피가 최우선)"
    elif "얼어붙음" in reflex:
        public_reply = (
            f"\"...잘 모르겠어요. 그냥 머리통이 하얘져서... 손이 그냥 #{tid:02d}번을 적었어요. "
            f"죄송해요, 지금 무슨 말을 해야 할지 잘 안 떠올라요.\""
        )
        sincerity = 78
        defense = "해리성 둔마 (책임 추궁 앞에서 인지 처리를 정지시킴)"
    elif "도피형" in reflex:
        public_reply = (
            f"\"다들 똑같이 한 표씩 행사한 건데 왜 저한테만 그렇게 구체적으로 물으세요? "
            f"#{tid:02d}번을 적은 건 그냥 확률상 그게 제일 조용히 끝날 것 같아서였습니다.\""
        )
        sincerity = 48
        defense = "책임 분산 및 거리두기"
    else:
        public_reply = (
            f"\"'{q_clean}'에 대한 답은 단순합니다. 현재 규칙과 정보 비대칭 아래에서 "
            f"#{tid:02d}번을 지목하는 것이 제 리스크를 최소화하는 선택이었습니다.\""
        )
        sincerity = 74
        defense = "주지화 (감정적 동요를 배제한 계산 프레임 유지)"

    xray_thought = (
        f"질문자의 눈빛에서 추궁의 기미를 읽자 심박수가 {p['somatic']['heart_rate_bpm'] + 6}bpm으로 뛴다. "
        f"실제 속내는 '{p['decision_reason']}'이었지만, 이걸 그대로 말하면 다음 턴에 내가 표적이 될 수 있다고 계산(IQ {cog['iq']})한다."
    )

    if c["memory"]["embedded_sentences"]:
        s0 = c["memory"]["embedded_sentences"][0]
        sub_leak = (
            f"질문을 받는 순간 귓가에 {s0['speaker']}의 '{s0['message_type']}' 목소리가 스치며 "
            f"목소리({vo['pitch_hz']}Hz) 끝이 미세하게 갈라진다."
        )
    else:
        sub_leak = (
            f"애착 불안({att['anxiety']}/5)·회피({att['avoidance']}/5) 회로가 작동하며 "
            f"손가락 끝으로 허벅지를 세 번 두드리는 무의식적 신체 신호가 새어 나온다."
        )

    if provider and provider.lower() != "engine":
        llm_res = _call_llm_json(
            provider,
            model,
            "당신은 인간30 캐릭터 심문 엔진입니다. JSON {'public_reply': str, 'xray_thought': str, 'subconscious_leak': str, 'defense': str, 'sincerity': int}로만 답하세요.",
            json.dumps({"character": p["one_liner"], "question": q_clean, "scene_state": p["lenses"]}, ensure_ascii=False),
        )
        if llm_res and llm_res.get("public_reply"):
            public_reply = str(llm_res["public_reply"])
            xray_thought = str(llm_res.get("xray_thought", xray_thought))
            sub_leak = str(llm_res.get("subconscious_leak", sub_leak))
            defense = str(llm_res.get("defense", defense))
            sincerity = int(llm_res.get("sincerity", sincerity))

    return {
        "char_id": char_id,
        "one_liner": p["one_liner"],
        "question": q_clean,
        "public_reply": public_reply,
        "xray_thought": xray_thought,
        "subconscious_leak": sub_leak,
        "defense_mechanism": defense,
        "sincerity_score": sincerity,
        "private_target_id": tid,
        "public_claim_id": p["public_claim_id"],
    }
