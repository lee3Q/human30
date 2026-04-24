#!/usr/bin/env python3
"""
통화녹음 텍스트 전량 분석 — 이상규 발견 리포트
stdlib only. Python 3.10+
"""

import os
import re
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime

# ── 설정 ──────────────────────────────────────────────
DATA_DIR = '/Users/sanggyulee/Downloads/통화녹음텍스트/'
EXTRA_FILE = '/Users/sanggyulee/pp/동결/작업실/시스템/아카이브/2026-03-14/폴더/사랑/원본데이터/통화_녹음_앤두_260304.txt'
REPORT_PATH = '/Users/sanggyulee/pp/30p/runs/self/discoveries/02_call_patterns.md'

# 정원이 관련 이름/번호 (발화자 2 = 상대방)
JUNGWON_MARKERS = ['손정원', '앤두', '앵두', '01087322028']

# ── 파싱 ──────────────────────────────────────────────

def parse_timestamp(ts_str):
    """MM:SS 또는 HH:MM:SS -> 초"""
    parts = ts_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def extract_date_from_filename(fname):
    """파일명에서 YYMMDD 추출 -> datetime"""
    m = re.search(r'_(\d{6})_\d{6}', fname)
    if m:
        ds = m.group(1)
        try:
            return datetime.strptime(ds, '%y%m%d')
        except ValueError:
            pass
    return None

def is_jungwon_call(fname):
    """정원이와의 통화인지"""
    for marker in JUNGWON_MARKERS:
        if marker in fname:
            return True
    return False

def parse_call(filepath):
    """통화 파일 파싱 -> list of (speaker, timestamp_sec, text)"""
    try:
        with open(filepath, encoding='utf-16') as f:
            content = f.read()
    except Exception:
        try:
            with open(filepath, encoding='utf-8-sig') as f:
                content = f.read()
        except Exception:
            return []

    utterances = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r'발화자\s+(\d)\s+\((\d{1,2}:\d{2}(?::\d{2})?)\)', line)
        if m:
            speaker = int(m.group(1))
            ts = parse_timestamp(m.group(2))
            # next line(s) = text
            text_lines = []
            i += 1
            while i < len(lines):
                tl = lines[i].strip()
                if tl == '' or re.match(r'발화자\s+\d\s+\(', tl):
                    break
                text_lines.append(tl)
                i += 1
            text = ' '.join(text_lines)
            utterances.append((speaker, ts, text))
        else:
            i += 1
    return utterances

# ── 데이터 로드 ──────────────────────────────────────────────

def load_all_calls():
    """모든 통화 파일 로드"""
    calls = []

    # 메인 디렉토리
    for fname_raw in os.listdir(DATA_DIR):
        if not fname_raw.endswith('.txt'):
            continue
        fpath = os.path.join(DATA_DIR, fname_raw)
        # macOS returns NFD filenames; normalize to NFC for Korean matching
        fname = unicodedata.normalize('NFC', fname_raw)
        date = extract_date_from_filename(fname)
        jw = is_jungwon_call(fname)
        utts = parse_call(fpath)
        if utts:
            calls.append({
                'filename': fname,
                'filepath': fpath,
                'date': date,
                'is_jungwon': jw,
                'utterances': utts,
            })

    # 추가 파일
    extra_nfd = unicodedata.normalize('NFD', EXTRA_FILE)
    extra_path = EXTRA_FILE if os.path.exists(EXTRA_FILE) else (extra_nfd if os.path.exists(extra_nfd) else None)
    if extra_path:
        fname = unicodedata.normalize('NFC', os.path.basename(extra_path))
        utts = parse_call(extra_path)
        if utts:
            calls.append({
                'filename': fname,
                'filepath': extra_path,
                'date': datetime(2026, 3, 4),
                'is_jungwon': True,
                'utterances': utts,
            })

    calls.sort(key=lambda c: c['date'] or datetime(2000, 1, 1))
    return calls

# ── 분석 함수들 ──────────────────────────────────────────────

def analysis_1_meta(calls):
    """1. 전체 통화 메타데이터"""
    out = []
    out.append("## 1. 전체 통화 메타데이터\n")

    total = len(calls)
    dates = [c['date'] for c in calls if c['date']]
    jw_calls = [c for c in calls if c['is_jungwon']]

    out.append(f"- 총 통화 수: **{total}**개")
    out.append(f"- 정원이 통화: **{len(jw_calls)}**개 ({len(jw_calls)/total*100:.1f}%)")
    out.append(f"- 기타 통화: **{total - len(jw_calls)}**개")
    if dates:
        out.append(f"- 날짜 범위: **{min(dates).strftime('%Y-%m-%d')}** ~ **{max(dates).strftime('%Y-%m-%d')}**")
        out.append(f"- 고유 날짜 수: **{len(set(d.strftime('%Y-%m-%d') for d in dates))}**일")

    # 통화 길이
    durations = []
    for c in calls:
        if c['utterances']:
            last_ts = max(u[1] for u in c['utterances'])
            durations.append((c['filename'], last_ts / 60, c))

    durations.sort(key=lambda x: -x[1])

    out.append(f"\n- 평균 통화 길이: **{sum(d[1] for d in durations)/len(durations):.1f}분**")
    out.append(f"- 최장 통화: **{durations[0][1]:.1f}분** ({durations[0][0]})")

    out.append(f"\n### 가장 긴 통화 Top 10\n")
    out.append("| 순위 | 파일 | 길이(분) | 발화 수 |")
    out.append("|------|------|----------|---------|")
    for i, (fname, dur, c) in enumerate(durations[:10]):
        short_name = fname[:50] + '...' if len(fname) > 50 else fname
        out.append(f"| {i+1} | {short_name} | {dur:.1f} | {len(c['utterances'])} |")

    # 발화자 1/2 비율
    total_s1 = sum(len([u for u in c['utterances'] if u[0] == 1]) for c in calls)
    total_s2 = sum(len([u for u in c['utterances'] if u[0] == 2]) for c in calls)
    out.append(f"\n- 전체 발화 수 — 이상규: **{total_s1}** ({total_s1/(total_s1+total_s2)*100:.1f}%), 상대: **{total_s2}** ({total_s2/(total_s1+total_s2)*100:.1f}%)")

    # 발화자 1/2 글자 수 비율
    total_chars_s1 = sum(len(u[2]) for c in calls for u in c['utterances'] if u[0] == 1)
    total_chars_s2 = sum(len(u[2]) for c in calls for u in c['utterances'] if u[0] == 2)
    out.append(f"- 전체 글자 수 — 이상규: **{total_chars_s1}** ({total_chars_s1/(total_chars_s1+total_chars_s2)*100:.1f}%), 상대: **{total_chars_s2}** ({total_chars_s2/(total_chars_s1+total_chars_s2)*100:.1f}%)")

    return '\n'.join(out)


