"""Malformed JSON envelopes are client errors, with no session/provider effects."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

@pytest.mark.parametrize('route', ['upload', 'discover', 'rebut', 'deeper', 'save'])
@pytest.mark.parametrize('body', [b'', b'{', b'\xff', b'[]', b'null', b'"synthetic"', b'1'])
def test_bad_json_envelope_is_400_without_side_effects(route, body, monkeypatch):
    spec = importlib.util.spec_from_file_location('json_body_server', Path(__file__).parents[1] / 'product/server.py')
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec.loader.exec_module(server)
    monkeypatch.setattr(server, 'call_claude', lambda *a: pytest.fail('provider must not be called'))
    handler = object.__new__(server.Handler)
    handler.path = '/api/' + route
    handler.headers = {'Content-Type': 'application/json'}
    handler.read_body = lambda: body
    replies = []
    handler.json_response = lambda data, status=200: replies.append((data, status))
    handler.do_POST()
    assert len(replies) == 1
    assert replies[0][1] == 400
    assert 'error' in replies[0][0]
    assert not server.sessions and not server.sessions_created

def test_unexpected_internal_failure_stays_500(monkeypatch):
    spec = importlib.util.spec_from_file_location('json_body_failure', Path(__file__).parents[1] / 'product/server.py')
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec.loader.exec_module(server)
    handler = object.__new__(server.Handler)
    handler.path = '/api/save'
    handler.handle_save = lambda: (_ for _ in ()).throw(RuntimeError('synthetic private detail'))
    replies = []
    handler.json_response = lambda data, status=200: replies.append((data, status))
    handler.do_POST()
    assert replies == [({'error': '처리 중 오류가 발생했습니다.'}, 500)]
