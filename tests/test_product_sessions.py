"""Synthetic upload session isolation without provider calls or an HTTP listener."""
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID


def test_same_second_uploads_keep_distinct_sessions(monkeypatch):
    spec = importlib.util.spec_from_file_location("human30_test_server", Path(__file__).parents[1] / "product/server.py")
    server = importlib.util.module_from_spec(spec)
    # server's local imports must not persistently change import search order.
    import sys
    monkeypatch.setattr(sys, "path", list(sys.path))
    spec.loader.exec_module(server)
    class FixedClock:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 1, 10, 0, 0)
    monkeypatch.setattr(server, "datetime", FixedClock)
    def upload(name):
        handler = object.__new__(server.Handler)
        handler.headers = {"Content-Type": "application/json"}
        csv = f"date,user,message\n2026.1.1 10:00,{name},synthetic hello\n2026.1.1 10:01,partner,synthetic reply\n"
        handler.read_body = lambda: json.dumps({"csv_content": csv, "me": name}).encode()
        replies = []
        handler.json_response = lambda data, **kwargs: replies.append(data)
        handler.handle_upload()
        return replies[0]["session_id"]
    first = upload("first synthetic user")
    original = server.sessions[first]
    second = upload("second synthetic user")
    assert first != second
    assert UUID(first).version == UUID(second).version == 4
    assert server.sessions[first] is original
    assert server.sessions[first]["stats"]["meta"]["me"] == "first synthetic user"
    assert server.sessions[second]["stats"]["meta"]["me"] == "second synthetic user"
    assert set(server.sessions_created) == {first, second}
    assert server.sessions_created[first] == server.sessions_created[second]