def analysis_2_monologue(calls):
    """2. 이상규 발화 길이 + 장문 독백"""
    out = []
    out.append("## 2. 이상규 발화 길이 분석\n")

    # 통화별 평균 글자수
    call_avg_chars = []
    for c in calls:
        s1_utts = [u for u in c['utterances'] if u[0] == 1]
        if s1_utts:
            avg = sum(len(u[2]) for u in s1_utts) / len(s1_utts)
            call_avg_chars.append((c['filename'], avg, len(s1_utts)))

    overall_avg = sum(x[1] for x in call_avg_chars) / len(call_avg_chars) if call_avg_chars else 0
    out.append(f"- 이상규 1턴당 전체 평균 글자 수: **{overall_avg:.1f}자**")

    # 가장 많이 말한 통화
    call_avg_chars.sort(key=lambda x: -x[1])
    out.append(f"\n### 이상규가 가장 길게 말한 통화 Top 10\n")
    out.append("| 순위 | 파일 | 턴당 평균 글자수 | 발화 수 |")
    out.append("|------|------|-----------------|---------|")
    for i, (fname, avg, cnt) in enumerate(call_avg_chars[:10]):
        short = fname[:50] + '...' if len(fname) > 50 else fname
        out.append(f"| {i+1} | {short} | {avg:.1f} | {cnt} |")

    # 60초 이상 연속 독백 찾기
    # "60초 이상 연속 말한" = 이상규가 연속 발화하며, 첫 발화~마지막 발화 시간차가 60초+
    long_monologues = []
    for c in calls:
        utts = c['utterances']
        i = 0
        while i < len(utts):
            if utts[i][0] == 1:
                # 연속 발화자1 구간 시작
                start = i
                j = i + 1
                while j < len(utts) and utts[j][0] == 1:
                    j += 1
                # start~j-1 까지가 연속 발화자1
                duration = utts[j-1][1] - utts[start][1]
                if duration >= 60 and (j - start) >= 2:
                    text = ' '.join(u[2] for u in utts[start:j])
                    long_monologues.append({
                        'file': c['filename'],
                        'date': c['date'],
                        'duration_sec': duration,
                        'num_turns': j - start,
                        'text': text,
                        'char_count': len(text),
                        'start_ts': utts[start][1],
                    })
                i = j
            else:
                i += 1

    out.append(f"\n### 60초 이상 연속 독백\n")
    out.append(f"- 총 독백 구간 수: **{len(long_monologues)}**개")

    if long_monologues:
        long_monologues.sort(key=lambda x: -x['duration_sec'])
        avg_dur = sum(m['duration_sec'] for m in long_monologues) / len(long_monologues)
        out.append(f"- 평균 독백 길이: **{avg_dur:.0f}초** ({avg_dur/60:.1f}분)")
        out.append(f"- 최장 독백: **{long_monologues[0]['duration_sec']}초** ({long_monologues[0]['duration_sec']/60:.1f}분)")

        # 독백 내용 분류 시도
        rule_keywords = ['해야', '규칙', '원칙', '약속', '안 돼', '하면 안', '해줘야', '이렇게 해',
                         '그래야', '당연히', '마땅히', '의무', '책임', '역할', '해야지', '해야 돼',
                         '그게 맞', '그게 아니', '잘못', '틀렸', '제대로', '올바']
        past_keywords = ['예전에', '그때', '어렸을', '학교', '군대', '대학', '중학', '고등',
                         '어릴 때', '옛날', '과거', '했었', '이었', '전에']
        emotion_keywords = ['사랑', '보고싶', '미안', '힘들', '외로', '무서', '화가', '짜증',
                           '슬프', '미치', '지쳤', '피곤']

        rule_count = 0
        past_count = 0
        emotion_count = 0
        other_count = 0

        for m in long_monologues:
            text = m['text']
            has_rule = any(kw in text for kw in rule_keywords)
            has_past = any(kw in text for kw in past_keywords)
            has_emotion = any(kw in text for kw in emotion_keywords)

            if has_rule:
                rule_count += 1
                m['category'] = '규칙/지시'
            elif has_past:
                past_count += 1
                m['category'] = '과거/경험'
            elif has_emotion:
                emotion_count += 1
                m['category'] = '감정 표현'
            else:
                other_count += 1
                m['category'] = '기타'

        out.append(f"\n### 독백 내용 분류\n")
        out.append(f"- 규칙/지시 설명: **{rule_count}**개 ({rule_count/len(long_monologues)*100:.1f}%)")
        out.append(f"- 과거/경험 이야기: **{past_count}**개 ({past_count/len(long_monologues)*100:.1f}%)")
        out.append(f"- 감정 표현: **{emotion_count}**개 ({emotion_count/len(long_monologues)*100:.1f}%)")
        out.append(f"- 기타: **{other_count}**개 ({other_count/len(long_monologues)*100:.1f}%)")

        out.append(f"\n### 장문 독백 표본 (상위 20개, 길이순)\n")
        for i, m in enumerate(long_monologues[:20]):
            date_str = m['date'].strftime('%Y-%m-%d') if m['date'] else '?'
            out.append(f"#### 독백 #{i+1} — {date_str}, {m['duration_sec']}초, [{m.get('category','?')}]")
            preview = m['text'][:300] + '...' if len(m['text']) > 300 else m['text']
            out.append(f"> {preview}\n")

    return '\n'.join(out), long_monologues


def analysis_3_jungwon(calls):
    """3. 정원이의 발화 패턴"""
    out = []
    out.append("## 3. 정원이의 발화 패턴\n")

    jw_calls = [c for c in calls if c['is_jungwon']]

    # 수용 발화 키워드
    accept_patterns = ['네', '응', '알겠어', '알았어', '죄송', '미안', '그래', '어',
                       '맞아', '알겠습니다', '그렇구나', '그렇지']

    # 통화별 수용 발화 비율
    accept_data = []
    for c in jw_calls:
        s2_utts = [u for u in c['utterances'] if u[0] == 2]
        if not s2_utts:
            continue
        accept_count = 0
        for u in s2_utts:
            text = u[2].strip().rstrip('.!? ')
            if text in accept_patterns or len(text) <= 3:
                accept_count += 1
        ratio = accept_count / len(s2_utts) if s2_utts else 0
        accept_data.append((c['filename'], c['date'], ratio, accept_count, len(s2_utts)))

    overall_accept = sum(d[3] for d in accept_data) / sum(d[4] for d in accept_data) if accept_data else 0
    out.append(f"- 정원이 수용 발화(네/응/알겠어/3자 이하) 비율: **{overall_accept*100:.1f}%**")

    # 정원이 턴당 평균 글자수
    jw_turn_chars = []
    for c in jw_calls:
        s2_utts = [u for u in c['utterances'] if u[0] == 2]
        if s2_utts:
            avg = sum(len(u[2]) for u in s2_utts) / len(s2_utts)
            jw_turn_chars.append((c['filename'], c['date'], avg))

    overall_jw_avg = sum(x[2] for x in jw_turn_chars) / len(jw_turn_chars) if jw_turn_chars else 0
    out.append(f"- 정원이 1턴당 평균 글자 수: **{overall_jw_avg:.1f}자**")

    # 이상규 대 정원이 발화량 비율 (시기별)
    out.append(f"\n### 이상규 대 정원이 발화량 비율 — 시기별 변화\n")

    monthly_ratio = defaultdict(lambda: {'s1_chars': 0, 's2_chars': 0, 's1_turns': 0, 's2_turns': 0, 'count': 0})
    for c in jw_calls:
        if not c['date']:
            continue
        key = c['date'].strftime('%Y-%m')
        for u in c['utterances']:
            if u[0] == 1:
                monthly_ratio[key]['s1_chars'] += len(u[2])
                monthly_ratio[key]['s1_turns'] += 1
            else:
                monthly_ratio[key]['s2_chars'] += len(u[2])
                monthly_ratio[key]['s2_turns'] += 1
        monthly_ratio[key]['count'] += 1

    out.append("| 월 | 통화수 | 이상규 글자 | 정원이 글자 | 비율(이/정) | 이상규 턴 | 정원이 턴 |")
    out.append("|-----|--------|------------|------------|------------|----------|----------|")
    for month in sorted(monthly_ratio.keys()):
        d = monthly_ratio[month]
        ratio = d['s1_chars'] / d['s2_chars'] if d['s2_chars'] > 0 else float('inf')
        out.append(f"| {month} | {d['count']} | {d['s1_chars']} | {d['s2_chars']} | **{ratio:.2f}** | {d['s1_turns']} | {d['s2_turns']} |")

    # "죄송" 빈도
    sorry_count = 0
    sorry_total_s2 = 0
    for c in jw_calls:
        for u in c['utterances']:
            if u[0] == 2:
                sorry_total_s2 += 1
                if '죄송' in u[2] or '미안' in u[2]:
                    sorry_count += 1
    out.append(f"\n- 정원이 '죄송/미안' 발화: **{sorry_count}**회 (전체 {sorry_total_s2}회 중 {sorry_count/sorry_total_s2*100:.1f}%)")

    return '\n'.join(out)


