# Human30 Quickstart Guide (Run in 60 Seconds)

`Human30` runs out of the box with **Python 3.11+ standard library only**—zero third-party runtime dependencies and no API keys required.

---

## 1. Launch the Interactive Web Studio (Recommended)

```bash
python3 -m human30 studio --port 8000
```

Open **http://127.0.0.1:8000** in your browser to:
- **01. Cohort & Dossiers**: Browse 30 procedurally sampled humans across 4 layers & 28 empirical tables, filter by stress reflex/attachment/ACE/IQ, or generate new cohorts.
- **02. Stage Simulator & 4-Lens Inspector**: Run multi-agent scenarios (Anonymous Vote, Public Roll-Call Vote, Unanimous Scapegoat Dilemma, Resource Rationing, Whistleblower Test, Partner Vote), inspect **Surface / X-Ray / Phone / Subconscious** lenses, and **interrogate any character 1-on-1**.
- **03. Counterfactual Lab**: Mutate a single axis (`body`, `memory`, `identity`, `world_model`) on any character and verify behavioral shifts with SHA-256 provenance receipts.
- **04. Prompt Bundle Compiler**: Export token-optimized prompt bundles for Claude, ChatGPT, Gemini, or local LLMs.

---

## 2. Command-Line Interface (CLI)

```bash
# Generate a new 30-person cohort (Seed 7)
python3 -m human30 generate 7

# Summarize cohort & detect statistical outliers
python3 -m human30 summary 1

# View clinical chart card for character #9
python3 -m human30 card 1 9

# Run a multi-agent scenario simulation in terminal
python3 -m human30 simulate --seed 1 --stage S01 --scenario SC01 --char 9

# Run 5 Monte Carlo repetitions to inspect target convergence
python3 -m human30 simulate --seed 1 --stage S01 --scenario SC01 --runs 5

# Interrogate character #9 (compare spoken excuse vs X-Ray truth)
python3 -m human30 interrogate 1 9 "Why did you vote for #21?"

# Run a single-axis counterfactual experiment
python3 -m human30 counterfactual --seed 1 --char 9 --axis memory
```
