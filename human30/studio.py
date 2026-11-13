"""Zero-Dependency HTTP Server & REST API for the Human30 Interactive Web Studio."""

from __future__ import annotations

import json
import os
import re
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from human30.cards import cohort_analytics, one_liner, render_card
from human30.catalog import list_scenarios, list_stages
from human30.counterfactual import AXIS_DESCRIPTIONS, run_counterfactual
from human30.generator import generate_cohort, list_seeds, load_cohort, save_cohort
from human30.prompt_compiler import compile_prompt
from human30.simulator import interrogate_character, run_multi_simulation, simulate_scene

WEB_DIR = Path(__file__).resolve().parent / "web"


def get_meta() -> dict[str, Any]:
    return {
        "name": "Human30 Studio",
        "version": "2.0.0",
        "seeds": list_seeds(),
        "stages": list_stages(),
        "scenarios": list_scenarios(),
        "axes": list(AXIS_DESCRIPTIONS.values()),
        "providers": [
            {"id": "engine", "label": "Built-in Psych Engine (즉시 실행 · 무료/오프라인)", "available": True},
            {"id": "openai", "label": "OpenAI API (OPENAI_API_KEY)", "available": bool(os.environ.get("OPENAI_API_KEY"))},
            {"id": "anthropic", "label": "Anthropic API (ANTHROPIC_API_KEY)", "available": bool(os.environ.get("ANTHROPIC_API_KEY"))},
            {"id": "openrouter", "label": "OpenRouter API (OPENROUTER_API_KEY)", "available": bool(os.environ.get("OPENROUTER_API_KEY"))},
            {"id": "ollama", "label": "Local Ollama (localhost:11434)", "available": True},
        ],
    }


def dispatch_api(method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    """Pure dispatcher function (testable without opening sockets)."""
    body = body or {}
    try:
        if method == "GET" and path == "/api/meta":
            return 200, get_meta()

        m_cohort = re.match(r"^/api/cohorts/(\d+)$", path)
        if method == "GET" and m_cohort:
            seed = int(m_cohort.group(1))
            cohort = load_cohort(seed, auto_generate=True)
            return 200, cohort_analytics(cohort)

        m_char = re.match(r"^/api/cohorts/(\d+)/character/(\d+)$", path)
        if method == "GET" and m_char:
            seed = int(m_char.group(1))
            cid = int(m_char.group(2))
            cohort = load_cohort(seed, auto_generate=True)
            by_id = {c["id"]: c for c in cohort["characters"]}
            if cid not in by_id:
                return 404, {"error": f"Character #{cid} not found in seed {seed}"}
            char = by_id[cid]
            return 200, {
                "seed": seed,
                "id": cid,
                "one_liner": one_liner(char),
                "card_text": render_card(cohort, cid),
                "character": char,
            }

        if method == "POST" and path == "/api/cohorts/generate":
            seed = int(body.get("seed", 7))
            count = int(body.get("count", 30))
            age_mode = str(body.get("age_mode", "default"))
            cohort = generate_cohort(seed, count=count, age_mode=age_mode)
            save_cohort(cohort, force=True)
            return 200, {
                "cohort": cohort_analytics(cohort),
                "seeds": list_seeds(),
            }

        if method == "POST" and path == "/api/simulate":
            seed = int(body.get("seed", 1))
            stage_id = str(body.get("stage_id", "S01"))
            scenario_id = str(body.get("scenario_id", "SC01"))
            custom_stimulus = body.get("custom_stimulus") or None
            custom_stage_text = body.get("custom_stage_text") or None
            sim_seed = int(body.get("sim_seed", 42))
            tick = int(body.get("tick", 1))
            runs = int(body.get("runs", 1))
            provider = str(body.get("provider", "engine"))
            model = body.get("model") or None
            prior_votes_raw = body.get("prior_votes") or {}
            prior_votes = {int(k): int(v) for k, v in prior_votes_raw.items()} if isinstance(prior_votes_raw, dict) else {}

            cohort = load_cohort(seed, auto_generate=True)
            if runs > 1:
                multi = run_multi_simulation(
                    cohort,
                    stage_id=stage_id,
                    scenario_id=scenario_id,
                    custom_stimulus=custom_stimulus,
                    runs=runs,
                    base_sim_seed=sim_seed,
                )
                return 200, {"mode": "multi", "multi": multi, "scene": multi["first_run"]}
            scene = simulate_scene(
                cohort,
                stage_id=stage_id,
                scenario_id=scenario_id,
                custom_stage_text=custom_stage_text,
                custom_stimulus=custom_stimulus,
                sim_seed=sim_seed,
                tick=tick,
                provider=provider,
                model=model,
                prior_votes=prior_votes,
            )
            return 200, {"mode": "single", "scene": scene}

        if method == "POST" and path == "/api/interrogate":
            seed = int(body.get("seed", 1))
            char_id = int(body.get("char_id", 9))
            question = str(body.get("question", "방금 왜 그렇게 행동했나요?"))
            stage_id = str(body.get("stage_id", "S01"))
            scenario_id = str(body.get("scenario_id", "SC01"))
            provider = str(body.get("provider", "engine"))
            model = body.get("model") or None
            cohort = load_cohort(seed, auto_generate=True)
            res = interrogate_character(
                cohort,
                char_id,
                question,
                stage_id=stage_id,
                scenario_id=scenario_id,
                provider=provider,
                model=model,
            )
            return 200, res

        if method == "POST" and path == "/api/counterfactual":
            seed = int(body.get("seed", 1))
            char_id = int(body.get("char_id", 9))
            axis = str(body.get("axis", "memory"))
            stage_id = str(body.get("stage_id", "S01"))
            scenario_id = str(body.get("scenario_id", "SC01"))
            sim_seed = int(body.get("sim_seed", 42))
            cohort = load_cohort(seed, auto_generate=True)
            res = run_counterfactual(
                cohort,
                char_id=char_id,
                axis=axis,
                stage_id=stage_id,
                scenario_id=scenario_id,
                sim_seed=sim_seed,
            )
            return 200, res

        if method == "POST" and path == "/api/prompt":
            seed = int(body.get("seed", 1))
            stage_id = str(body.get("stage_id", "S01"))
            scenario_id = str(body.get("scenario_id", "SC01"))
            char_ids = body.get("char_ids")
            if isinstance(char_ids, list):
                char_ids = [int(x) for x in char_ids]
            else:
                char_ids = None
            custom_stimulus = body.get("custom_stimulus") or None
            cohort = load_cohort(seed, auto_generate=True)
            res = compile_prompt(
                cohort,
                stage_id=stage_id,
                scenario_id=scenario_id,
                char_ids=char_ids,
                custom_stimulus=custom_stimulus,
            )
            return 200, res

        return 404, {"error": f"Unknown API endpoint: {method} {path}"}
    except KeyError as exc:
        return 404, {"error": str(exc)}
    except ValueError as exc:
        return 400, {"error": str(exc)}
    except Exception as exc:
        return 500, {"error": str(exc)}


class StudioRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            index_file = WEB_DIR / "index.html"
            raw = index_file.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path.startswith("/api/"):
            status, res = dispatch_api("GET", path)
            self._send_json(status, res)
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON request body"})
            return
        status, res = dispatch_api("POST", path, body)
        self._send_json(status, res)


def run_studio(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False) -> None:
    server = ThreadingHTTPServer((host, port), StudioRequestHandler)
    url = f"http://{host}:{port}"
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Human30 Interactive Studio running at: {url}")
    print(f"  Press Ctrl+C to stop.")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Human30 Studio...")
    finally:
        server.server_close()