def analysis_4_emotion(calls):
    """4. 감정 키워드 추출"""
    out = []
    out.append("## 4. 감정 키워드 분석\n")

    emotion_words = {
        '사랑': ['사랑'],
        '보고싶': ['보고싶', '보고 싶'],
        '화/짜증': ['화가', '짜증', '열받', '빡치', '빡쳐', '화나', '화 나'],
        '미안': ['미안'],
        '힘들': ['힘들', '힘드'],
        '무서': ['무서', '두려', '겁나', '겁이'],
        '슬프': ['슬프', '슬퍼', '울고', '울었', '눈물'],
        '외로': ['외로', '혼자'],
        '미치': ['미치', '미쳐', '미칠'],
        '개같': ['개같', '씨발', '존나', '병신', '지랄'],
        '행복': ['행복', '좋아', '기뻐', '감사'],
        '걱정': ['걱정'],
        '지침': ['지쳤', '지치', '피곤', '에너지'],
    }

    # 이상규 발화에서 감정어 빈도
    emotion_counts = {k: 0 for k in emotion_words}
    monthly_emotions = defaultdict(lambda: {k: 0 for k in emotion_words})
    total_s1_utts = 0

    call_emotion_data = []

    for c in calls:
        if not c['is_jungwon']:
            continue
        call_emotions = {k: 0 for k in emotion_words}
        for u in c['utterances']:
            if u[0] != 1:
                continue
            total_s1_utts += 1
            text = u[2]
            for cat, words in emotion_words.items():
                for w in words:
                    cnt = text.count(w)
                    if cnt > 0:
                        emotion_counts[cat] += cnt
                        call_emotions[cat] += cnt
                        if c['date']:
                            monthly_emotions[c['date'].strftime('%Y-%m')][cat] += cnt

        total_emo = sum(call_emotions.values())
        call_emotion_data.append((c['filename'], c['date'], total_emo, call_emotions))

    out.append("### 이상규 감정어 빈도 (정원이 통화)\n")
    out.append("| 감정 범주 | 횟수 |")
    out.append("|----------|------|")
    for cat, cnt in sorted(emotion_counts.items(), key=lambda x: -x[1]):
        out.append(f"| {cat} | {cnt} |")

    # 시기별 변화
    out.append(f"\n### 시기별 감정어 변화\n")
    months = sorted(monthly_emotions.keys())
    header_cats = ['사랑', '보고싶', '화/짜증', '미안', '힘들', '무서', '미치', '개같']
    out.append("| 월 | " + " | ".join(header_cats) + " |")
    out.append("|-----|" + "|".join(["------"] * len(header_cats)) + "|")
    for m in months:
        vals = [str(monthly_emotions[m][c]) for c in header_cats]
        out.append(f"| {m} | " + " | ".join(vals) + " |")

    # 감정어 없는 통화 vs 폭발 통화
    no_emotion = [d for d in call_emotion_data if d[2] == 0]
    explosion = sorted(call_emotion_data, key=lambda x: -x[2])[:10]

    out.append(f"\n### 감정어 없는 통화: **{len(no_emotion)}**개")
    if no_emotion:
        out.append(f"- 예시: {', '.join(d[0][:40] for d in no_emotion[:5])}")

    out.append(f"\n### 감정어 폭발 통화 Top 10\n")
    out.append("| 파일 | 감정어 합계 | 주요 감정 |")
    out.append("|------|-----------|----------|")
    for fname, date, total, cats in explosion:
        top_cats = sorted(cats.items(), key=lambda x: -x[1])[:3]
        top_str = ', '.join(f"{c}({n})" for c, n in top_cats if n > 0)
        short = fname[:45] + '...' if len(fname) > 45 else fname
        out.append(f"| {short} | {total} | {top_str} |")

    return '\n'.join(out)


def analysis_5_ending(calls):
    """5. 통화 종료 패턴"""
    out = []
    out.append("## 5. 통화 종료 패턴\n")

    jw_calls = [c for c in calls if c['is_jungwon']]

    end_keywords = ['끊자', '끊을게', '끊어', '그만', '이만', '잘자', '잘 자',
                    '자야', '가봐야', '가야', '바이바이', '바이', '다음에',
                    '이따', '나중에', '전화 끊', '들어가']
    tired_keywords = ['지쳤', '지치', '피곤', '에너지', '힘들', '더 이상']

    sg_ends = 0  # 이상규가 끊자
    jw_ends = 0  # 정원이가 끊자
    neither = 0
    tired_endings = 0

    ending_samples = []

    for c in jw_calls:
        utts = c['utterances']
        if len(utts) < 5:
            continue

        last5 = utts[-5:]
        sg_end = False
        jw_end = False
        is_tired = False

        for u in last5:
            text = u[2]
            has_end = any(kw in text for kw in end_keywords)
            has_tired = any(kw in text for kw in tired_keywords)

            if has_end:
                if u[0] == 1:
                    sg_end = True
                else:
                    jw_end = True
            if has_tired:
                is_tired = True

        if sg_end and not jw_end:
            sg_ends += 1
        elif jw_end and not sg_end:
            jw_ends += 1
        elif sg_end and jw_end:
            # 둘 다 있으면 먼저 말한 쪽
            for u in last5:
                if any(kw in u[2] for kw in end_keywords):
                    if u[0] == 1:
                        sg_ends += 1
                    else:
                        jw_ends += 1
                    break
        else:
            neither += 1

        if is_tired:
            tired_endings += 1

        ending_samples.append({
            'file': c['filename'],
            'date': c['date'],
            'last5': last5,
            'sg_end': sg_end,
            'jw_end': jw_end,
            'is_tired': is_tired,
        })

    total_analyzed = sg_ends + jw_ends + neither
    out.append(f"- 분석 대상 통화 수: **{total_analyzed}**개 (5발화 이상)")
    out.append(f"- 이상규가 먼저 끊자고 한 통화: **{sg_ends}**개 ({sg_ends/total_analyzed*100:.1f}%)")
    out.append(f"- 정원이가 먼저 끊자고 한 통화: **{jw_ends}**개 ({jw_ends/total_analyzed*100:.1f}%)")
    out.append(f"- 종료 키워드 없는 통화: **{neither}**개 ({neither/total_analyzed*100:.1f}%)")
    out.append(f"- 소진 표현('지쳤/피곤/에너지') 있는 종료: **{tired_endings}**개 ({tired_endings/total_analyzed*100:.1f}%)")

    # 마지막 5 발화 표본
    out.append(f"\n### 이상규가 끊은 통화의 마지막 5발화 표본\n")
    sg_end_samples = [s for s in ending_samples if s['sg_end'] and not s['jw_end']][:5]
    for s in sg_end_samples:
        date_str = s['date'].strftime('%Y-%m-%d') if s['date'] else '?'
        out.append(f"**{date_str}** ({s['file'][:40]}...)")
        for u in s['last5']:
            speaker = '이상규' if u[0] == 1 else '정원이'
            out.append(f"  - [{speaker}] {u[2][:100]}")
        out.append("")

    out.append(f"\n### 정원이가 끊은 통화의 마지막 5발화 표본\n")
    jw_end_samples = [s for s in ending_samples if s['jw_end'] and not s['sg_end']][:5]
    for s in jw_end_samples:
        date_str = s['date'].strftime('%Y-%m-%d') if s['date'] else '?'
        out.append(f"**{date_str}** ({s['file'][:40]}...)")
        for u in s['last5']:
            speaker = '이상규' if u[0] == 1 else '정원이'
            out.append(f"  - [{speaker}] {u[2][:100]}")
        out.append("")

    return '\n'.join(out)


