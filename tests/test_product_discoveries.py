"""Malformed model output cannot overwrite a prior valid discovery session."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest


@pytest.mark.parametrize('payload', ['not json', '[]', '[null]', '[1]', '["text"]', '[{}]', '[{"title":"test"}]'] + [json.dumps([{field: (value if field == 'title' else 'synthetic') for field in ('title', 'data', 'meaning', 'surprise', 'question')}]) for value in (None, [], 1, ' ', '')])
def test_invalid_model_discoveries_preserve_session(payload, monkeypatch):
    spec = importlib.util.spec_from_file_location('human30_discoveries', Path(__file__).parents[1] / 'product/server.py')
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec.loader.exec_module(server)
    session = {'stats': {'meta': {'me': 'synthetic'}}, 'discoveries': [{'title': 'old'}], 'responses': [{'action': 'agree'}]}
    before = json.dumps(session, sort_keys=True)
    server.sessions['synthetic'] = session
    monkeypatch.setattr(server, 'call_claude', lambda *args: payload)
    handler = object.__new__(server.Handler)
    handler.read_body = lambda: b'{"session_id":"synthetic"}'
    replies = []
    handler.json_response = lambda data, **kwargs: replies.append((data, kwargs))
    handler.handle_discover()
    assert replies[0][1]['status'] == 502
    assert 'error' in replies[0][0]
    assert json.dumps(session, sort_keys=True) == before


def test_valid_discoveries_replace_session_and_initialize_responses(monkeypatch):
    spec = importlib.util.spec_from_file_location('human30_valid_discoveries', Path(__file__).parents[1] / 'product/server.py')
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec.loader.exec_module(server)
    session = {'stats': {'meta': {'me': 'synthetic'}}, 'discoveries': [], 'responses': []}
    server.sessions['synthetic'] = session
    discovery = {field: f'synthetic {field}' for field in ('title', 'data', 'meaning', 'surprise')}
    monkeypatch.setattr(server, 'call_claude', lambda *args: json.dumps([discovery]))
    handler = object.__new__(server.Handler)
    handler.read_body = lambda: b'{"session_id":"synthetic"}'
    replies = []
    handler.json_response = lambda data, **kwargs: replies.append((data, kwargs))
    handler.handle_discover()
    assert replies[0][0] == {'discoveries': [discovery], 'count': 1}
    assert session['discoveries'] == [discovery]
    assert session['responses'] == [{'action': 'pending'}]
