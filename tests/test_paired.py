import copy
import json
from pathlib import Path

import pytest

from human30.paired import AXES, build_run, digest
from scripts.build_public_pairs import write_examples


SCENARIO = {
    "stimulus": "A shared shelter has one free place. A stranger asks you to give it up.",
    "allowed_judgment_ids": ["keep", "yield"],
    "allowed_action_ids": ["stay", "give_place"],
    "allowed_claim_ids": ["need_rest", "stranger_needs_help"],
    "forbidden_choices": {"judgment_ids": [], "action_ids": [], "claim_ids": []},
    "incompatible_claim_pairs": [],
}
OUTPUT = {
    "judgment_id": "keep", "emotion": {"valence": 0, "arousal": 1},
    "action_id": "stay", "claim_ids": ["need_rest"], "utterance": "I need this place.",
}


def make_run(axis="body"):
    first = dict.fromkeys(AXES, "baseline")
    second = {**first, axis: "changed"}
    return build_run(
        axis=axis, scenario=SCENARIO, conditions=[first, second],
        outputs=[OUTPUT, copy.deepcopy(OUTPUT)], prompt_version="public-v1",
        model={"id": "human30.manual-synthetic", "version": "1", "source": "curated_example"},
        seed=42, settings={"temperature": 0}, environment={"python": "3.11"},
        retries=[0, 0],
    )


@pytest.mark.parametrize("axis", AXES)
def test_each_axis_has_one_changed_condition_and_hashed_outputs(axis):
    pair, manifest = make_run(axis)
    assert [key for key in AXES if manifest["condition_vectors"][0][key]
            != manifest["condition_vectors"][1][key]] == [axis]
    assert manifest["scenario_sha256"] == digest(pair["scenario"])
    assert manifest["output_sha256"] == [digest(output) for output in pair["outputs"]]
    assert manifest["model"]["version"] == "1"
    assert manifest["retries"] == [0, 0]


def test_rejects_second_axis_change():
    first = dict.fromkeys(AXES, "baseline")
    second = {**first, "body": "changed", "memory": "changed"}
    with pytest.raises(ValueError, match="only body"):
        build_run(
            axis="body", scenario=SCENARIO, conditions=[first, second],
            outputs=[OUTPUT, OUTPUT], prompt_version="public-v1",
            model={"id": "x", "version": "1", "source": "test"}, seed=42,
            settings={}, environment={}, retries=[0, 0],
        )


def test_run_snapshots_inputs_before_hashing():
    scenario = copy.deepcopy(SCENARIO)
    first = dict.fromkeys(AXES, "baseline")
    conditions = [first, {**first, "body": "changed"}]
    outputs = [copy.deepcopy(OUTPUT), copy.deepcopy(OUTPUT)]
    model = {"id": "example", "version": "1", "source": "test"}
    settings = {"temperature": 0}
    environment = {"python": "3.11"}
    retries = [0, 0]
    pair, manifest = build_run(
        axis="body", scenario=scenario, conditions=conditions, outputs=outputs,
        prompt_version="public-v1", model=model, seed=42, settings=settings,
        environment=environment, retries=retries,
    )
    scenario["stimulus"] = "changed"
    conditions[1]["body"] = "baseline"
    outputs[0]["utterance"] = "changed"
    model["version"] = "2"
    settings["temperature"] = 1
    environment["python"] = "3.12"
    retries[0] = 1
    assert pair["scenario"]["stimulus"] == SCENARIO["stimulus"]
    assert manifest["condition_vectors"][1]["body"] == "changed"
    assert manifest["model"]["version"] == "1"
    assert manifest["settings"] == {"temperature": 0}
    assert manifest["environment"] == {"python": "3.11"}
    assert manifest["retries"] == [0, 0]
    assert manifest["scenario_sha256"] == digest(pair["scenario"])
    assert manifest["output_sha256"] == [digest(item) for item in pair["outputs"]]


def test_public_examples_round_trip(tmp_path):
    write_examples(tmp_path)
    for axis in AXES:
        pair = json.loads((tmp_path / f"{axis}.pair.json").read_text(encoding="utf-8"))
        manifest = json.loads((tmp_path / f"{axis}.manifest.json").read_text(encoding="utf-8"))
        assert manifest["axis"] == axis
        assert manifest["scenario_sha256"] == digest(pair["scenario"])
        assert manifest["output_sha256"] == [digest(output) for output in pair["outputs"]]
        assert manifest["model"]["source"] == "hand_authored_synthetic"


def test_public_examples_on_disk_match_generator(tmp_path):
    write_examples(tmp_path)
    committed = Path(__file__).resolve().parents[1] / "runs" / "public_counterfactual"
    for axis in AXES:
        for suffix in ("pair", "manifest"):
            filename = f"{axis}.{suffix}.json"
            assert json.loads((committed / filename).read_text(encoding="utf-8")) == json.loads(
                (tmp_path / filename).read_text(encoding="utf-8")
            )


def test_public_examples_hold_stimulus_model_seed_and_settings_constant():
    committed = Path(__file__).resolve().parents[1] / "runs" / "public_counterfactual"
    pairs = [json.loads((committed / f"{axis}.pair.json").read_text(encoding="utf-8")) for axis in AXES]
    manifests = [json.loads((committed / f"{axis}.manifest.json").read_text(encoding="utf-8")) for axis in AXES]
    assert len({digest(pair["scenario"]) for pair in pairs}) == 1
    for field in ("prompt_version", "model", "seed", "settings", "environment"):
        assert len({digest(manifest[field]) for manifest in manifests}) == 1
    for axis, manifest in zip(AXES, manifests):
        assert manifest["condition_vectors"][0] == manifests[0]["condition_vectors"][0]
        assert [key for key in AXES if manifest["condition_vectors"][0][key]
                != manifest["condition_vectors"][1][key]] == [axis]
