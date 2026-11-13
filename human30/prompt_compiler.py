"""Portable Prompt Bundle Compiler for Claude, ChatGPT, Gemini, and Local LLMs."""

from __future__ import annotations

from typing import Any

from human30.cards import compute_rankings, education_context, one_liner
from human30.catalog import get_scenario, get_stage
from human30.generator import load_cohort


def _compact_character_block(c: dict[str, Any], rk: dict[int, Any]) -> str:
    b = c["body"]
    m = c["memory"]
    ident = c["identity"]
    kor = c["korea"]
    edu = education_context(c)
    vo = b["vocal"]
    att = m["attachment"]
    reflex = m["default_reflex"]
    cog = ident["cognitive"]
    sx = ident["sexuality"]
    impA = ident["impulse_footprint"]["A_impulse"]
    impB = ident["impulse_footprint"]["B_footprint"]

    sent_str = "; ".join(f"{s['speaker']}:'{s['message_type']}'(@{s['trigger']})" for s in m["embedded_sentences"][:2]) or "없음"
    trig_str = "; ".join(f"{t['channel']}({t['intensity']})" for t in m["trauma_trigger"][:2]) or "없음"
    taboo_str = ", ".join(sx["taboos"][:3]) or "없음"

    return (
        f"### #{c['id']:02d} ({c['sex']}, {c.get('age', 20)}세, {kor['region_voice']['birth_region'].split(' ')[0]})\n"
        f"- **요약**: {one_liner(c)}\n"
        f"- **Body**: 키 {b['height_cm']}cm, BMI {b['body_composition']['bmi']}, 매력 {b['face_attractiveness']['absolute_score']}/10(동성 {b['face_attractiveness']['sex_rank']}위), "
        f"수면 {b['sleep']['duration_hours']}h({b['sleep']['current_debt']}), 음성 {vo['pitch_hz']}Hz/{vo['volume']}/{vo['speech_rate']}, 자기집중={b['self_image']['focused_concern'] or ['없음']}\n"
        f"- **Memory**: ACE {m['ace']['total']}점({', '.join(m['ace']['categories'][:3]) or '없음'}), CSA={'있음' if m['csa'] else '없음'}, "
        f"애착={att['style']}(불안{att['anxiety']}/회피{att['avoidance']}), 기본반사={reflex['primary']}(+{reflex['secondary']}), "
        f"박힌문장=[{sent_str}], 트리거=[{trig_str}]\n"
        f"- **Identity**: IQ {cog['iq']}({cog['strength']}, 메타인지={cog['metacognition']}), 성지향={sx['orientation']}/욕망={sx['desire_intensity']}({sx['desire_grain']}), 금기=[{taboo_str}], "
        f"디지털={impA['digital_hours']}h({impA['compulsion']}, 회피={impA['escape_default']}), 메모톤='{impB['journal_tone']}', 공사간극='{impB['private_vs_public_gap']}'\n"
        f"- **Context**: {edu['narrative']} 직업={kor.get('occupation', '')}, 외모차별={kor['appearance_experience']['discrimination_frequency']}, 억양={kor['region_voice']['accent_intensity']}"
    )


def compile_prompt(
    cohort_or_seed: dict[str, Any] | int = 1,
    *,
    stage_id: str = "S01",
    scenario_id: str = "SC01",
    char_ids: list[int] | None = None,
    custom_stimulus: str | None = None,
) -> dict[str, Any]:
    """Compile a ready-to-paste LLM prompt bundle with 4-layer persona data, stage, and scenario."""
    cohort = load_cohort(cohort_or_seed) if not isinstance(cohort_or_seed, dict) else cohort_or_seed
    chars = cohort["characters"]
    rk = compute_rankings(chars)

    if char_ids:
        wanted = set(char_ids)
        selected = [c for c in chars if c["id"] in wanted]
    else:
        selected = chars

    stage = get_stage(stage_id)
    scenario = dict(get_scenario(scenario_id))
    if custom_stimulus:
        scenario["prompt_stimulus"] = custom_stimulus

    char_blocks = "\n\n".join(_compact_character_block(c, rk) for c in selected)

    prompt_text = f"""# Human30 (인간30) — 4층 다중 에이전트 행동 시뮬레이션 프롬프트 번들

## 1. 시뮬레이션 절대 원칙
- **작용 중심 (Action over Catalog)**: 캐릭터의 프로필 수치를 그대로 읊지 말고, 그 수치가 현재 무대와 자극 아래에서 **어떻게 행동을 휘게 만드는지**만 서술한다.
- **건조한 관찰 톤**: 동정·훈계·도덕적 미화·해피엔딩 강요를 일절 금지한다. 임상 차트 및 수사 기록 톤을 유지한다.
- **내면과 외피의 동시 생성**: 사람은 속마음과 다르게 말하고 행동한다. 반드시 각 캐릭터의 **내면(X-Ray)**과 **무의식(Subconscious)**을 먼저 계산한 뒤, 그 결과로 밖으로 드러난 **외피(Surface)** 행동·발화·투표를 도출한다.

## 2. 현재 무대 (Stage: {stage['id']} — {stage['title']})
- **공간**: {stage['location']}
- **시각**: {stage['time_default']}
- **감각 단서**: {', '.join(stage['sensory_cues'])}
- **설명**: {stage['description']}

## 3. 부여된 사건·자극 (Scenario: {scenario['id']} — {scenario['title']})
> {scenario['prompt_stimulus']}

- **규칙 요약**: {scenario['rules_summary']}

## 4. 참가 캐릭터 데이터 (Seed {cohort['seed']} · 총 {len(selected)}명)

{char_blocks}

---

## 5. 출력 요청 포맷
위 무대와 자극이 주어졌을 때, 각 캐릭터가 보이는 반응을 아래 4개 렌즈로 구분하여 출력하세요:
1. **[Surface / 외피]**: 방 안의 다른 사람들에게 보이는 자세, 표정, 목소리 톤, 실제 발화(또는 침묵), 최종 지목/선택 번호
2. **[X-Ray / 속마음]**: 캐릭터 본인이 의식하는 계산, 심박·호흡 등 신체 반응, 왜 그 표적을 골랐는지에 대한 솔직한 속내
3. **[Phone / 디지털 발자국]**: 테이블 아래에서 스마트폰으로 몰래 하는 행동 (검색어, 메모장 초안, 지운 메시지 등)
4. **[Subconscious / 무의식]**: 캐릭터 본인도 자각하지 못하는 트라우마 트리거, 내면에 박힌 문장(M6/M11)의 재활성화, 작동 중인 방어기제

마지막에는 **전체 득표/지목 집계표**, **겉과 속이 달랐던 위선 사례**, **상호 지목 쌍**을 요약하세요.
"""

    return {
        "seed": cohort["seed"],
        "stage_id": stage["id"],
        "scenario_id": scenario["id"],
        "character_count": len(selected),
        "char_ids": [c["id"] for c in selected],
        "estimated_tokens": len(prompt_text) // 2,
        "prompt": prompt_text,
    }