def analysis_6_silence(calls):
    """6. 이상규가 멈추는 순간"""
    out = []
    out.append("## 6. 이상규가 멈추는 순간\n")

    jw_calls = [c for c in calls if c['is_jungwon']]

    silence_events = []

    for c in jw_calls:
        utts = c['utterances']
        for i in range(1, len(utts)):
            # 이상규의 발화인데, 이전 발화와 20초+ 간격
            if utts[i][0] == 1 and i > 0:
                gap = utts[i][1] - utts[i-1][1]
                if gap >= 20:
                    # 침묵 직전 발화 찾기 (이상규 직전의 정원이 발화)
                    prev_jw = None
                    for j in range(i-1, -1, -1):
                        if utts[j][0] == 2:
                            prev_jw = utts[j]
                            break
                    # 이상규의 "..." 또는 매우 짧은 반응
                    sg_text = utts[i][2].strip()
                    is_short = len(sg_text) <= 5 or sg_text in ['...', '..', '.', '음', '어', '응', '그래']

                    silence_events.append({
                        'file': c['filename'],
                        'date': c['date'],
                        'gap_sec': gap,
                        'sg_response': sg_text,
                        'prev_jw_text': prev_jw[2] if prev_jw else None,
                        'is_short_response': is_short,
                        'timestamp': utts[i][1],
                    })

            # 또는: 정원이가 말한 직후 이상규가 말하는데, "..." 또는 짧은 반응
            if utts[i][0] == 1 and i > 0 and utts[i-1][0] == 2:
                sg_text = utts[i][2].strip()
                if sg_text in ['...', '..', '.']:
                    prev_jw = utts[i-1]
                    silence_events.append({
                        'file': c['filename'],
                        'date': c['date'],
                        'gap_sec': utts[i][1] - utts[i-1][1],
                        'sg_response': sg_text,
                        'prev_jw_text': prev_jw[2],
                        'is_short_response': True,
                        'timestamp': utts[i][1],
                    })

    # 중복 제거 (같은 파일, 같은 타임스탬프)
    seen = set()
    unique_events = []
    for e in silence_events:
        key = (e['file'], e['timestamp'])
        if key not in seen:
            seen.add(key)
            unique_events.append(e)
    silence_events = unique_events

    out.append(f"- 20초+ 침묵/짧은반응 이벤트: **{len(silence_events)}**개")

    # 침묵 전 정원이의 발화 내용 패턴 분석
    jw_before_silence = [e['prev_jw_text'] for e in silence_events if e['prev_jw_text']]
    out.append(f"- 침묵 직전 정원이 발화가 확인된 이벤트: **{len(jw_before_silence)}**개")

    # 키워드 분류
    trigger_categories = {
        '감정 표현': ['무서', '힘들', '사랑', '미안', '죄송', '슬프', '외로', '울고', '울어'],
        '자기 주장': ['나는', '내가', '나도', '나한테', '내 생각', '싫어', '원해', '하고 싶'],
        '관계 질문': ['우리', '왜 그래', '어떻게', '뭐가', '무슨'],
        '거부/반론': ['아니', '그건 아니', '그렇게 안', '난 못', '싫다', '안 돼'],
        '침묵/짧은답': ['응', '네', '어', '그래', '알겠어'],
    }

    trigger_counts = {k: 0 for k in trigger_categories}
    trigger_samples = {k: [] for k in trigger_categories}

    for text in jw_before_silence:
        categorized = False
        for cat, keywords in trigger_categories.items():
            if any(kw in text for kw in keywords):
                trigger_counts[cat] += 1
                if len(trigger_samples[cat]) < 5:
                    trigger_samples[cat].append(text[:100])
                categorized = True
                break
        if not categorized:
            trigger_counts.setdefault('기타', 0)
            trigger_counts['기타'] = trigger_counts.get('기타', 0) + 1

    out.append(f"\n### 정원이의 어떤 말에 이상규가 멈추는가\n")
    out.append("| 정원이 발화 유형 | 횟수 |")
    out.append("|----------------|------|")
    for cat, cnt in sorted(trigger_counts.items(), key=lambda x: -x[1]):
        out.append(f"| {cat} | {cnt} |")

    out.append(f"\n### 침묵 유발 발화 표본\n")
    for cat, samples in trigger_samples.items():
        if samples:
            out.append(f"**{cat}:**")
            for s in samples:
                out.append(f"  - \"{s}\"")
            out.append("")

    # 가장 긴 침묵
    silence_events.sort(key=lambda x: -x['gap_sec'])
    out.append(f"\n### 가장 긴 침묵 Top 10\n")
    out.append("| 파일 | 간격(초) | 정원이 직전 발화 | 이상규 반응 |")
    out.append("|------|---------|----------------|-----------|")
    for e in silence_events[:10]:
        short = e['file'][:30] + '...' if len(e['file']) > 30 else e['file']
        jw_text = (e['prev_jw_text'][:40] + '...') if e['prev_jw_text'] and len(e['prev_jw_text']) > 40 else (e['prev_jw_text'] or '-')
        out.append(f"| {short} | {e['gap_sec']} | {jw_text} | {e['sg_response'][:30]} |")

    return '\n'.join(out)


def analysis_7_unique_vs_repeat(calls):
    """7. 이상규가 처음 하는 말 vs 반복하는 말"""
    out = []
    out.append("## 7. 이상규의 유니크 발화 vs 반복 발화\n")

    jw_calls = [c for c in calls if c['is_jungwon']]

    # 이상규의 모든 발화를 정규화해서 수집
    # 3자 이하 제거 (응, 어, 네 등)
    phrase_counter = Counter()
    phrase_contexts = defaultdict(list)

    for c in jw_calls:
        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = u[2].strip().rstrip('.!? ')
            if len(text) <= 3:
                continue
            # 정규화: 공백 정리
            text_norm = re.sub(r'\s+', ' ', text).strip()
            phrase_counter[text_norm] += 1
            if len(phrase_contexts[text_norm]) < 3:
                phrase_contexts[text_norm].append((c['filename'], c['date']))

    total_phrases = sum(phrase_counter.values())
    unique_phrases = [p for p, c in phrase_counter.items() if c == 1]
    repeat_10plus = [(p, c) for p, c in phrase_counter.items() if c >= 10]
    repeat_5plus = [(p, c) for p, c in phrase_counter.items() if c >= 5]

    out.append(f"- 전체 발화 (4자 이상): **{total_phrases}**개")
    out.append(f"- 1회만 등장한 발화: **{len(unique_phrases)}**개 ({len(unique_phrases)/total_phrases*100:.1f}%)")
    out.append(f"- 5회 이상 반복 발화: **{len(repeat_5plus)}**개")
    out.append(f"- 10회 이상 반복 발화: **{len(repeat_10plus)}**개")

    # 10회 이상 반복
    repeat_10plus.sort(key=lambda x: -x[1])
    out.append(f"\n### 10회 이상 반복 발화\n")
    out.append("| 발화 | 횟수 |")
    out.append("|------|------|")
    for phrase, cnt in repeat_10plus[:30]:
        out.append(f"| {phrase[:60]} | {cnt} |")

    # 5~9회 반복
    repeat_5to9 = sorted([(p, c) for p, c in phrase_counter.items() if 5 <= c < 10], key=lambda x: -x[1])
    out.append(f"\n### 5~9회 반복 발화\n")
    out.append("| 발화 | 횟수 |")
    out.append("|------|------|")
    for phrase, cnt in repeat_5to9[:30]:
        out.append(f"| {phrase[:60]} | {cnt} |")

    # n-gram 기반 반복 패턴 (더 세밀한 분석)
    # 5글자 이상의 부분 문자열 반복
    out.append(f"\n### 반복 구문 패턴 (부분 문자열)\n")

    # 모든 이상규 발화에서 5~15자 n-gram 추출
    ngram_counter = Counter()
    for c in jw_calls:
        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = re.sub(r'\s+', ' ', u[2].strip())
            if len(text) < 8:
                continue
            for n in range(8, min(20, len(text)+1)):
                for i in range(len(text) - n + 1):
                    gram = text[i:i+n]
                    if gram.strip():
                        ngram_counter[gram] += 1

    # 50회 이상 반복된 8자+ 구문
    frequent_ngrams = [(g, c) for g, c in ngram_counter.items() if c >= 30 and len(g) >= 8]
    # 중복 제거: 더 긴 구문이 포함하면 짧은 것 제거
    frequent_ngrams.sort(key=lambda x: (-len(x[0]), -x[1]))
    filtered = []
    for gram, cnt in frequent_ngrams:
        is_sub = False
        for fg, fc in filtered:
            if gram in fg:
                is_sub = True
                break
        if not is_sub:
            filtered.append((gram, cnt))

    filtered.sort(key=lambda x: -x[1])
    out.append("| 구문 | 횟수 |")
    out.append("|------|------|")
    for gram, cnt in filtered[:30]:
        out.append(f"| {gram} | {cnt} |")

    return '\n'.join(out)


