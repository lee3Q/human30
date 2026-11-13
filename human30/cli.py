"""Unified Command-Line Interface for Human30 (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from human30.cards import cohort_analytics, one_liner, render_card
from human30.catalog import list_scenarios, list_stages
from human30.counterfactual import run_counterfactual
from human30.generator import generate_cohort, load_cohort, save_cohort
from human30.prompt_compiler import compile_prompt
from human30.simulator import interrogate_character, run_multi_simulation, simulate_scene
from human30.studio import run_studio


def _cmd_studio(args: argparse.Namespace) -> int:
    run_studio(host=args.host, port=args.port, open_browser=args.open)
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    cohort = generate_cohort(
        args.seed,
        count=args.count,
        age_mode=args.age_mode,
        min_age=args.min_age,
        max_age=args.max_age,
    )
    out = Path(args.out) if args.out else None
    try:
        saved = save_cohort(cohort, out, force=args.force)
    except FileExistsError:
        print(f"오류: 시드 {args.seed} 파일이 이미 존재합니다. 덮어쓰려면 --force를 붙이세요.", file=sys.stderr)
        return 2
    print(f"✓ 생성 완료: {saved} (캐릭터 {len(cohort['characters'])}명)")
    return 0


def _cmd_card(args: argparse.Namespace) -> int:
    cohort = load_cohort(args.seed, auto_generate=args.auto_generate)
    ids_arg = args.ids or ["all"]
    if ids_arg == ["all"]:
        if args.json:
            print(json.dumps(cohort["characters"], ensure_ascii=False, indent=2))
        else:
            print(render_card(cohort, None))
        return 0

    by_id = {c["id"]: c for c in cohort["characters"]}
    target_ids = [int(x) for x in ids_arg]
    for cid in target_ids:
        if cid not in by_id:
            print(f"오류: 캐릭터 #{cid}번을 찾을 수 없습니다.", file=sys.stderr)
            return 2
    if args.json:
        print(json.dumps([by_id[cid] for cid in target_ids], ensure_ascii=False, indent=2))
    else:
        for cid in target_ids:
            print(render_card(cohort, cid))
            print()
    return 0


def _cmd_summary(args: argparse.Namespace) -> int:
    cohort = load_cohort(args.seed, auto_generate=True)
    stats = cohort_analytics(cohort)
    print(f"=== Seed {stats['seed']} 군상 요약 ({stats['count']}명 · 평균 IQ {stats['iq_stats']['mean']} · 평균 ACE {stats['ace_stats']['mean']}) ===")
    for c in cohort["characters"]:
        print(one_liner(c))
    print("\n=== 특이 케이스 하이라이트 ===")
    for h in stats["highlights"]:
        print(f"  [{h['tag']}] {h['summary']}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    cohort = load_cohort(args.seed, auto_generate=True)
    stats = cohort_analytics(cohort)
    print(f"=== Seed {stats['seed']} 분포 및 무결성 검증 ===")
    print(f"총 인원: {stats['count']}명 (성비: {stats['sex_ratio']})")
    print(f"IQ: 평균={stats['iq_stats']['mean']}, 범위={stats['iq_stats']['min']}~{stats['iq_stats']['max']}")
    print(f"ACE: 평균={stats['ace_stats']['mean']}, 고위험(4+)={stats['ace_stats']['high_risk_count']}명, 분포={stats['ace_stats']['distribution']}")
    print(f"애착 분포: {stats['attachment_distribution']}")
    print(f"위협 반사 분포: {stats['reflex_distribution']}")
    print("✓ 스키마 및 교차 일관성 정상")
    return 0


def _cmd_simulate(args: argparse.Namespace) -> int:
    cohort = load_cohort(args.seed, auto_generate=True)
    if args.runs > 1:
        multi = run_multi_simulation(
            cohort,
            stage_id=args.stage,
            scenario_id=args.scenario,
            custom_stimulus=args.stimulus,
            runs=args.runs,
            base_sim_seed=args.sim_seed,
        )
        if args.json:
            print(json.dumps(multi, ensure_ascii=False, indent=2))
            return 0
        print(f"=== 다중 실행 분산 비교 (Seed {args.seed} × {args.stage} × {args.scenario} · {args.runs}회 반복) ===")
        for item in multi["invariant_targets"]:
            print(
                f"  표적 #{item['target_id']:02d} : 총 {item['total_votes']:2d}표 "
                f"(평균 {item['avg_votes_per_run']}표/회, 최다득표 {item['times_ranked_first']}/{args.runs}회) — {item['one_liner']}"
            )
        return 0

    scene = simulate_scene(
        cohort,
        stage_id=args.stage,
        scenario_id=args.scenario,
        custom_stimulus=args.stimulus,
        sim_seed=args.sim_seed,
        tick=args.tick,
        provider=args.provider,
        model=args.model,
    )
    if args.out:
        Path(args.out).write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(scene, ensure_ascii=False, indent=2))
        return 0

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  HUMAN 30 시뮬레이션 리포트 — Seed {scene['seed']} | {scene['stage']['id']} {scene['stage']['title']} | {scene['scenario']['id']} {scene['scenario']['title']}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  자극: {scene['scenario']['prompt_stimulus']}")
    print(f"  평균 긴장도: {scene['summary']['mean_stress']}/100 | 겉·속 위선 기표: {scene['summary']['hypocrisy_count']}명 | 반사 분포: {scene['summary']['reflex_breakdown']}")
    print("\n■ 득표 / 지목 상위 집계")
    for vt in scene["vote_tally"][:8]:
        voters_str = ", ".join(f"#{v:02d}" for v in vt["voters"])
        print(f"  · #{vt['target_id']:02d} ({vt['sex']}, {vt['reflex']}, 매력{vt['face_rank']}위) — {vt['votes']}표  ← [{voters_str}]")

    if scene["summary"]["mutual_pairs"]:
        mp_str = ", ".join(f"#{m['a']:02d}↔#{m['b']:02d}" for m in scene["summary"]["mutual_pairs"])
        print(f"\n■ 상호 지목 쌍: {mp_str}")

    focal_ids = [args.char] if args.char else [vt["target_id"] for vt in scene["vote_tally"][:3]]
    p_map = {p["id"]: p for p in scene["participants"]}
    print("\n■ 4-렌즈 심층 관찰 (Surface / X-Ray / Phone / Subconscious)")
    for fid in focal_ids:
        if fid not in p_map:
            continue
        p = p_map[fid]
        print(f"\n─── 캐릭터 #{p['id']:02d} ({p['sex']}, {p['age']}세) → 지목: #{p['target_id']:02d} | 긴장 {p['stress_arousal']}/100 | 반사: {p['activated_reflex']} ───")
        print(f"  {p['lenses']['surface']}")
        print(f"  {p['lenses']['xray']}")
        print(f"  {p['lenses']['phone']}")
        print(f"  {p['lenses']['subconscious']}")
    return 0


def _cmd_interrogate(args: argparse.Namespace) -> int:
    res = interrogate_character(
        args.seed,
        args.char,
        args.question,
        stage_id=args.stage,
        scenario_id=args.scenario,
        provider=args.provider,
    )
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    print(f"━━━ 캐릭터 #{res['char_id']:02d} 1:1 심문 결과 (진실성 {res['sincerity_score']}% · 방어기제: {res['defense_mechanism']}) ━━━")
    print(f"질문: {res['question']}")
    print(f"\n[표면 답변] {res['public_reply']}")
    print(f"\n[X-Ray 속내] {res['xray_thought']}")
    print(f"\n[무의식 누출] {res['subconscious_leak']}")
    return 0


def _cmd_counterfactual(args: argparse.Namespace) -> int:
    res = run_counterfactual(
        args.seed,
        char_id=args.char,
        axis=args.axis,
        stage_id=args.stage,
        scenario_id=args.scenario,
    )
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    ev = res["evaluation"]
    a0 = res["arm_0"]
    a1 = res["arm_1"]
    print(f"━━━ 반사실적 단일축 실험 — Seed {res['seed']} 캐릭터 #{res['char_id']:02d} × [{res['axis'].upper()}] ━━━")
    print(f"변이 요약: {res['mutation_summary']}")
    print(f"독립 평가(evaluate.py): 판단변화={ev['judgment_changed']} (#{a0['target_id']:02d} → #{a1['target_id']:02d}) | 행동변화={ev['action_changed']} | 감정델타={ev['emotion_delta']}")
    print(f"\n[Arm 0 원본] ({res['conditions']['arm_0'][res['axis']]})")
    print(f"  {a0['lenses']['surface']}")
    print(f"  {a0['lenses']['xray']}")
    print(f"\n[Arm 1 변이] ({res['conditions']['arm_1'][res['axis']]})")
    print(f"  {a1['lenses']['surface']}")
    print(f"  {a1['lenses']['xray']}")
    return 0


def _cmd_prompt(args: argparse.Namespace) -> int:
    char_ids = [int(x.strip()) for x in args.chars.split(",") if x.strip()] if args.chars else None
    res = compile_prompt(
        args.seed,
        stage_id=args.stage,
        scenario_id=args.scenario,
        char_ids=char_ids,
        custom_stimulus=args.stimulus,
    )
    if args.out:
        Path(args.out).write_text(res["prompt"], encoding="utf-8")
        print(f"✓ 프롬프트 번들 저장 완료: {args.out} (약 {res['estimated_tokens']} 토큰)")
    else:
        print(res["prompt"])
    return 0


def _cmd_catalog(_args: argparse.Namespace) -> int:
    print("=== 무대 카탈로그 (Stages) ===")
    for st in list_stages():
        print(f"  {st['id']} : {st['title']} ({st['title_en']}) — {st['location']}")
    print("\n=== 시나리오 카탈로그 (Scenarios) ===")
    for sc in list_scenarios():
        print(f"  {sc['id']} : {sc['title']} ({sc['title_en']}) — {sc['rules_summary']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="human30",
        description="Human30 (인간30) — 4층 28표 인간 군상 생성기 & 표층·내면·무의식 다중 에이전트 시뮬레이터",
    )
    sub = parser.add_subparsers(dest="command")

    p_studio = sub.add_parser("studio", help="브라우저 기반 인터랙티브 Human30 웹 스튜디오 실행")
    p_studio.add_argument("--host", default="127.0.0.1")
    p_studio.add_argument("--port", type=int, default=8000)
    p_studio.add_argument("--open", action="store_true", help="브라우저 자동 열기")
    p_studio.set_defaults(func=_cmd_studio)

    p_gen = sub.add_parser("generate", help="시드 번호 기반 30인(또는 N인) 인간 군상 JSON 생성")
    p_gen.add_argument("seed", type=int, help="시드 번호 (예: 7)")
    p_gen.add_argument("--count", type=int, default=30, help="생성할 캐릭터 수 (기본 30)")
    p_gen.add_argument("--age-mode", choices=("default", "diverse", "youth", "adult"), default="default")
    p_gen.add_argument("--min-age", type=int, default=None)
    p_gen.add_argument("--max-age", type=int, default=None)
    p_gen.add_argument("--out", default=None, help="출력 파일 경로")
    p_gen.add_argument("--force", action="store_true", help="기존 시드 파일 덮어쓰기")
    p_gen.set_defaults(func=_cmd_generate)

    p_card = sub.add_parser("card", help="캐릭터 임상 차트 카드 열람")
    p_card.add_argument("seed", type=int, help="시드 번호")
    p_card.add_argument("ids", nargs="*", help="캐릭터 번호(들) 또는 all")
    p_card.add_argument("--json", action="store_true", help="JSON 형식으로 출력")
    p_card.add_argument("--auto-generate", action="store_true", help="시드가 없으면 즉시 생성")
    p_card.set_defaults(func=_cmd_card)

    p_sum = sub.add_parser("summary", help="30명 1줄 요약 및 특이 케이스 하이라이트")
    p_sum.add_argument("seed", type=int, nargs="?", default=1)
    p_sum.set_defaults(func=_cmd_summary)

    p_ver = sub.add_parser("verify", help="코호트 통계 분포 및 성별 교차 일관성 검증")
    p_ver.add_argument("seed", type=int, nargs="?", default=1)
    p_ver.set_defaults(func=_cmd_verify)

    p_sim = sub.add_parser("simulate", help="무대·시나리오 다중 에이전트 시뮬레이션 실행 (4-렌즈 관찰)")
    p_sim.add_argument("--seed", type=int, default=1)
    p_sim.add_argument("--stage", default="S01")
    p_sim.add_argument("--scenario", default="SC01")
    p_sim.add_argument("--stimulus", default=None, help="사용자 지정 사건/자극 문장")
    p_sim.add_argument("--sim-seed", type=int, default=42)
    p_sim.add_argument("--tick", type=int, default=1)
    p_sim.add_argument("--runs", type=int, default=1, help="다중 실행 분산 비교 횟수 (예: 5)")
    p_sim.add_argument("--char", type=int, default=None, help="집중 관찰할 캐릭터 번호")
    p_sim.add_argument("--provider", default="engine", choices=("engine", "openai", "anthropic", "openrouter", "ollama"))
    p_sim.add_argument("--model", default=None)
    p_sim.add_argument("--json", action="store_true")
    p_sim.add_argument("--out", default=None)
    p_sim.set_defaults(func=_cmd_simulate)

    p_int = sub.add_parser("interrogate", help="특정 캐릭터 1:1 심문 (표면 발화 vs 실제 속마음 대조)")
    p_int.add_argument("seed", type=int)
    p_int.add_argument("char", type=int)
    p_int.add_argument("question", help="질문 내용")
    p_int.add_argument("--stage", default="S01")
    p_int.add_argument("--scenario", default="SC01")
    p_int.add_argument("--provider", default="engine")
    p_int.add_argument("--json", action="store_true")
    p_int.set_defaults(func=_cmd_interrogate)

    p_cf = sub.add_parser("counterfactual", help="반사실적 단일축 변이 실험 및 독립 검증")
    p_cf.add_argument("--seed", type=int, default=1)
    p_cf.add_argument("--char", type=int, default=9)
    p_cf.add_argument("--axis", default="memory", choices=("body", "memory", "identity", "world_model"))
    p_cf.add_argument("--stage", default="S01")
    p_cf.add_argument("--scenario", default="SC01")
    p_cf.add_argument("--json", action="store_true")
    p_cf.set_defaults(func=_cmd_counterfactual)

    p_pr = sub.add_parser("prompt", help="Claude/ChatGPT/Gemini용 포터블 프롬프트 번들 생성")
    p_pr.add_argument("--seed", type=int, default=1)
    p_pr.add_argument("--stage", default="S01")
    p_pr.add_argument("--scenario", default="SC01")
    p_pr.add_argument("--chars", default=None, help="콤마로 구분된 캐릭터 번호 (예: 1,4,9,21)")
    p_pr.add_argument("--stimulus", default=None)
    p_pr.add_argument("--out", default=None)
    p_pr.set_defaults(func=_cmd_prompt)

    p_cat = sub.add_parser("catalog", help="내장 무대(Stages) 및 시나리오(Scenarios) 목록 보기")
    p_cat.set_defaults(func=_cmd_catalog)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
