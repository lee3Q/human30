"""Invalid/unsupported files are actionable input failures, not server faults."""
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

ROOT=Path(__file__).parents[1]

def load(monkeypatch):
    spec=importlib.util.spec_from_file_location('human30_csv_intake',ROOT/'product/server.py')
    module=importlib.util.module_from_spec(spec)
    monkeypatch.setattr(sys,'path',list(sys.path))
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('csv', ['', 'not a chat export', 'date,user,message\nunsupported,row,here\n', 'date,user,message\n2026-99-99 10:00:00,"A","synthetic"\n', 'date,user,message\n2026.99.99 10:00,A,synthetic\n'])
def test_invalid_csv_gets_400_no_new_session(monkeypatch,csv):
    s=load(monkeypatch)
    h=object.__new__(s.Handler)
    h.headers={'Content-Type':'application/json'}
    h.read_body=lambda:json.dumps({'csv_content':csv}).encode()
    replies=[]
    h.json_response=lambda data,**kw:replies.append((data,kw))
    with patch.object(s,'call_claude',side_effect=AssertionError('no provider')):
        h.handle_upload()
    assert replies[-1][1]['status']==400
    assert 'CSV' in replies[-1][0]['error']
    assert not s.sessions and not s.sessions_created

@pytest.mark.parametrize('line',['2026-01-01 10:00:00,"A","hello, quoted world"','2026.1.1 10:00,A,hello'])
def test_documented_formats_keep_exact_message(monkeypatch,line):
    s=load(monkeypatch)
    messages=s.parse_text('date,user,message\n'+line+'\n')
    assert len(messages)==1
    assert messages[0][1]=='A'
    assert 'hello' in messages[0][2]
