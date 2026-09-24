import copy
import json
import subprocess
import sys

import pytest


def pair():
    return {
        "scenario": {
            "allowed_judgment_ids": ["wait", "act"],
            "allowed_action_ids": ["stay", "leave"],
            "allowed_claim_ids": ["safe", "unsafe", "urgent"],
            "forbidden_choices": {
                "judgment_ids": ["act"],
                "action_ids": ["leave"],
                "claim_ids": ["urgent"],
            },
            "incompatible_claim_pairs": [["safe", "unsafe"]],
        },
        "outputs": [
            {
                "judgment_id": "wait",
                "emotion": {"valence": 0, "arousal": 1},
                "action_id": "stay",
                "claim_ids": ["safe"],
                "utterance": "I can wait.",
            },
            {
                "judgment_id": "act",
                "emotion": {"valence": -2, "arousal": 2},
                "action_id": "leave",
                "claim_ids": ["safe", "unsafe", "urgent"],
                "utterance": "I will go.",
            },
        ],
        "generator_self_evaluation": {"judgment_changed": False, "verdict": "safe"},
    }


def cli(tmp_path, value):
    input_path = tmp_path / "pair.json"
    output_path = tmp_path / "receipt.json"
    input_path.write_text(json.dumps(value), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "human30.evaluate", "--pair", str(input_path), "--out", str(output_path)],
        capture_output=True, text=True,
    )
    return result, output_path


def test_cli_reports_changes_violations_and_contradictions(tmp_path):
    result, path = cli(tmp_path, pair())
    assert result.returncode == 0, result.stderr
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["judgment_changed"] is True
    assert receipt["emotion_changed"] is True
    assert receipt["emotion_delta"] == {"valence": -2, "arousal": 1}
    assert receipt["action_changed"] is True
    assert receipt["utterance_expression_changed"] is True
    assert receipt["arms"][0] == {"constraint_violations": [], "self_contradictions": []}
    assert receipt["arms"][1] == {
        "constraint_violations": [
            {"field": "judgment_id", "id": "act"},
            {"field": "action_id", "id": "leave"},
            {"field": "claim_ids", "id": "urgent"},
        ],
        "self_contradictions": [["safe", "unsafe"]],
    }


def test_utterance_difference_is_separate_from_structured_changes(tmp_path):
    value = pair()
    value["outputs"][1] = copy.deepcopy(value["outputs"][0])
    value["outputs"][1]["utterance"] = "Let's wait."
    result, path = cli(tmp_path, value)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["utterance_expression_changed"] is True
    assert receipt["judgment_changed"] is False
    assert receipt["emotion_changed"] is False
    assert receipt["action_changed"] is False


def test_generator_self_evaluation_cannot_change_receipt(tmp_path):
    first = pair()
    second = copy.deepcopy(first)
    second["generator_self_evaluation"] = {
        "judgment_changed": True,
        "verdict": "unsafe",
        "arms": [{"constraint_violations": []}, {"constraint_violations": []}],
    }
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first_result, first_path = cli(first_dir, first)
    second_result, second_path = cli(second_dir, second)
    assert first_result.returncode == 0, first_result.stderr
    assert second_result.returncode == 0, second_result.stderr
    assert json.loads(first_path.read_text(encoding="utf-8")) == json.loads(
        second_path.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("mutation", [
    lambda p: p["outputs"][0].__setitem__("judgment_id", "undefined"),
    lambda p: p["outputs"][0].__setitem__("action_id", "undefined"),
    lambda p: p["outputs"][0].__setitem__("claim_ids", ["undefined"]),
    lambda p: p["outputs"][0].pop("judgment_id"),
    lambda p: p["outputs"][0].pop("emotion"),
    lambda p: p["outputs"][0].pop("action_id"),
    lambda p: p["outputs"][0].pop("claim_ids"),
    lambda p: p["outputs"][0].pop("utterance"),
    lambda p: p["outputs"][0]["emotion"].pop("valence"),
    lambda p: p["outputs"][0]["emotion"].pop("arousal"),
    lambda p: p["outputs"][0]["emotion"].__setitem__("valence", 3),
    lambda p: p["outputs"][0]["emotion"].__setitem__("valence", -3),
    lambda p: p["outputs"][0]["emotion"].__setitem__("arousal", -1),
    lambda p: p["outputs"][0]["emotion"].__setitem__("arousal", 3),
    lambda p: p["outputs"][0]["emotion"].__setitem__("arousal", True),
    lambda p: p["outputs"][0].__setitem__("extra", "no"),
])
def test_invalid_output_fails_without_receipt(tmp_path, mutation):
    value = pair()
    mutation(value)
    result, path = cli(tmp_path, value)
    assert result.returncode != 0
    assert not path.exists()