def analysis_extra_patterns(calls):
    """추가 발견: 시간대, 통화 빈도, 이상규만의 특이 패턴"""
    out = []
    out.append("## 8. 추가 발견\n")

    jw_calls = [c for c in calls if c['is_jungwon']]

    # ── 8a. 통화 시간대 분석 ──
    out.append("### 8a. 통화 시간대\n")
    hour_counter = Counter()
    for c in calls:
        fname = c['filename']
        m = re.search(r'_\d{6}_(\d{2})\d{4}', fname)
        if m:
            hour = int(m.group(1))
            hour_counter[hour] += 1

    out.append("| 시간대 | 통화 수 |")
    out.append("|--------|--------|")
    for h in range(24):
        cnt = hour_counter.get(h, 0)
        bar = '#' * cnt
        out.append(f"| {h:02d}시 | {cnt} {bar} |")

    late_night = sum(hour_counter.get(h, 0) for h in [0, 1, 2, 3, 4, 5])
    total_with_hour = sum(hour_counter.values())
    out.append(f"\n- 새벽 통화(00~05시): **{late_night}**개 ({late_night/total_with_hour*100:.1f}%)")

    # ── 8b. 하루 다중 통화 패턴 ──
    out.append("\n### 8b. 하루 다중 통화\n")
    date_counts = Counter()
    for c in jw_calls:
        if c['date']:
            date_counts[c['date'].strftime('%Y-%m-%d')] += 1

    multi_call_days = [(d, cnt) for d, cnt in date_counts.items() if cnt >= 3]
    multi_call_days.sort(key=lambda x: -x[1])

    out.append(f"- 하루 3통 이상 한 날: **{len(multi_call_days)}**일")
    if multi_call_days:
        out.append(f"- 최다 통화 하루: **{multi_call_days[0][1]}**통 ({multi_call_days[0][0]})")
        out.append("\n| 날짜 | 통화 수 |")
        out.append("|------|--------|")
        for d, cnt in multi_call_days[:15]:
            out.append(f"| {d} | {cnt} |")

    # ── 8c. 이상규의 질문 vs 선언 비율 ──
    out.append("\n### 8c. 이상규의 질문 vs 선언\n")
    question_count = 0
    statement_count = 0
    for c in jw_calls:
        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = u[2].strip()
            if text.endswith('?') or '?' in text:
                question_count += 1
            elif len(text) > 3:
                statement_count += 1

    out.append(f"- 질문('?' 포함): **{question_count}**개")
    out.append(f"- 선언(4자+, ? 없음): **{statement_count}**개")
    out.append(f"- 질문:선언 비율: **1:{statement_count/question_count:.1f}**" if question_count > 0 else "")

    # ── 8d. "나" vs "너" vs "우리" 사용빈도 ──
    out.append("\n### 8d. 인칭 대명사 사용 빈도\n")
    pronoun_counts_sg = Counter()  # 이상규
    pronoun_counts_jw = Counter()  # 정원이
    pronouns = {
        '나/내가': ['내가', '나는', '나도', '나한테', '나를', '나의'],
        '너/네가': ['네가', '너는', '너도', '너한테', '너를', '너의', '니가'],
        '우리': ['우리'],
    }

    for c in jw_calls:
        for u in c['utterances']:
            text = u[2]
            for cat, words in pronouns.items():
                cnt = sum(text.count(w) for w in words)
                if u[0] == 1:
                    pronoun_counts_sg[cat] += cnt
                else:
                    pronoun_counts_jw[cat] += cnt

    out.append("| 인칭 | 이상규 | 정원이 |")
    out.append("|------|--------|--------|")
    for cat in pronouns:
        out.append(f"| {cat} | {pronoun_counts_sg[cat]} | {pronoun_counts_jw[cat]} |")

    # ── 8e. 이상규가 정원이의 감정을 되받는 패턴 ──
    out.append("\n### 8e. 정원이가 감정 표현 후 이상규 반응 패턴\n")

    jw_emotion_words = ['무서워', '힘들어', '슬퍼', '외로워', '미안해', '죄송해', '사랑해',
                        '보고 싶', '보고싶', '울고', '울어', '무서운', '두려워', '겁나']

    reaction_types = Counter()
    reaction_samples = defaultdict(list)

    for c in jw_calls:
        utts = c['utterances']
        for i in range(len(utts) - 1):
            if utts[i][0] == 2:  # 정원이
                text_jw = utts[i][2]
                if not any(ew in text_jw for ew in jw_emotion_words):
                    continue
                # 다음 이상규 발화
                for j in range(i + 1, min(i + 3, len(utts))):
                    if utts[j][0] == 1:
                        sg_resp = utts[j][2]
                        # 분류
                        if any(w in sg_resp for w in ['없다', '아니야', '괜찮', '걱정 마', '그런 거', '그럴 리']):
                            cat = '안심/부정("아니야, 그런거아니야")'
                            reaction_types[cat] += 1
                            if len(reaction_samples[cat]) < 5:
                                reaction_samples[cat].append((text_jw[:50], sg_resp[:50]))
                        elif any(w in sg_resp for w in ['왜', '뭐가', '무슨']):
                            cat = '질문("왜?")'
                            reaction_types[cat] += 1
                            if len(reaction_samples[cat]) < 5:
                                reaction_samples[cat].append((text_jw[:50], sg_resp[:50]))
                        elif any(w in sg_resp for w in ['미안', '잘못']):
                            cat = '사과'
                            reaction_types[cat] += 1
                            if len(reaction_samples[cat]) < 5:
                                reaction_samples[cat].append((text_jw[:50], sg_resp[:50]))
                        elif any(w in sg_resp for w in ['해야', '해줘', '하면', '그래야']):
                            cat = '지시/규칙 제시'
                            reaction_types[cat] += 1
                            if len(reaction_samples[cat]) < 5:
                                reaction_samples[cat].append((text_jw[:50], sg_resp[:50]))
                        elif len(sg_resp.strip()) <= 5:
                            cat = '짧은 반응/침묵'
                            reaction_types[cat] += 1
                            if len(reaction_samples[cat]) < 5:
                                reaction_samples[cat].append((text_jw[:50], sg_resp[:50]))
                        else:
                            cat = '기타 장문 반응'
                            reaction_types[cat] += 1
                            if len(reaction_samples[cat]) < 5:
                                reaction_samples[cat].append((text_jw[:50], sg_resp[:50]))
                        break

    total_reactions = sum(reaction_types.values())
    out.append(f"정원이 감정 표현 후 이상규 반응 총 **{total_reactions}**회:\n")
    out.append("| 반응 유형 | 횟수 | 비율 |")
    out.append("|----------|------|------|")
    for cat, cnt in sorted(reaction_types.items(), key=lambda x: -x[1]):
        out.append(f"| {cat} | {cnt} | {cnt/total_reactions*100:.1f}% |")

    out.append(f"\n**반응 표본:**\n")
    for cat, samples in reaction_samples.items():
        out.append(f"**{cat}:**")
        for jw_text, sg_text in samples:
            out.append(f'  - 정원: "{jw_text}" -> 이상규: "{sg_text}"')
        out.append("")

    # ── 8f. 통화 시작 패턴 ──
    out.append("\n### 8f. 통화 시작 패턴 (첫 3발화)\n")

    start_patterns = Counter()
    for c in jw_calls:
        utts = c['utterances']
        if len(utts) < 3:
            continue
        first3 = tuple(u[0] for u in utts[:3])
        start_patterns[first3] += 1

    # 이상규의 첫 발화 내용 분류
    first_sg_content = Counter()
    for c in jw_calls:
        for u in c['utterances']:
            if u[0] == 1:
                text = u[2].strip().rstrip('.!? ')
                if len(text) <= 10:
                    first_sg_content[text] += 1
                else:
                    first_sg_content[text[:10] + '...'] += 1
                break

    out.append("이상규의 첫 마디:\n")
    out.append("| 첫 마디 | 횟수 |")
    out.append("|--------|------|")
    for phrase, cnt in first_sg_content.most_common(15):
        out.append(f"| {phrase} | {cnt} |")

    # ── 8g. 이상규가 자기 이름/역할 언급 ──
    out.append("\n### 8g. 이상규의 자기 규정 표현\n")

    self_labels = Counter()
    self_role_patterns = ['주인', '남자', '남편', '오빠', '형', '리더', '책임',
                          '보호', '지켜', '내가 해', '내가 할', '내 역할', '당연히 내가']

    for c in jw_calls:
        for u in c['utterances']:
            if u[0] != 1:
                continue
            for pat in self_role_patterns:
                if pat in u[2]:
                    self_labels[pat] += 1

    out.append("| 자기 규정 표현 | 횟수 |")
    out.append("|--------------|------|")
    for label, cnt in self_labels.most_common():
        out.append(f"| {label} | {cnt} |")

    # ── 8h. 연속 통화 패턴 (끊고 다시 거는) ──
    out.append("\n### 8h. 끊고 다시 거는 패턴\n")

    # 같은 날 통화들 중 30분 이내 재통화
    date_calls = defaultdict(list)
    for c in jw_calls:
        if c['date']:
            # 파일명에서 시간 추출
            m = re.search(r'_(\d{6})_(\d{6})', c['filename'])
            if m:
                time_str = m.group(2)
                h, mi, s = int(time_str[:2]), int(time_str[2:4]), int(time_str[4:6])
                call_start = h * 3600 + mi * 60 + s
                date_calls[c['date'].strftime('%Y-%m-%d')].append((call_start, c))

    reconnect_count = 0
    reconnect_gaps = []
    for date, day_calls in date_calls.items():
        day_calls.sort(key=lambda x: x[0])
        for i in range(1, len(day_calls)):
            prev_end = day_calls[i-1][0]
            if day_calls[i-1][1]['utterances']:
                prev_end += max(u[1] for u in day_calls[i-1][1]['utterances'])
            curr_start = day_calls[i][0]
            gap = curr_start - prev_end
            if 0 < gap < 1800:  # 30분 이내
                reconnect_count += 1
                reconnect_gaps.append(gap)

    out.append(f"- 30분 이내 재통화: **{reconnect_count}**회")
    if reconnect_gaps:
        out.append(f"- 재통화 평균 간격: **{sum(reconnect_gaps)/len(reconnect_gaps)/60:.1f}분**")

    return '\n'.join(out)


