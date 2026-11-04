"""Parser-level signals must not confuse multiline messages with dropped rows."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'product'))
import analyze

def test_valid_multiline_has_no_false_dropped_message():
    text='date,user,message\n2026-01-01 10:00:00,"가상 나","첫 줄\n둘째 줄"\n2026-01-01 10:02:00,"가상 친구","답변"\n'
    messages,quality=analyze.parse_text_with_diagnostics(text)
    assert messages==analyze.parse_text(text)
    assert quality=={'format':'A','parsed_messages':2,'rejected_records':0,'unrecognized_lines':0,'continuation_lines':0}

def test_b_invalid_date_is_visible_without_changing_prior_parsing():
    text='date,user,message\n2026.1.1 10:00,가상 나,첫 문장\n2026.13.1 10:01,가상 친구,잘못된 날짜\n2026.1.1 10:02,가상 친구,답변\n'
    messages,quality=analyze.parse_text_with_diagnostics(text)
    assert messages==analyze.parse_text(text)
    assert len(messages)==2
    assert quality['rejected_records']==1
    assert quality['unrecognized_lines']==0

def test_b_continuations_are_not_claimed_validated_or_dropped():
    text='date,user,message\n2026.1.1 10:00,가상 나,첫 문장\n알 수 없는 줄\n2026.1.1 10:02,가상 친구,답변\n'
    messages,quality=analyze.parse_text_with_diagnostics(text)
    assert messages==analyze.parse_text(text)
    assert quality['continuation_lines']==1
    assert quality['rejected_records']==0

def test_a_unrecognized_line_is_visible():
    text='date,user,message\n알 수 없는 줄\n2026-01-01 10:00:00,"가상 나","안녕"\n'
    messages,quality=analyze.parse_text_with_diagnostics(text)
    assert messages==analyze.parse_text(text)
    assert quality['unrecognized_lines']==1

def test_upload_exposes_aggregate_only_without_provider(monkeypatch):
    import json
    from unittest.mock import patch
    spec=importlib.util.spec_from_file_location('diagnostics_server',ROOT/'product/server.py')
    s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
    h=object.__new__(s.Handler);h.headers={'Content-Type':'application/json'}
    csv='date,user,message\n2026.1.1 10:00,A,hello\n2026.13.1 10:01,B,REJECTED_PRIVATE_MESSAGE\n2026.1.1 10:02,B,answer\n'
    h.read_body=lambda:json.dumps({'csv_content':csv}).encode();replies=[]
    h.json_response=lambda data,**kw:replies.append((data,kw))
    with patch.object(s,'call_claude',side_effect=AssertionError('no provider')):
        h.handle_upload()
    data=replies[-1][0]
    assert data['parse_quality']['rejected_records']==1
    assert data['meta']['total_messages']==2
    assert 'REJECTED_PRIVATE_MESSAGE' not in json.dumps(data)
    assert 'parse_quality' not in s.sessions[data['session_id']]
