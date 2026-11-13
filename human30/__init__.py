"""Human30 — Empirical 4-Layer Human Cohort Generator & Dual-Surface Multi-Agent Behavioral Simulator."""

from human30.cards import cohort_analytics, compute_rankings, make_card, one_liner, render_card
from human30.catalog import get_scenario, get_stage, list_scenarios, list_stages
from human30.counterfactual import run_counterfactual
from human30.evaluate import InvalidPair, evaluate
from human30.generator import generate_cohort, list_seeds, load_cohort, load_personas, load_tables, save_cohort
from human30.paired import AXES, build_run, digest
from human30.prompt_compiler import compile_prompt
from human30.simulator import interrogate_character, run_multi_simulation, simulate_scene

__version__ = "2.0.0"

__all__ = [
    "AXES",
    "InvalidPair",
    "__version__",
    "build_run",
    "cohort_analytics",
    "compile_prompt",
    "compute_rankings",
    "digest",
    "evaluate",
    "generate_cohort",
    "get_scenario",
    "get_stage",
    "interrogate_character",
    "list_scenarios",
    "list_seeds",
    "list_stages",
    "load_cohort",
    "load_personas",
    "load_tables",
    "make_card",
    "one_liner",
    "render_card",
    "run_counterfactual",
    "run_multi_simulation",
    "save_cohort",
    "simulate_scene",
]
