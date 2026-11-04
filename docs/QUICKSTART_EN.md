# 30p (human30) Quick Start (English)

**30p (인간30 / human30)** — up and running in about a minute.

30p is a Korean-language thought-experiment tool: 30 de-socialized human
characters on one stage, observed in real time. The seed generation and card
tools below run in any language environment, but all generated character
content and the simulation prompts are in Korean. You do not need to read
Korean to generate or inspect the data, but you do need it (or a translator)
to read the cards and run the simulation.

---

## Step 1: View character cards (10 seconds)

```bash
git clone https://github.com/lee3Q/human30.git
cd human30
python3 scripts/card.py 1 all       # all 30 cards
python3 scripts/card.py 1 5         # only character #5
```

The repository already includes seed 1 (`runs/seed_001.json`), so this works
immediately after cloning. Terminal cards are in Korean. A browser view with
filters is available: open `scripts/card_renderer.html` and load
`runs/seed_001.json`.

## Step 2: Generate your own seed (30 seconds)

Pick a new number and generate:

```bash
python3 scripts/generate_seed.py 7
```

Output: `runs/seed_007.json` (30 characters) - check it with
`python3 scripts/card.py 7 all`. (The repository already includes seeds 1, 2, 3, 42, and 999.)

Running an already-existing number is refused to protect the existing file
(exit code 2); for example `python3 scripts/generate_seed.py 1` will not touch
the included seed 1. To overwrite intentionally:

```bash
python3 scripts/generate_seed.py 1 --force
```

A different seed number produces a different sample. The same number, code,
tables, and Python environment produce the same characters and generation
metadata, except `generated_at`, which is the actual generation time — so two
files generated at different times are not byte-identical.

## Step 3: Try the manual LLM simulation

The local tools above prepare characters; they do not run a simulation or connect to an LLM. This manual path is not tested by CI. Check the selected service's current input instructions, data handling and possible costs. Use fictional character data only, never real people's private information or API keys.

1. Read `docs/PORTABLE_PROMPT.md`, then provide it in a new conversation or a prompt field the selected service supports. Not every service exposes the same system-prompt controls. You do not need to change existing conversations or account-wide instructions.
2. Provide character data: open `runs/seed_001.json` and paste the section
   for the character you want to observe, or paste `card.py` output.
3. Call play in natural language (Korean commands shown; the prompt is
   Korean-first):
   ```
   play 시드 1 캐릭터 5 "5분 @ 강당, 처형 투표 결과 발표 직후"
   ```
4. Observation commands:
   ```
   x-ray #5        -> inner thoughts
   phone #5        -> digital footprint (recent apps, messages)
   subconscious #5 -> what the character does not know about themselves
   ```
   (`x-ray #N`, `phone #N`, `subconscious #N` are the canonical forms;
   `sub N` and Korean forms like `5번 무의식` are aliases.)

Output quality, compatibility and content-policy behavior depend on the LLM and account you choose; the project does not guarantee them.

---

## Minimal path

```
view included cards -> (optional) generate your own seed -> paste PORTABLE_PROMPT into an LLM -> play -> observe
```

## Helper scripts

| Command | Purpose |
|------|------|
| `python3 scripts/summarize_seed.py 1` | One-line summary of all 30 |
| `python3 scripts/inspect_char.py 1 5` | Character #5 field detail |
| `python3 scripts/verify_seed.py 1` | Distribution check |

## Requirements

- Python 3 (standard library only; no external packages for the steps above)
- The 4 JSON tables in `tables/` (body, memory, identity, korea) — included
- LLM access (Claude, GPT, Gemini, ...) for the simulation step only

## Scenario examples

| Scenario | play call |
|----------|---------------|
| Execution vote | `"처형 투표 후 결과 발표, 강당"` |
| A day at a hagwon | `"평범한 수요일 오전, 재수학원 자습실"` |
| Holiday gathering | `"추석 저녁, 친척 12명 모임"` |

---

*Korean original: [`QUICKSTART.md`](QUICKSTART.md). Detailed documents live in
`docs/` (Korean).*
