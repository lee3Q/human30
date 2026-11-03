"""Code-backed notice facts, using synthetic data and no network/model calls."""
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime


def test_web_provider_payload_and_session_lifecycle(monkeypatch):
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location('human30_notice_server', root / 'product/server.py')
    server = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec.loader.exec_module(server)
    calls = []
    discovery = {'title': 'synthetic discovery', 'data': 'count 2', 'meaning': 'synthetic meaning', 'surprise': 'synthetic surprise'}
    def model(system, prompt):
        calls.append(prompt)
        return json.dumps([discovery]) if len(calls) == 1 else 'synthetic followup'
    monkeypatch.setattr(server, 'call_claude', model)
    handler = object.__new__(server.Handler)
    handler.headers = {'Content-Type': 'application/json'}
    replies = []
    handler.json_response = lambda data, **kwargs: replies.append(data)
    def invoke(method, data):
        handler.read_body = lambda: json.dumps(data).encode()
        getattr(handler, method)()
        return replies[-1]
    csv = 'date,user,message\n2026.1.1 10:00,synthetic me,UNIQUE_RAW_SENTENCE\n2026.1.1 10:01,synthetic partner,synthetic reply\n'
    sid = invoke('handle_upload', {'csv_content': csv, 'me': 'synthetic me'})['session_id']
    invoke('handle_discover', {'session_id': sid})
    assert 'synthetic me' in calls[0] and 'synthetic partner' in calls[0]
    assert 'UNIQUE_RAW_SENTENCE' not in calls[0]
    invoke('handle_rebut', {'session_id': sid, 'index': 0, 'action': 'rebut', 'text': 'UNIQUE_REBUTTAL'})
    assert 'UNIQUE_REBUTTAL' in calls[1]
    invoke('handle_deeper', {'session_id': sid})
    assert 'UNIQUE_REBUTTAL' in calls[2]
    invoke('handle_deeper', {'session_id': sid, 'answer': 'UNIQUE_FINAL_ANSWER'})
    assert len(calls) == 3
    saved = invoke('handle_save', {'session_id': sid})
    assert saved['session_data']['deeper_answer'] == 'UNIQUE_FINAL_ANSWER'
    assert sid in server.sessions and sid in server.sessions_created
    server.sessions_created[sid] = datetime.now().timestamp() - server.SESSION_TTL_SECONDS - 10
    invoke('handle_save', {'session_id': sid})
    assert sid in server.sessions  # save does not invoke expiration cleanup
    invoke('handle_upload', {'csv_content': csv})
    assert sid not in server.sessions and sid not in server.sessions_created


def test_ui_notice_describes_current_boundaries_without_false_guarantees():
    html = (Path(__file__).parents[1] / 'product/index.html').read_text()
    assert '세션 종료 시 모든 데이터가 메모리에서 삭제됩니다.' not in html
    assert 'AI에게는 통계(숫자)만 전송됩니다.' not in html
    assert '카톡 원문은 이 기기에서만 처리됩니다.' not in html
    for phrase in ['참가자 이름과 통계', '반박을 적으면', '다음 CSV 업로드 시', '서버 메모리에 남아 있습니다', 'AI 제공자의 보관·삭제 정책']:
        assert phrase in html