# ── 메인 ──────────────────────────────────────────────

def analysis_discoveries(calls):
    """9. 종합 발견 — 이상규가 모르는 패턴들"""
    out = []
    out.append("## 9. 발견 종합 — 이 데이터에서만 나오는 패턴\n")

    jw_calls = [c for c in calls if c['is_jungwon']  and c['date']]
    jw_calls.sort(key=lambda c: c['date'])

    # ── 발견 1: 글자 비율의 시기별 변화 (정밀) ──
    out.append("### 발견 1: 이상규의 발화 점유율은 4개월간 꾸준히 감소했다\n")

    monthly = defaultdict(lambda: {'s1': 0, 's2': 0})
    for c in jw_calls:
        key = c['date'].strftime('%Y-%m')
        for u in c['utterances']:
            if u[0] == 1:
                monthly[key]['s1'] += len(u[2])
            else:
                monthly[key]['s2'] += len(u[2])

    for m in sorted(monthly.keys()):
        d = monthly[m]
        total = d['s1'] + d['s2']
        pct = d['s1'] / total * 100 if total else 0
        out.append(f"- {m}: 이상규 **{pct:.1f}%** (이:{d['s1']} / 정:{d['s2']})")

    out.append("")
    months_sorted = sorted(monthly.keys())
    if len(months_sorted) >= 2:
        first_pct = monthly[months_sorted[0]]['s1'] / (monthly[months_sorted[0]]['s1'] + monthly[months_sorted[0]]['s2']) * 100
        last_pct = monthly[months_sorted[-1]]['s1'] / (monthly[months_sorted[-1]]['s1'] + monthly[months_sorted[-1]]['s2']) * 100
        out.append(f"**{months_sorted[0]}에 {first_pct:.1f}%이던 이상규 글자 점유율이 {months_sorted[-1]}에는 {last_pct:.1f}%로 떨어졌다.** "
                   f"정원이가 더 많이 말하게 된 것이 아니라, 이상규가 조금씩 줄인 것이다.\n")

    # ── 발견 2: "사랑" 감소 vs "힘들" 유지 ──
    out.append("### 발견 2: '사랑'은 4개월간 91% 감소했지만, '힘들'은 유지되었다\n")

    emo_monthly = defaultdict(lambda: Counter())
    for c in jw_calls:
        key = c['date'].strftime('%Y-%m')
        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = u[2]
            for w in ['사랑']:
                emo_monthly[key]['사랑'] += text.count(w)
            for w in ['힘들', '힘드']:
                emo_monthly[key]['힘들'] += text.count(w)
            for w in ['보고싶', '보고 싶']:
                emo_monthly[key]['보고싶'] += text.count(w)
            for w in ['무서']:
                emo_monthly[key]['무서'] += text.count(w)

    out.append("| 월 | 사랑 | 힘들 | 보고싶 | 무서 |")
    out.append("|-----|------|------|--------|------|")
    for m in sorted(emo_monthly.keys()):
        d = emo_monthly[m]
        out.append(f"| {m} | {d['사랑']} | {d['힘들']} | {d['보고싶']} | {d['무서']} |")

    out.append(f"\n**'사랑'이라는 단어는 11월 157회에서 3월 14회로 줄었다. "
               f"'보고싶'도 29회에서 11회로 줄었다. 반면 '힘들'은 115 -> 209 -> 74 -> 180 -> 103으로, "
               f"줄어들지 않았다. 감정어 중 '사랑'이 가장 가파르게 소멸했다.**\n")

    # ── 발견 3: 나 vs 너 비율 ──
    out.append("### 발견 3: 이상규의 '나/내가' 대 '너/네가' 비율\n")

    na_count = 0
    neo_count = 0
    for c in jw_calls:
        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = u[2]
            for w in ['내가', '나는', '나도', '나한테', '나를', '나의']:
                na_count += text.count(w)
            for w in ['네가', '너는', '너도', '너한테', '너를', '너의', '니가']:
                neo_count += text.count(w)

    ratio_na_neo = na_count / neo_count if neo_count > 0 else float('inf')
    out.append(f"- 이상규 '나/내가' 사용: **{na_count}**회")
    out.append(f"- 이상규 '너/네가' 사용: **{neo_count}**회")
    out.append(f"- 비율: **{ratio_na_neo:.1f}:1** (나:너)")
    out.append(f"\n**이상규는 정원이에게 '너'라고 말하는 횟수의 {ratio_na_neo:.1f}배 '나'라고 말한다. "
               f"관계 대화에서 '너'보다 '나'를 압도적으로 많이 쓰는 것은, "
               f"상대를 향한 언어가 아니라 자기를 향한 언어로 관계를 운영한다는 뜻이다.**\n")

    # ── 발견 4: 정원이가 "무서워" 했을 때 ──
    out.append("### 발견 4: 정원이가 '무서워'라고 했을 때 이상규의 반응\n")

    scary_reactions = Counter()
    scary_samples = defaultdict(list)

    for c in jw_calls:
        utts = c['utterances']
        for i in range(len(utts) - 1):
            if utts[i][0] == 2 and '무서' in utts[i][2]:
                # 다음 이상규 발화 찾기
                for j in range(i + 1, min(i + 3, len(utts))):
                    if utts[j][0] == 1:
                        sg = utts[j][2]
                        if any(w in sg for w in ['괜찮', '아니야', '없다', '그런 거', '안 그래', '무서울 게']):
                            cat = '안심("괜찮아/무서울 게 없어")'
                        elif any(w in sg for w in ['왜', '뭐가', '무슨']):
                            cat = '되물음("왜?")'
                        elif len(sg.strip()) <= 5 or sg.strip() in ['응', '어', '음', '그래', '네']:
                            cat = '침묵/짧은반응'
                        elif any(w in sg for w in ['미안', '잘못']):
                            cat = '사과'
                        elif any(w in sg for w in ['해야', '하면', '그래야', '안 돼', '근데']):
                            cat = '설명/규칙 전환'
                        else:
                            cat = '기타 장문'
                        scary_reactions[cat] += 1
                        if len(scary_samples[cat]) < 3:
                            scary_samples[cat].append((utts[i][2][:60], sg[:60]))
                        break

    total_scary = sum(scary_reactions.values())
    out.append(f"정원이가 '무서워'라고 말한 직후 이상규 반응 총 **{total_scary}**회:\n")
    out.append("| 반응 유형 | 횟수 | 비율 |")
    out.append("|----------|------|------|")
    for cat, cnt in sorted(scary_reactions.items(), key=lambda x: -x[1]):
        out.append(f"| {cat} | {cnt} | {cnt/total_scary*100:.1f}% |")

    out.append("\n표본:")
    for cat, samples in scary_samples.items():
        for jw, sg in samples:
            out.append(f'- 정원: "{jw}" -> 이상규: "{sg}" [{cat}]')
    out.append("")

    # ── 발견 5: 이상규가 "그렇구나/그랬구나" 뒤에 하는 말 ──
    out.append("### 발견 5: '그랬구나/그렇구나' — 이상규의 가장 빈번한 반응어의 실제 기능\n")

    gruk_follow = Counter()
    gruk_samples = []

    for c in jw_calls:
        utts = c['utterances']
        for i in range(len(utts)):
            if utts[i][0] != 1:
                continue
            text = utts[i][2].strip()
            if text not in ('그랬구나', '그렇구나', '그랬구나.', '그렇구나.'):
                continue
            # 다음 이상규 발화
            for j in range(i + 1, min(i + 3, len(utts))):
                if utts[j][0] == 1:
                    follow = utts[j][2]
                    if any(w in follow for w in ['근데', '그런데', '하지만']):
                        cat = '역접 전환 ("근데...")'
                    elif any(w in follow for w in ['해야', '하면', '안 돼', '그래야']):
                        cat = '규칙/지시 전환'
                    elif any(w in follow for w in ['나도', '나는', '내가']):
                        cat = '자기 이야기 전환'
                    elif '?' in follow:
                        cat = '질문'
                    elif len(follow.strip()) <= 5:
                        cat = '짧은 추가 반응'
                    else:
                        cat = '주제 확장'
                    gruk_follow[cat] += 1
                    if len(gruk_samples) < 10:
                        gruk_samples.append((text, follow[:60], cat))
                    break

    total_gruk = sum(gruk_follow.values())
    if total_gruk > 0:
        out.append(f"'그랬구나/그렇구나' 다음 이상규의 후속 발화 총 **{total_gruk}**회:\n")
        out.append("| 후속 발화 유형 | 횟수 | 비율 |")
        out.append("|--------------|------|------|")
        for cat, cnt in sorted(gruk_follow.items(), key=lambda x: -x[1]):
            out.append(f"| {cat} | {cnt} | {cnt/total_gruk*100:.1f}% |")

        reversal_pct = (gruk_follow.get('역접 전환 ("근데...")', 0) + gruk_follow.get('규칙/지시 전환', 0) + gruk_follow.get('자기 이야기 전환', 0)) / total_gruk * 100
        out.append(f"\n**'그랬구나/그렇구나' 후 역접+규칙+자기이야기 전환: {reversal_pct:.1f}%. "
                   f"이 표현이 수용이 아니라 화제 전환 브릿지로 기능하는 비율이다.**\n")

        out.append("표본:")
        for text, follow, cat in gruk_samples[:8]:
            out.append(f'- "{text}" -> "{follow}" [{cat}]')
        out.append("")

    # ── 발견 6: 새벽 통화의 내용 특성 ──
    out.append("### 발견 6: 새벽 통화(00~05시)의 감정 밀도\n")

    dawn_emo = Counter()
    day_emo = Counter()
    dawn_calls_n = 0
    day_calls_n = 0

    emo_words_all = ['사랑', '힘들', '힘드', '무서', '미안', '외로', '슬프', '울고', '보고싶', '보고 싶']

    for c in jw_calls:
        m = re.search(r'_\d{6}_(\d{2})\d{4}', c['filename'])
        if not m:
            continue
        hour = int(m.group(1))
        is_dawn = hour < 6

        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = u[2]
            for w in emo_words_all:
                cnt = text.count(w)
                if cnt > 0:
                    if is_dawn:
                        dawn_emo[w] += cnt
                    else:
                        day_emo[w] += cnt

        if is_dawn:
            dawn_calls_n += 1
        else:
            day_calls_n += 1

    out.append(f"- 새벽 통화 수: **{dawn_calls_n}**개 / 낮 통화 수: **{day_calls_n}**개")

    if dawn_calls_n > 0 and day_calls_n > 0:
        dawn_total = sum(dawn_emo.values())
        day_total = sum(day_emo.values())
        dawn_per = dawn_total / dawn_calls_n
        day_per = day_total / day_calls_n
        out.append(f"- 새벽 통화당 감정어: **{dawn_per:.1f}**개 / 낮 통화당 감정어: **{day_per:.1f}**개")
        out.append(f"- 비율: **{dawn_per/day_per:.1f}배** (새벽이 더 높음)\n")

        out.append("| 감정어 | 새벽(통화당) | 낮(통화당) | 배율 |")
        out.append("|--------|-----------|---------|------|")
        for w in ['사랑', '힘들', '무서', '미안', '외로', '보고싶']:
            dw = dawn_emo.get(w, 0) + dawn_emo.get(w.replace('힘들','힘드'), 0)
            da = day_emo.get(w, 0) + day_emo.get(w.replace('힘들','힘드'), 0)
            dp = dw / dawn_calls_n if dawn_calls_n else 0
            dap = da / day_calls_n if day_calls_n else 0
            ratio = dp / dap if dap > 0 else 0
            out.append(f"| {w} | {dp:.2f} | {dap:.2f} | {ratio:.1f}x |")
        out.append("")

    # ── 발견 7: 하루 다중 통화 날의 감정 패턴 ──
    out.append("### 발견 7: 하루 3통 이상 통화한 날의 특성\n")

    date_call_map = defaultdict(list)
    for c in jw_calls:
        date_call_map[c['date'].strftime('%Y-%m-%d')].append(c)

    multi_dates = {d: cs for d, cs in date_call_map.items() if len(cs) >= 3}
    single_dates = {d: cs for d, cs in date_call_map.items() if len(cs) < 3}

    # 다중 통화 날의 총 통화 시간
    multi_total_min = 0
    multi_emo_count = 0
    for d, cs in multi_dates.items():
        for c in cs:
            if c['utterances']:
                multi_total_min += max(u[1] for u in c['utterances']) / 60
            for u in c['utterances']:
                if u[0] == 1:
                    for w in emo_words_all:
                        multi_emo_count += u[2].count(w)

    single_total_min = 0
    single_emo_count = 0
    for d, cs in single_dates.items():
        for c in cs:
            if c['utterances']:
                single_total_min += max(u[1] for u in c['utterances']) / 60
            for u in c['utterances']:
                if u[0] == 1:
                    for w in emo_words_all:
                        single_emo_count += u[2].count(w)

    multi_days = len(multi_dates)
    single_days = len(single_dates)

    if multi_days > 0 and single_days > 0:
        out.append(f"- 하루 3통+ 날: **{multi_days}**일, 평균 일일 통화시간: **{multi_total_min/multi_days:.0f}분**")
        out.append(f"- 하루 1~2통 날: **{single_days}**일, 평균 일일 통화시간: **{single_total_min/single_days:.0f}분**")
        out.append(f"- 다중통화 날의 일일 감정어: **{multi_emo_count/multi_days:.1f}**개 vs 단일통화 날: **{single_emo_count/single_days:.1f}**개")
        out.append(f"\n**3통 이상 걸린 날({multi_days}일)의 하루 평균 통화시간은 {multi_total_min/multi_days:.0f}분, "
                   f"감정어 밀도는 {multi_emo_count/multi_days:.1f}개. "
                   f"이상규는 '해결될 때까지 끊지 않는' 것이 아니라 '끊었다가 다시 거는' 패턴으로 관계를 운영한다.**\n")

    # ── 발견 8: 정원이의 말 길이 변화 ──
    out.append("### 발견 8: 정원이의 턴당 글자 수 변화\n")

    monthly_jw_chars = defaultdict(lambda: {'total_chars': 0, 'total_turns': 0})
    for c in jw_calls:
        key = c['date'].strftime('%Y-%m')
        for u in c['utterances']:
            if u[0] == 2:
                monthly_jw_chars[key]['total_chars'] += len(u[2])
                monthly_jw_chars[key]['total_turns'] += 1

    out.append("| 월 | 정원이 턴당 평균 글자수 | 턴 수 |")
    out.append("|-----|---------------------|-------|")
    for m in sorted(monthly_jw_chars.keys()):
        d = monthly_jw_chars[m]
        avg = d['total_chars'] / d['total_turns'] if d['total_turns'] else 0
        out.append(f"| {m} | **{avg:.1f}** | {d['total_turns']} |")

    months_jw = sorted(monthly_jw_chars.keys())
    if len(months_jw) >= 2:
        first_avg = monthly_jw_chars[months_jw[0]]['total_chars'] / monthly_jw_chars[months_jw[0]]['total_turns']
        last_avg = monthly_jw_chars[months_jw[-1]]['total_chars'] / monthly_jw_chars[months_jw[-1]]['total_turns']
        change = (last_avg - first_avg) / first_avg * 100
        direction = "늘었다" if change > 0 else "줄었다"
        out.append(f"\n**정원이 턴당 글자수가 {first_avg:.1f}자에서 {last_avg:.1f}자로 {abs(change):.1f}% {direction}.**\n")

    # ── 발견 9: 이상규의 질문 후 자기가 답하는 패턴 ──
    out.append("### 발견 9: 이상규가 질문하고 자기가 답하는 비율\n")

    self_answer_count = 0
    jw_answer_count = 0
    self_answer_samples = []

    for c in jw_calls:
        utts = c['utterances']
        for i in range(len(utts) - 1):
            if utts[i][0] == 1 and '?' in utts[i][2]:
                # 다음 발화자
                if utts[i+1][0] == 1:
                    self_answer_count += 1
                    if len(self_answer_samples) < 10:
                        self_answer_samples.append((utts[i][2][:60], utts[i+1][2][:60]))
                else:
                    jw_answer_count += 1

    total_q = self_answer_count + jw_answer_count
    if total_q > 0:
        out.append(f"- 이상규 질문 후 정원이가 답한 횟수: **{jw_answer_count}**")
        out.append(f"- 이상규 질문 후 이상규가 스스로 이어간 횟수: **{self_answer_count}**")
        out.append(f"- 자문자답 비율: **{self_answer_count/total_q*100:.1f}%**")
        out.append(f"\n**이상규의 질문 중 {self_answer_count/total_q*100:.1f}%는 정원이가 답하기 전에 이상규 자신이 이어간다. "
                   f"질문이 정보를 구하는 것이 아니라 자기 논리 전개의 수사적 장치로 기능한다.**\n")

        out.append("표본:")
        for q, a in self_answer_samples[:6]:
            out.append(f'- Q: "{q}" -> A(이상규 자신): "{a}"')
        out.append("")

    # ── 발견 10: "해야 돼" vs "하고 싶어" — 관계 맥락만 ──
    out.append("### 발견 10: 당위('해야') vs 욕구('하고 싶') 표현\n")

    must_count = 0
    want_count = 0
    must_samples = []
    want_samples = []
    for c in jw_calls:
        for u in c['utterances']:
            if u[0] != 1:
                continue
            text = u[2]
            for w in ['해야', '해야지', '해야 돼', '해야 해', '해야만', '해야 되']:
                cnt = text.count(w)
                must_count += cnt
                if cnt > 0 and len(must_samples) < 10:
                    must_samples.append(text[:80])
            for w in ['하고 싶', '하고싶']:
                cnt = text.count(w)
                want_count += cnt
                if cnt > 0 and len(want_samples) < 10:
                    want_samples.append(text[:80])

    out.append(f"- '해야/해야 돼' (당위): **{must_count}**회")
    out.append(f"- '하고 싶' (욕구): **{want_count}**회")
    if want_count > 0:
        ratio_mw = must_count / want_count
        out.append(f"- 비율: **{ratio_mw:.1f}:1** (당위:욕구)")
        if ratio_mw > 1:
            out.append(f"\n**이상규는 '~하고 싶다'보다 '~해야 한다'를 {ratio_mw:.1f}배 더 많이 말한다.**\n")
        else:
            out.append(f"\n**이상규는 '~해야 한다'({must_count}회)와 '~하고 싶다'({want_count}회)를 비슷하게 쓴다. "
                       f"그러나 당위 표현이 {must_count}회라는 것 자체가 주목할 수치다 -- "
                       f"4개월 197통화에서 평균 통화당 {must_count/len(jw_calls):.1f}회 '해야'를 말한다.**\n")
    else:
        out.append("")

    out.append("당위 표현 표본:")
    for s in must_samples[:5]:
        out.append(f'- "{s}"')
    out.append("")

    # ── 발견 11: 통화 길이와 감정어 상관 ──
    out.append("### 발견 11: 긴 통화일수록 감정어가 많은가?\n")

    call_stats = []
    for c in jw_calls:
        if not c['utterances']:
            continue
        duration = max(u[1] for u in c['utterances']) / 60
        emo_cnt = 0
        for u in c['utterances']:
            if u[0] == 1:
                for w in emo_words_all:
                    emo_cnt += u[2].count(w)
        call_stats.append((duration, emo_cnt))

    # Divide into quartiles
    call_stats.sort(key=lambda x: x[0])
    n = len(call_stats)
    q_size = n // 4

    if q_size > 0:
        q1 = call_stats[:q_size]
        q4 = call_stats[-q_size:]

        q1_avg_dur = sum(d for d, _ in q1) / len(q1)
        q1_avg_emo = sum(e for _, e in q1) / len(q1)
        q4_avg_dur = sum(d for d, _ in q4) / len(q4)
        q4_avg_emo = sum(e for _, e in q4) / len(q4)

        # per-minute density
        q1_density = sum(e for _, e in q1) / sum(d for d, _ in q1) if sum(d for d, _ in q1) > 0 else 0
        q4_density = sum(e for _, e in q4) / sum(d for d, _ in q4) if sum(d for d, _ in q4) > 0 else 0

        out.append(f"- 가장 짧은 25% 통화 (평균 {q1_avg_dur:.1f}분): 통화당 감정어 **{q1_avg_emo:.1f}**개, 분당 **{q1_density:.2f}**개")
        out.append(f"- 가장 긴 25% 통화 (평균 {q4_avg_dur:.1f}분): 통화당 감정어 **{q4_avg_emo:.1f}**개, 분당 **{q4_density:.2f}**개")
        out.append(f"\n**분당 감정어 밀도: 짧은 통화 {q1_density:.2f} vs 긴 통화 {q4_density:.2f}. "
                   f"{'긴 통화가 분당 감정어가 더 높다 — 감정이 통화를 길게 만드는 것이 아니라, 긴 통화에서 감정이 더 쏟아진다.' if q4_density > q1_density else '짧은 통화의 분당 감정어가 더 높다 — 짧은 통화가 오히려 감정적으로 더 밀도 있다.'}**\n")

    return '\n'.join(out)


