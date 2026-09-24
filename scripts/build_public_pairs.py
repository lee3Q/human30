"""Write four transparent, curated public counterfactual examples."""

from __future__ import annotations

import json
from pathlib import Path

from human30.paired import AXES, build_run


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "runs" / "public_counterfactual"
SCENARIO = {
    "id": "shared_shelter_v1",
    "stimulus": "At a public shelter there is one free seat. A stranger asks to use it. Decide what to do now.",
    "allowed_judgment_ids": ["keep_seat", "yield_seat", "seat_is_owned"],
    "allowed_action_ids": ["sit", "offer_seat", "push_stranger"],
    "allowed_claim_ids": ["own_need", "stranger_need", "can_stand", "stranger_has_no_right"],
    "forbidden_choices": {
        "judgment_ids": ["seat_is_owned"],
        "action_ids": ["push_stranger"],
        "claim_ids": ["stranger_has_no_right"],
    },
    "incompatible_claim_pairs": [["own_need", "can_stand"]],
}
BASELINE = {
    "body": "rested", "memory": "no_related_memory",
    "identity": "values_fair_turns", "world_model": "seat_demand_unknown",
}
CHANGED = {
    "body": "leg_pain",
    "memory": "remembers_receiving_help_at_shelter",
    "identity": "values_offering_help",
    "world_model": "next_seat_expected_soon",
}


def output(yield_seat: bool, utterance: str) -> dict:
    return {
        "judgment_id": "yield_seat" if yield_seat else "keep_seat",
        "emotion": {"valence": 1 if yield_seat else 0, "arousal": 1},
        "action_id": "offer_seat" if yield_seat else "sit",
        "claim_ids": ["stranger_need", "can_stand"] if yield_seat else ["own_need"],
        "utterance": utterance,
    }


EXAMPLES = {
    "body": [output(True, "Please take the seat."), output(False, "My leg hurts, so I need to sit.")],
    "memory": [output(False, "I will sit for now."), output(True, "Someone helped me here once. Take it.")],
    "identity": [output(False, "I will use the seat."), output(True, "You can take my place.")],
    "world_model": [output(False, "I will sit here."), output(True, "Another seat should open soon; take this one.")],
}


def write_examples(destination: Path = DESTINATION) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for axis in AXES:
        pair, manifest = build_run(
            axis=axis,
            scenario=SCENARIO,
            conditions=[BASELINE, {**BASELINE, axis: CHANGED[axis]}],
            outputs=EXAMPLES[axis],
            prompt_version="public-synthetic-v1",
            model={
                "id": "human30.curated-example",
                "version": "1",
                "source": "hand_authored_synthetic",
            },
            seed=42,
            settings={"generation": "curated", "temperature": None},
            environment={"generation_context": "hand_authored_fixture_v1"},
            retries=[0, 0],
        )
        for suffix, value in (("pair", pair), ("manifest", manifest)):
            path = destination / f"{axis}.{suffix}.json"
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_examples()
