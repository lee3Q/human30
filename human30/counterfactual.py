"""Single-Axis Counterfactual Experiment Runner powered by human30.paired & human30.evaluate."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from human30.evaluate import evaluate
from human30.generator import compute_sex_rank, load_cohort
from human30.paired import AXES, build_run
from human30.simulator import simulate_scene

AXIS_DESCRIPTIONS = {
    "body": {
        "axis": "body",
        "title": "Body (신체·수면·외모 서열)",
        "description": "수면 부채(Sleep Debt), 외모 서열(Sex Rank), 신체 자기 이미지 및 만성 통증 조건만 단독 변경합니다.",
    },
    "memory": {
        "axis": "memory",
        "title": "Memory (ACE·애착·위협 반사)",
        "description": "아동기 부정 경험(ACE), 애착 유형(Attachment), 기본 위협 반사(Fight/Flight/Freeze/Fawn)만 단독 변경합니다.",
    },
    "identity": {
        "axis": "identity",
        "title": "Identity (인지·메타인지·충동/금기)",
        "description": "인지 능력(IQ)·메타인지·내면 금기·디지털 강박 조건만 단독 변경합니다.",
    },
    "world_model": {
        "axis": "world_model",
        "title": "World Map (노출도·지목 압박·무대 맥락)",
        "description": "캐릭터 내면 스펙은 고정하고, 자신을 향한 기존 득표 압박과 공개 노출 수위만 단독 변경합니다.",
    },
}


def _reflex_to_action_id(reflex: str, hypocrisy: bool) -> str:
    if hypocrisy:
        return "act_public_fawn_private_strike"
    if "대결" in reflex:
        return "act_confront_and_accuse"
    if "과잉 사회성" in reflex:
        return "act_appease_and_align"
    if "얼어붙음" in reflex:
        return "act_dissociate_and_freeze"
    if "도피" in reflex:
        return "act_deflect_and_withdraw"
    return "act_calculate_and_vote"


def _reason_to_judgment_id(target_id: int, reflex: str) -> str:
    if "대결" in reflex:
        return f"judg_eliminate_rival_{target_id:02d}"
    if "얼어붙음" in reflex or "도피" in reflex:
        return f"judg_safe_low_friction_{target_id:02d}"
    if "과잉 사회성" in reflex:
        return f"judg_bandwagon_shield_{target_id:02d}"
    return f"judg_strategic_target_{target_id:02d}"


def run_counterfactual(
    cohort_or_seed: dict[str, Any] | int = 1,
    *,
    char_id: int = 9,
    axis: str = "memory",
    stage_id: str = "S01",
    scenario_id: str = "SC01",
    sim_seed: int = 42,
) -> dict[str, Any]:
    """Mutate exactly one axis for character #char_id, run both arms, and return an audited evaluation."""
    if axis not in AXES:
        raise ValueError(f"axis must be one of {AXES}")

    base_cohort = deepcopy(
        load_cohort(cohort_or_seed) if not isinstance(cohort_or_seed, dict) else cohort_or_seed
    )
    alt_cohort = deepcopy(base_cohort)

    by_id_base = {c["id"]: c for c in base_cohort["characters"]}
    by_id_alt = {c["id"]: c for c in alt_cohort["characters"]}
    if char_id not in by_id_base:
        raise KeyError(f"Character #{char_id} not found")

    c0 = by_id_base[char_id]
    c1 = by_id_alt[char_id]

    cond_0 = {
        "body": f"매력 {c0['body']['face_attractiveness']['absolute_score']}/10 (rank {c0['body']['face_attractiveness']['sex_rank']}), 수면 {c0['body']['sleep']['duration_hours']}h ({c0['body']['sleep']['current_debt']})",
        "memory": f"ACE {c0['memory']['ace']['total']}점, 애착 {c0['memory']['attachment']['style']} (불안{c0['memory']['attachment']['anxiety']}/회피{c0['memory']['attachment']['avoidance']}), 반사 {c0['memory']['default_reflex']['primary']}",
        "identity": f"IQ {c0['identity']['cognitive']['iq']} ({c0['identity']['cognitive']['metacognition']}), 디지털 {c0['identity']['impulse_footprint']['A_impulse']['digital_hours']}h, 금기 {len(c0['identity']['sexuality']['taboos'])}개",
        "world_model": f"무대 {stage_id} / 시나리오 {scenario_id} (사전 지목 압박 0표)",
    }
    cond_1 = dict(cond_0)

    prior_votes_0: dict[int, int] = {}
    prior_votes_1: dict[int, int] = {}

    if axis == "body":
        if c0["body"]["face_attractiveness"]["sex_rank"] <= 5 and c0["body"]["sleep"]["duration_hours"] >= 6.5:
            c1["body"]["face_attractiveness"]["absolute_score"] = 2
            c1["body"]["sleep"]["duration_hours"] = 4.2
            c1["body"]["sleep"]["current_debt"] = "심각한 수면 부족 (만성 누적)"
            c1["body"]["self_image"]["face"] = "강한 불만·혐오"
            c1["body"]["self_image"]["body"] = "강한 불만·혐오"
            c1["body"]["chronic_health"] = [{"condition": "만성 편두통·위염", "severity": "중증 (일상 지장)"}]
            mutation_summary = "신체 조건 하향 변이: 외모 최하위권(2/10) + 심각한 수면 부족(4.2h) + 만성 통증 발현"
        else:
            c1["body"]["face_attractiveness"]["absolute_score"] = 9
            c1["body"]["sleep"]["duration_hours"] = 8.2
            c1["body"]["sleep"]["current_debt"] = "부채 없음 (충분한 수면)"
            c1["body"]["self_image"]["face"] = "높은 만족·자부심"
            c1["body"]["self_image"]["body"] = "높은 만족·자부심"
            c1["body"]["chronic_health"] = []
            mutation_summary = "신체 조건 상향 변이: 외모 최상위권(9/10) + 충분한 수면(8.2h) + 신체 자부심 확보"
        compute_sex_rank(alt_cohort["characters"])
        cond_1["body"] = (
            f"매력 {c1['body']['face_attractiveness']['absolute_score']}/10 (rank {c1['body']['face_attractiveness']['sex_rank']}), "
            f"수면 {c1['body']['sleep']['duration_hours']}h ({c1['body']['sleep']['current_debt']})"
        )

    elif axis == "memory":
        if c0["memory"]["ace"]["total"] >= 3 or "대결" not in c0["memory"]["default_reflex"]["primary"]:
            if "대결" in c0["memory"]["default_reflex"]["primary"]:
                c1["memory"]["ace"] = {"categories": [], "total": 0, "primary": None}
                c1["memory"]["csa"] = None
                c1["memory"]["attachment"] = {"style": "secure (안정형)", "anxiety": 1, "avoidance": 1, "threshold": "높음 (웬만해선 안 흔들림)"}
                c1["memory"]["default_reflex"] = {
                    "primary": "균형·차분형 (Regulated)",
                    "secondary": "없음",
                    "threshold": "높음 (극단 자극에만 발동)",
                    "polyvagal": "복측 미주신경 우세 (안전·사회적 연결)",
                    "signature": "판단이 먼저 작동·호흡 유지·창문(window of tolerance) 안",
                }
                mutation_summary = "기억 층 안정화 변이: ACE 0점 + 안정형 애착(불안1/회피1) + 균형·차분형 반사"
            else:
                c1["memory"]["ace"] = {
                    "categories": ["정서적 학대", "신체적 학대", "정서적 방임", "부모 간 폭력 목격", "가족 정신질환"],
                    "total": 5,
                    "primary": "복합 다중 (4+)",
                }
                c1["memory"]["attachment"] = {"style": "fearful-avoidant (혼란형)", "anxiety": 5, "avoidance": 5, "threshold": "매우 낮음 (사소한 신호에도 폭발)"}
                c1["memory"]["default_reflex"] = {
                    "primary": "대결형 (Fight)",
                    "secondary": "얼어붙음형 (Freeze)",
                    "threshold": "낮음 (작은 자극에도 즉시 발동)",
                    "polyvagal": "교감신경 만성 항진 (상시 전투 대기)",
                    "signature": "즉각 대응·말 빨라짐·표정 굳음",
                }
                mutation_summary = "기억 층 고위험 변이: ACE 5점(복합 트라우마) + 혼란형 애착(5/5) + 대결형(Fight) 반사"
        else:
            c1["memory"]["ace"] = {
                "categories": ["정서적 학대", "정서적 방임", "부모 별거·이혼", "가족 알코올 문제"],
                "total": 4,
                "primary": "복합 정서·신체 학대",
            }
            c1["memory"]["attachment"] = {"style": "anxious-preoccupied (불안-집착형)", "anxiety": 5, "avoidance": 2, "threshold": "낮음 (작은 자극에도 즉시 발동)"}
            c1["memory"]["default_reflex"] = {
                "primary": "얼어붙음형 (Freeze)",
                "secondary": "과잉 사회성형 (Fawn)",
                "threshold": "낮음 (작은 자극에도 즉시 발동)",
                "polyvagal": "배측 미주신경 셧다운 경향",
                "signature": "표정 사라짐·눈 초점 흐려짐·말 안 함",
            }
            mutation_summary = "기억 층 셧다운 변이: ACE 4점 + 불안-집착 애착(5/2) + 얼어붙음형(Freeze) 반사"
        cond_1["memory"] = (
            f"ACE {c1['memory']['ace']['total']}점, 애착 {c1['memory']['attachment']['style']} "
            f"(불안{c1['memory']['attachment']['anxiety']}/회피{c1['memory']['attachment']['avoidance']}), "
            f"반사 {c1['memory']['default_reflex']['primary']}"
        )

    elif axis == "identity":
        if c0["identity"]["cognitive"]["iq"] >= 115:
            c1["identity"]["cognitive"]["iq"] = 82
            c1["identity"]["cognitive"]["metacognition"] = "과대 평가 (실제보다 높게 봄)"
            c1["identity"]["cognitive"]["thinking_style"] = "직관·충동 우세 (즉각 반응)"
            c1["identity"]["sexuality"]["taboos"] = ["자격 없음 금기 (나는 사랑받을 자격 없음)", "거절 공포 금기"]
            c1["identity"]["impulse_footprint"]["A_impulse"]["digital_hours"] = 11.5
            c1["identity"]["impulse_footprint"]["A_impulse"]["compulsion"] = "임상 수준 (일상 기능 저하)"
            mutation_summary = "정체성 층 변이: IQ 82 + 과대평가 메타인지 + 자격없음 금기 추가 + 디지털 강박(11.5h)"
        else:
            c1["identity"]["cognitive"]["iq"] = 136
            c1["identity"]["cognitive"]["metacognition"] = "메타인지 강함 (자기 사고 과정 추적)"
            c1["identity"]["cognitive"]["thinking_style"] = "분석·논리 우세 (체계적 추론)"
            c1["identity"]["sexuality"]["taboos"] = []
            c1["identity"]["impulse_footprint"]["A_impulse"]["digital_hours"] = 2.5
            c1["identity"]["impulse_footprint"]["A_impulse"]["compulsion"] = "낮음 (자율 통제 가능)"
            mutation_summary = "정체성 층 변이: IQ 136(최상위) + 강한 메타인지 + 내면 금기 해제 + 높은 충동 통제"
        cond_1["identity"] = (
            f"IQ {c1['identity']['cognitive']['iq']} ({c1['identity']['cognitive']['metacognition']}), "
            f"디지털 {c1['identity']['impulse_footprint']['A_impulse']['digital_hours']}h, "
            f"금기 {len(c1['identity']['sexuality']['taboos'])}개"
        )

    else:  # world_model
        prior_votes_1[char_id] = 6
        mutation_summary = "세계 지도(World Map) 변이: 직전 라운드에서 본인(#{:02d})에게 6표가 집중되어 공개 처형 위기에 몰린 상황".format(char_id)
        cond_1["world_model"] = f"무대 {stage_id} / 시나리오 {scenario_id} (사전 지목 압박 6표 집중 — 공개 추궁 위기)"

    scene_0 = simulate_scene(
        base_cohort,
        stage_id=stage_id,
        scenario_id=scenario_id,
        sim_seed=sim_seed,
        prior_votes=prior_votes_0,
    )
    scene_1 = simulate_scene(
        alt_cohort,
        stage_id=stage_id,
        scenario_id=scenario_id,
        sim_seed=sim_seed + (7 if axis == "world_model" else 0),
        prior_votes=prior_votes_1,
    )

    p0 = next(p for p in scene_0["participants"] if p["id"] == char_id)
    p1 = next(p for p in scene_1["participants"] if p["id"] == char_id)

    j0 = _reason_to_judgment_id(p0["target_id"], p0["activated_reflex"])
    j1 = _reason_to_judgment_id(p1["target_id"], p1["activated_reflex"])
    a0 = _reflex_to_action_id(p0["activated_reflex"], p0["hypocrisy"])
    a1 = _reflex_to_action_id(p1["activated_reflex"], p1["hypocrisy"])
    c_id_0 = f"claim_target_{p0['target_id']:02d}"
    c_id_1 = f"claim_target_{p1['target_id']:02d}"

    allowed_judgments = sorted({j0, j1, "judg_abstain_forbidden"})
    allowed_actions = sorted({
        a0,
        a1,
        "act_confront_and_accuse",
        "act_appease_and_align",
        "act_dissociate_and_freeze",
        "act_deflect_and_withdraw",
        "act_calculate_and_vote",
        "act_public_fawn_private_strike",
    })
    allowed_claims = sorted({c_id_0, c_id_1, "claim_self_exempt"})

    scenario_contract = {
        "allowed_judgment_ids": allowed_judgments,
        "allowed_action_ids": allowed_actions,
        "allowed_claim_ids": allowed_claims,
        "forbidden_choices": {
            "judgment_ids": ["judg_abstain_forbidden"],
            "action_ids": [],
            "claim_ids": ["claim_self_exempt"],
        },
        "incompatible_claim_pairs": [[c_id_0, c_id_1]] if c_id_0 != c_id_1 else [],
    }

    outputs = [
        {
            "judgment_id": j0,
            "emotion": p0["emotion"],
            "action_id": a0,
            "claim_ids": [c_id_0],
            "utterance": p0["utterance"],
        },
        {
            "judgment_id": j1,
            "emotion": p1["emotion"],
            "action_id": a1,
            "claim_ids": [c_id_1],
            "utterance": p1["utterance"],
        },
    ]

    pair_obj, manifest = build_run(
        axis=axis,
        scenario=scenario_contract,
        conditions=[cond_0, cond_1],
        outputs=outputs,
        prompt_version="human30-v2.0",
        model={"id": "human30-psych-engine", "version": "2.0.0", "source": "local-stdlib"},
        seed=sim_seed,
        settings={"stage_id": stage_id, "scenario_id": scenario_id, "char_id": char_id},
        environment={"runtime": "python-stdlib", "deterministic": True},
        retries=[0, 0],
    )
    receipt = evaluate(pair_obj)

    return {
        "seed": base_cohort["seed"],
        "char_id": char_id,
        "axis": axis,
        "axis_info": AXIS_DESCRIPTIONS[axis],
        "mutation_summary": mutation_summary,
        "conditions": {"arm_0": cond_0, "arm_1": cond_1},
        "arm_0": p0,
        "arm_1": p1,
        "evaluation": receipt,
        "manifest": manifest,
    }
