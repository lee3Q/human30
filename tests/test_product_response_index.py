"""Invalid discovery indexes must not select a different response or call a model."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest


@pytest.mark.parametrize("index", [-1, -2, 2, True, 0.0, "0", None])
def test_invalid_response_index_leaves_session_unchanged(index, monkeypatch):
    spec = importlib.util.spec_from_file_location("human30_index_server", Path(__file__).parents[1] / "product/server.py")
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, "path", list(sys.path))
    spec.loader.exec_module(server)
    session = {"discoveries": [{"title": "one"}, {"title": "two"}],
               "responses": [{"action": "pending"}, {"action": "pending"}]}
    server.sessions["synthetic"] = session
    before = json.dumps(session, sort_keys=True)
    def forbidden(*args):
        pytest.fail("invalid index must not call a provider")
    monkeypatch.setattr(server, "call_claude", forbidden)
    handler = object.__new__(server.Handler)
    handler.read_body = lambda: json.dumps({"session_id": "synthetic", "index": index,
        "action": "rebut", "text": "synthetic reason"}).encode()
    replies = []
    handler.json_response = lambda data, **kwargs: replies.append((data, kwargs))
    handler.handle_rebut()
    assert replies[0][1]["status"] == 400
    assert "error" in replies[0][0]
    assert json.dumps(session, sort_keys=True) == before


def test_valid_zero_index_still_updates_first_response(monkeypatch):
    spec = importlib.util.spec_from_file_location("human30_valid_index", Path(__file__).parents[1] / "product/server.py")
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, "path", list(sys.path))
    spec.loader.exec_module(server)
    server.sessions["synthetic"] = {"discoveries": [{"title": "one"}], "responses": []}
    handler = object.__new__(server.Handler)
    handler.read_body = lambda: b'{"session_id":"synthetic","index":0,"action":"agree"}'
    handler.json_response = lambda *args, **kwargs: None
    handler.handle_rebut()
    assert server.sessions["synthetic"]["responses"] == [{"action": "agree", "text": ""}]
