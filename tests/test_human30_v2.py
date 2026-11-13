"""Comprehensive tests for Human30 v2.0 SDK, Simulator, Counterfactuals, Studio API, and CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human30 import (
    cohort_analytics,
    compile_prompt,
    generate_cohort,
    get_scenario,
    get_stage,
    interrogate_character,
    list_scenarios,
    list_seeds,
    list_stages,
    load_cohort,
    render_card,
    run_counterfactual,
    run_multi_simulation,
    simulate_scene,
)
from human30.cli import main as cli_main
from human30.studio import WEB_DIR, dispatch_api


def test_generator_and_bit_reproducibility():
    c1 = generate_cohort(1)
    c1_repeat = generate_cohort(1)
    assert c1["characters"] == c1_repeat["characters"]
    assert len(c1["characters"]) == 30

    diverse = generate_cohort(17, count=12, age_mode="diverse")
    assert len(diverse["characters"]) == 12
    ages = [c["age"] for c in diverse["characters"]]
    assert min(ages) >= 17 and max(ages) <= 35


def test_cards_and_cohort_analytics():
    cohort = load_cohort(1)
    stats = cohort_analytics(cohort)
    assert stats["count"] == 30
    assert stats["sex_ratio"] == {"M": 15, "F": 15}
    assert len(stats["characters"]) == 30
    assert len(stats["highlights"]) > 0

    card_9 = render_card(cohort, 9)
    assert "#09" in card_9
    assert "■ 신체" in card_9
    assert "■ 트라우마·기억" in card_9
    assert "■ 스토리" in card_9


@pytest.mark.parametrize("scenario_id", ["SC01", "SC02", "SC03", "SC04", "SC05", "SC06"])
def test_simulate_scene_all_scenarios(scenario_id: str):
    scene = simulate_scene(1, stage_id="S01", scenario_id=scenario_id, sim_seed=42)
    assert scene["seed"] == 1
    assert scene["scenario"]["id"] == scenario_id
    assert len(scene["participants"]) == 30
    assert len(scene["vote_tally"]) > 0
    total_votes = sum(vt["votes"] for vt in scene["vote_tally"])
    assert total_votes == 30

    p0 = scene["participants"][0]
    for lens in ("surface", "xray", "phone", "subconscious"):
        assert lens in p0["lenses"]
        assert len(p0["lenses"][lens]) > 20


def test_multi_simulation_and_interrogation():
    multi = run_multi_simulation(1, stage_id="S02", scenario_id="SC01", runs=3)
    assert multi["runs"] == 3
    assert len(multi["invariant_targets"]) > 0
    assert len(multi["character_stability"]) == 30

    reply = interrogate_character(1, 9, "왜 21번에게 투표했나요?", stage_id="S01", scenario_id="SC06")
    assert reply["char_id"] == 9
    assert 0 <= reply["sincerity_score"] <= 100
    assert reply["public_reply"]
    assert reply["xray_thought"]
    assert reply["subconscious_leak"]


@pytest.mark.parametrize("axis", ["body", "memory", "identity", "world_model"])
def test_single_axis_counterfactual_all_axes(axis: str):
    cf = run_counterfactual(1, char_id=9, axis=axis, stage_id="S01", scenario_id="SC01")
    assert cf["axis"] == axis
    assert cf["char_id"] == 9
    assert "judgment_changed" in cf["evaluation"]
    assert "emotion_delta" in cf["evaluation"]
    assert len(cf["manifest"]["output_sha256"]) == 2
    # Verify only the selected axis condition string changed
    for k in ("body", "memory", "identity", "world_model"):
        if k == axis:
            assert cf["conditions"]["arm_0"][k] != cf["conditions"]["arm_1"][k]
        else:
            assert cf["conditions"]["arm_0"][k] == cf["conditions"]["arm_1"][k]


def test_prompt_compiler():
    bundle = compile_prompt(1, stage_id="S03", scenario_id="SC02", char_ids=[1, 4, 9, 21])
    assert bundle["character_count"] == 4
    assert "### #09" in bundle["prompt"]
    assert "S03" in bundle["prompt"]
    assert "SC02" in bundle["prompt"]


def test_studio_api_endpoints():
    assert (WEB_DIR / "index.html").is_file()

    status, meta = dispatch_api("GET", "/api/meta")
    assert status == 200
    assert len(meta["stages"]) == 5
    assert len(meta["scenarios"]) == 6

    status, cohort_res = dispatch_api("GET", "/api/cohorts/1")
    assert status == 200
    assert cohort_res["count"] == 30

    status, char_res = dispatch_api("GET", "/api/cohorts/1/character/9")
    assert status == 200
    assert char_res["id"] == 9
    assert "#09" in char_res["card_text"]

    status, sim_res = dispatch_api("POST", "/api/simulate", {"seed": 1, "stage_id": "S01", "scenario_id": "SC01", "runs": 1})
    assert status == 200
    assert sim_res["mode"] == "single"
    assert len(sim_res["scene"]["participants"]) == 30

    status, int_res = dispatch_api("POST", "/api/interrogate", {"seed": 1, "char_id": 9, "question": "이유가 뭔가요?"})
    assert status == 200
    assert int_res["char_id"] == 9

    status, cf_res = dispatch_api("POST", "/api/counterfactual", {"seed": 1, "char_id": 9, "axis": "memory"})
    assert status == 200
    assert cf_res["axis"] == "memory"

    status, pr_res = dispatch_api("POST", "/api/prompt", {"seed": 1, "stage_id": "S01", "scenario_id": "SC01", "char_ids": [1, 9]})
    assert status == 200
    assert pr_res["character_count"] == 2


def test_cli_commands(capsys):
    assert cli_main(["catalog"]) == 0
    out = capsys.readouterr().out
    assert "S01" in out and "SC01" in out

    assert cli_main(["summary", "1"]) == 0
    out = capsys.readouterr().out
    assert "Seed 1" in out

    assert cli_main(["verify", "1"]) == 0
    out = capsys.readouterr().out
    assert "무결성 검증" in out

    assert cli_main(["simulate", "--seed", "1", "--stage", "S01", "--scenario", "SC01", "--char", "9"]) == 0
    out = capsys.readouterr().out
    assert "HUMAN 30 시뮬레이션 리포트" in out

    assert cli_main(["interrogate", "1", "9", "왜 그랬어?"]) == 0
    out = capsys.readouterr().out
    assert "1:1 심문 결과" in out

    assert cli_main(["counterfactual", "--seed", "1", "--char", "9", "--axis", "body"]) == 0
    out = capsys.readouterr().out
    assert "반사실적 단일축 실험" in out


def test_studio_http_server_live():
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    from human30.studio import StudioRequestHandler

    server = ThreadingHTTPServer(("127.0.0.1", 0), StudioRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
            html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "HUMAN 30" in html

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/meta", timeout=5) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200
            assert meta["name"] == "Human30 Studio"

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/simulate",
            data=json.dumps({"seed": 1, "stage_id": "S02", "scenario_id": "SC02", "runs": 1}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            sim = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200
            assert sim["scene"]["stage"]["id"] == "S02"
            assert sim["scene"]["scenario"]["id"] == "SC02"
    finally:
        server.shutdown()
        server.server_close()
