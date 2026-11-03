"""Explicit synthetic demo is network-disabled and rejects personal uploads."""
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

ROOT = Path(__file__).parents[1]

def load(monkeypatch):
    spec = importlib.util.spec_from_file_location('human30_demo_test', ROOT / 'product/server.py')
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec.loader.exec_module(module)
    return module

def handler(server):
    h = object.__new__(server.Handler)
    h.headers = {'Content-Type': 'application/json'}
    replies = []
    h.json_response = lambda data, **kwargs: replies.append((data, kwargs))
    def invoke(name, data):
        h.read_body = lambda: json.dumps(data).encode()
        getattr(h, name)()
        return replies[-1]
    return invoke

def test_demo_full_cycle_no_network_even_with_key(monkeypatch):
    s = load(monkeypatch)
    s.DEMO_MODE = True
    s.API_KEY = 'synthetic-unused-key'
    invoke = handler(s)
    csv = (ROOT / 'product/demo.csv').read_text()
    with patch.object(s.urllib.request, 'urlopen', side_effect=AssertionError('demo must not contact provider')):
        upload, _ = invoke('handle_upload', {'csv_content': csv})
        sid = upload['session_id']
        found, _ = invoke('handle_discover', {'session_id': sid})
        assert len(found['discoveries']) == 1
        assert '[합성 데모]' in found['discoveries'][0]['title']
        rebuttal, _ = invoke('handle_rebut', {'session_id': sid, 'index': 0, 'action': 'rebut', 'text': 'test'})
        assert '합성 데모' in rebuttal['followup']
        deeper, _ = invoke('handle_deeper', {'session_id': sid})
        assert '합성 데모' in deeper['question']
        invoke('handle_deeper', {'session_id': sid, 'answer': 'synthetic answer'})
        saved, _ = invoke('handle_save', {'session_id': sid})
        assert saved['session_data']['demo'] is True
        assert saved['session_data']['deeper_answer'] == 'synthetic answer'

def test_demo_rejects_nonfixture_upload_before_parsing(monkeypatch):
    s = load(monkeypatch)
    s.DEMO_MODE = True
    invoke = handler(s)
    reply, status = invoke('handle_upload', {'csv_content': 'date,user,message\n2026.1.1 10:00,private,not allowed\n'})
    assert status['status'] == 400
    assert '합성 CSV' in reply['error']
    assert not s.sessions

def test_normal_mode_still_calls_provider(monkeypatch):
    s = load(monkeypatch)
    s.API_KEY = 'synthetic-unused-key'
    assert s.DEMO_MODE is False
    with patch.object(s.urllib.request, 'urlopen', side_effect=RuntimeError('expected real route')):
        with pytest.raises(RuntimeError, match='expected real route'):
            s.call_claude(s.SYSTEM_PROMPT, 'synthetic prompt')


def test_demo_http_status_fixture_and_normal_defaults(monkeypatch):
    from http.server import HTTPServer
    import threading
    import urllib.request
    from urllib.error import HTTPError
    s = load(monkeypatch)
    server = HTTPServer(('127.0.0.1', 0), s.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        status = json.loads(urllib.request.urlopen(base + '/api/status').read())
        assert status['demo'] is False
        with pytest.raises(HTTPError) as error:
            urllib.request.urlopen(base + '/demo.csv')
        assert error.value.code == 404
        s.DEMO_MODE = True
        status = json.loads(urllib.request.urlopen(base + '/api/status').read())
        assert status['demo'] is True and status['has_api_key'] is False
        assert urllib.request.urlopen(base + '/demo.csv').read() == (ROOT / 'product/demo.csv').read_bytes()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