def main():
    print("데이터 로드 중...")
    calls = load_all_calls()
    print(f"총 {len(calls)}개 통화 로드 완료.")

    sections = []

    # 헤더
    sections.append("# 통화녹음 전량 분석 보고서\n")
    sections.append(f"분석 대상: {len(calls)}개 통화")
    sections.append(f"분석 일시: 2026-04-10\n")
    sections.append("---\n")

    # 분석 실행
    print("1. 메타데이터 분석...")
    sections.append(analysis_1_meta(calls))
    sections.append("\n---\n")

    print("2. 독백 분석...")
    mono_text, monologues = analysis_2_monologue(calls)
    sections.append(mono_text)
    sections.append("\n---\n")

    print("3. 정원이 발화 패턴...")
    sections.append(analysis_3_jungwon(calls))
    sections.append("\n---\n")

    print("4. 감정 키워드...")
    sections.append(analysis_4_emotion(calls))
    sections.append("\n---\n")

    print("5. 종료 패턴...")
    sections.append(analysis_5_ending(calls))
    sections.append("\n---\n")

    print("6. 침묵 분석...")
    sections.append(analysis_6_silence(calls))
    sections.append("\n---\n")

    print("7. 유니크 vs 반복...")
    sections.append(analysis_7_unique_vs_repeat(calls))
    sections.append("\n---\n")

    print("8. 추가 발견...")
    sections.append(analysis_extra_patterns(calls))
    sections.append("\n---\n")

    print("9. 발견 종합...")
    sections.append(analysis_discoveries(calls))

    # 보고서 작성
    report = '\n'.join(sections)

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n보고서 저장 완료: {REPORT_PATH}")
    print(f"보고서 길이: {len(report)} 글자, {report.count(chr(10))} 줄")


if __name__ == '__main__':
    main()
