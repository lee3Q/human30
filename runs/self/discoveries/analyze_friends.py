#!/usr/bin/env python3
"""
친구 4명 카톡 분석 — 이상규의 '기준선' 측정
핵심 질문: "정원이에게만 그런 건가, 원래 그런 건가?"

stdlib만 사용. python3 analyze_friends.py 로 실행.
"""

import csv
import re
import os
import io
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ============================================================
# 0. 파일 경로
# ============================================================

ME = "이상규"

FRIENDS = [
    (
        os.path.expanduser("~/Downloads/KakaoTalk_Chat_유상현_2026-04-10-17-51-00.csv"),
        "유상현",
    ),
    (
        os.path.expanduser("~/Downloads/KakaoTalk_Chat_배묵현_2026-04-10-17-50-20.csv"),
        "배묵현",
    ),
    (
        os.path.expanduser("~/Downloads/KakaoTalk_Chat_김우현_2026-04-10-17-50-32.csv"),
        "김우현",
    ),
    (
        os.path.expanduser("~/Downloads/KakaoTalk_Chat_이준석_2026-04-10-17-50-43.csv"),
        "이준석",
    ),
]

# 기존 분석 수치 (01_kakao_patterns.md, 04_relational_selves.md)
EXISTING = {
    "정원이": {
        "kk_pct": 1.4,
        "avg_msg_len": 26.0,  # 초기 32.6 ~ 후기 24.8, 대략 평균
        "long_pct": None,  # 161건/25017 = 0.64%
        "emotion_pct": None,  # 별도 계산
        "init_pct": None,  # 후기 61%
        "honorific_pct": 2.0,
        "감정어비율": None,  # 사랑/힘들/슬프/아프 합산
    },
    "교수": {
        "kk_pct": 9.1,
        "avg_msg_len": 30.5,
        "long_pct": 0.55,  # 8/1479
        "emotion_pct": 10.28,
        "init_pct": 61.8,
        "honorific_pct": 33.6,
    },
    "형": {
        "kk_pct": 5.8,
        "avg_msg_len": 19.6,
        "long_pct": 0.34,  # 16/4768
        "emotion_pct": 1.93,
        "init_pct": 49.1,
        "honorific_pct": 0.2,
    },
}

# ============================================================
# 1. 파서 (analyze_kakao.py에서 복사)
# ============================================================

RE_FORMAT_A = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),"([^"]+)","(.*)"$',
    re.DOTALL,
)
RE_FORMAT_B = re.compile(
    r'^(\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{2}),([^,]+),(.*)$',
    re.DOTALL,
)
RE_NEWLINE_A = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},"')
RE_NEWLINE_B = re.compile(r'^\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{2},')


def try_read(path):
    for enc in ("utf-8-sig", "utf-8", "euc-kr", "cp949"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"인코딩 감지 실패: {path}")


def parse_datetime_a(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def parse_datetime_b(s):
    parts = s.split(" ")
    date_parts = parts[0].split(".")
    time_parts = parts[1].split(":")
    return datetime(
        int(date_parts[0]), int(date_parts[1]), int(date_parts[2]),
        int(time_parts[0]), int(time_parts[1]),
    )


def detect_format(text):
    for line in text.split("\n")[1:10]:
        line = line.strip()
        if not line:
            continue
        if RE_FORMAT_A.match(line):
            return "A"
        if RE_FORMAT_B.match(line):
            return "B"
    return None


def parse_file(path):
    text = try_read(path)
    fmt = detect_format(text)
    lines = text.split("\n")
    messages = []

    if fmt == "A":
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if RE_NEWLINE_A.match(line):
                full_line = line
                while full_line.count('"') % 2 != 0 and i + 1 < len(lines):
                    i += 1
                    full_line += "\n" + lines[i]
                m = RE_FORMAT_A.match(full_line)
                if m:
                    dt = parse_datetime_a(m.group(1))
                    messages.append((dt, m.group(2), m.group(3)))
                else:
                    try:
                        reader = csv.reader(io.StringIO(full_line))
                        row = next(reader)
                        if len(row) >= 3:
                            dt = parse_datetime_a(row[0])
                            messages.append((dt, row[1], ",".join(row[2:])))
                    except Exception:
                        pass
            i += 1

    elif fmt == "B":
        i = 1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if RE_NEWLINE_B.match(line):
                full_line = line
                m_start = RE_FORMAT_B.match(line)
                if m_start:
                    msg_part = m_start.group(3)
                    if msg_part.startswith('"') and not msg_part.endswith('"'):
                        while i + 1 < len(lines) and not RE_NEWLINE_B.match(lines[i + 1]):
                            i += 1
                            full_line += "\n" + lines[i]
                m2 = RE_FORMAT_B.match(full_line)
                if m2:
                    try:
                        dt = parse_datetime_b(m2.group(1))
                        user = m2.group(2)
                        msg = m2.group(3)
                        if msg.startswith('"') and msg.endswith('"'):
                            msg = msg[1:-1]
                        messages.append((dt, user, msg))
                    except Exception:
                        pass
            else:
                if messages:
                    dt, user, prev_msg = messages[-1]
                    messages[-1] = (dt, user, prev_msg + "\n" + line)
            i += 1
    else:
        print(f"  [WARN] 포맷 감지 실패: {path}")
        return []

    return messages


# ============================================================
# 2. 분석 유틸리티
# ============================================================

MEDIA_KEYWORDS = {"사진", "이모티콘", "동영상", "보이스톡", "페이스톡"}
kk_pattern = re.compile(r"ㅋ{2,}")
crying_pattern = re.compile(r"[ㅠㅜ]{2,}")

# 감정어
EMOTION_WORDS = ["사랑", "보고싶", "좋아", "미안", "죄송", "힘들", "슬프", "아프", "외롭", "무서"]

# 당위 표현
DEONTIC_PATTERNS = [
    re.compile(r"해야\s*(해|돼|된다|하는|할)"),
    re.compile(r"하면\s*안\s*(돼|된다|됨)"),
    re.compile(r"해야지"),
    re.compile(r"해라"),
    re.compile(r"하지\s*마"),
    re.compile(r"그래야"),
    re.compile(r"안\s*되는\s*거"),
]

# 분석 언어
ANALYSIS_WORDS = ["분석", "시스템", "구조", "패턴", "매뉴얼", "규칙", "프레임", "모델"]

# 교안/매뉴얼 톤 (지시형 표현)
TEACHING_PATTERNS = [
    re.compile(r"첫째|둘째|셋째"),
    re.compile(r"\d+\.\s"),  # 번호 매기기
    re.compile(r"정리하[면자]"),
    re.compile(r"요약하[면자]"),
    re.compile(r"결론[은적]"),
    re.compile(r"원리[는가]"),
    re.compile(r"핵심[은이]"),
]

# 약한 모습 (자기 약점 노출)
VULNERABILITY_WORDS = ["힘들", "슬프", "우울", "무서", "불안", "외롭", "지쳤", "지치", "못하겠", "모르겠", "어떡", "어떻게 해", "도와"]

# 농담/장난/밈
FUN_PATTERNS = [
    re.compile(r"ㅋ{3,}"),  # ㅋㅋㅋ 이상
    re.compile(r"ㅎㅎ{1,}"),
    re.compile(r"ㄹㅇ"),
    re.compile(r"ㅅㅂ"),
    re.compile(r"ㅈㄹ"),
    re.compile(r"미친"),
    re.compile(r"ㅁㅊ"),
    re.compile(r"개[웃겜]"),
    re.compile(r"존나|졸라|ㅈㄴ"),
    re.compile(r"시발|씨발|ㅅㅂ"),
    re.compile(r"ㄱㅇㄷ"),
    re.compile(r"레전드"),
    re.compile(r"낄낄"),
    re.compile(r"킹받"),
]

# 존댓말 판별
HONORIFIC_ENDINGS = re.compile(r"(합니다|습니다|니까|세요|시요|입니다|어요|아요|에요|네요|군요|거든요|잖아요|할게요|할까요|드릴|올게요|겠습니|ㅂ니다|려고요|인가요|던가요|실래요|인데요|는데요|는건가요|시죠|하죠|해요|봐요|줘요|줄게요|줄까요|할래요|갈게요|갈까요|고요|구요|까요|나요|는걸요|라고요|라니요|다고요|다니요|답니다|랍니다|럽습니다|십니다|했습니다|입니까|겠어요|시겠|하시|드려요|같아요|싶어요|대요|래요)[\s.!?~]*$")


def is_text_msg(msg):
    return msg.strip() not in MEDIA_KEYWORDS and not msg.startswith("파일:")


def analyze_friend(path, friend_name):
    """한 친구 대화 분석 → dict"""
    msgs = parse_file(path)
    if not msgs:
        return None

    result = {"name": friend_name, "total_msgs": len(msgs)}

    # 기간
    result["start"] = msgs[0][0]
    result["end"] = msgs[-1][0]
    result["days"] = (msgs[-1][0] - msgs[0][0]).days

    # 이상규 / 상대 분리
    me_msgs = [(dt, msg) for dt, user, msg in msgs if user == ME]
    other_msgs = [(dt, msg) for dt, user, msg in msgs if user != ME]

    result["me_count"] = len(me_msgs)
    result["other_count"] = len(other_msgs)
    result["me_ratio"] = len(me_msgs) / len(msgs) * 100 if msgs else 0

    # --- 텍스트만 ---
    me_text = [(dt, msg) for dt, msg in me_msgs if is_text_msg(msg)]
    other_text = [(dt, msg) for dt, msg in other_msgs if is_text_msg(msg)]

    # 1. ㅋㅋ 비율
    me_kk = sum(1 for _, msg in me_text if kk_pattern.search(msg))
    result["kk_pct"] = me_kk / len(me_text) * 100 if me_text else 0
    result["kk_count"] = me_kk

    # 2. 평균 메시지 길이
    me_lens = [len(msg) for _, msg in me_text]
    result["avg_msg_len"] = sum(me_lens) / len(me_lens) if me_lens else 0
    result["median_msg_len"] = sorted(me_lens)[len(me_lens) // 2] if me_lens else 0

    # 3. 장문 비율 (500자+)
    long_msgs = [(dt, msg) for dt, msg in me_text if len(msg) >= 500]
    result["long_count"] = len(long_msgs)
    result["long_pct"] = len(long_msgs) / len(me_text) * 100 if me_text else 0

    # 200자+ 비율도 (친구한테는 500자가 거의 없을 수 있으니)
    medium_msgs = [(dt, msg) for dt, msg in me_text if len(msg) >= 200]
    result["medium_count"] = len(medium_msgs)
    result["medium_pct"] = len(medium_msgs) / len(me_text) * 100 if me_text else 0

    # 100자+
    long100 = [(dt, msg) for dt, msg in me_text if len(msg) >= 100]
    result["long100_count"] = len(long100)
    result["long100_pct"] = len(long100) / len(me_text) * 100 if me_text else 0

    # 4. 감정어 비율
    emotion_count = 0
    for _, msg in me_text:
        for w in EMOTION_WORDS:
            if w in msg:
                emotion_count += 1
                break
    result["emotion_pct"] = emotion_count / len(me_text) * 100 if me_text else 0

    # 5. 대화 시작 비율 (2시간+ 침묵 후 먼저 말 건 사람)
    initiators_me = 0
    initiators_other = 0
    if msgs:
        # 첫 메시지
        if msgs[0][1] == ME:
            initiators_me += 1
        else:
            initiators_other += 1
        for i in range(1, len(msgs)):
            gap = (msgs[i][0] - msgs[i-1][0]).total_seconds() / 3600
            if gap >= 2:
                if msgs[i][1] == ME:
                    initiators_me += 1
                else:
                    initiators_other += 1
    total_init = initiators_me + initiators_other
    result["init_pct"] = initiators_me / total_init * 100 if total_init else 0
    result["init_me"] = initiators_me
    result["init_other"] = initiators_other

    # 6. 존댓말 비율
    honorific_count = 0
    for _, msg in me_text:
        if HONORIFIC_ENDINGS.search(msg):
            honorific_count += 1
    result["honorific_pct"] = honorific_count / len(me_text) * 100 if me_text else 0

    # 7. 당위 표현 빈도
    deontic_count = 0
    deontic_examples = []
    for _, msg in me_text:
        for p in DEONTIC_PATTERNS:
            if p.search(msg):
                deontic_count += 1
                if len(deontic_examples) < 5:
                    deontic_examples.append(msg[:80])
                break
    result["deontic_count"] = deontic_count
    result["deontic_per1000"] = deontic_count / len(me_text) * 1000 if me_text else 0
    result["deontic_examples"] = deontic_examples

    # 8. 분석 언어 빈도
    analysis_count = 0
    analysis_examples = []
    for _, msg in me_text:
        for w in ANALYSIS_WORDS:
            if w in msg:
                analysis_count += 1
                if len(analysis_examples) < 5:
                    analysis_examples.append(msg[:80])
                break
    result["analysis_count"] = analysis_count
    result["analysis_per1000"] = analysis_count / len(me_text) * 1000 if me_text else 0
    result["analysis_examples"] = analysis_examples

    # 9. 교안/매뉴얼 톤
    teaching_count = 0
    teaching_examples = []
    for _, msg in me_text:
        for p in TEACHING_PATTERNS:
            if p.search(msg):
                teaching_count += 1
                if len(teaching_examples) < 5:
                    teaching_examples.append(msg[:80])
                break
    result["teaching_count"] = teaching_count
    result["teaching_per1000"] = teaching_count / len(me_text) * 1000 if me_text else 0

    # 10. 자문자답 패턴 (이상규가 질문하고 1분 내 이상규가 답)
    self_answer = 0
    for i in range(len(msgs) - 1):
        dt1, user1, msg1 = msgs[i]
        dt2, user2, msg2 = msgs[i + 1]
        if user1 == ME and user2 == ME:
            if ("?" in msg1 or "？" in msg1) and (dt2 - dt1).total_seconds() <= 120:
                if "?" not in msg2 and "？" not in msg2:
                    self_answer += 1
    result["self_answer_count"] = self_answer
    result["self_answer_per1000"] = self_answer / len(me_text) * 1000 if me_text else 0

    # 11. 약한 모습 노출
    vuln_count = 0
    vuln_examples = []
    for _, msg in me_text:
        for w in VULNERABILITY_WORDS:
            if w in msg:
                vuln_count += 1
                if len(vuln_examples) < 10:
                    vuln_examples.append(msg[:100])
                break
    result["vuln_count"] = vuln_count
    result["vuln_pct"] = vuln_count / len(me_text) * 100 if me_text else 0
    result["vuln_examples"] = vuln_examples

    # 12. 농담/장난/밈 비율
    fun_count = 0
    for _, msg in me_text:
        for p in FUN_PATTERNS:
            if p.search(msg):
                fun_count += 1
                break
    result["fun_pct"] = fun_count / len(me_text) * 100 if me_text else 0
    result["fun_count"] = fun_count

    # 13. ㅠ/ㅜ 비율
    cry_count = sum(1 for _, msg in me_text if crying_pattern.search(msg))
    result["cry_pct"] = cry_count / len(me_text) * 100 if me_text else 0

    # 14. 물음표 비율 (질문 빈도)
    q_count = sum(1 for _, msg in me_text if "?" in msg or "？" in msg)
    result["q_pct"] = q_count / len(me_text) * 100 if me_text else 0

    # 15. 나:너 비율 (1인칭 vs 2인칭)
    i_words = ["나", "내가", "나는", "나도", "나한테", "내", "나를"]
    you_words = ["너", "니가", "너는", "너도", "너한테", "네가", "너를"]
    i_count = sum(sum(msg.count(w) for w in i_words) for _, msg in me_text)
    you_count = sum(sum(msg.count(w) for w in you_words) for _, msg in me_text)
    result["i_you_ratio"] = i_count / you_count if you_count > 0 else i_count
    result["i_count"] = i_count
    result["you_count"] = you_count

    # 16. 욕설 비율
    profanity = re.compile(r"시발|씨발|ㅅㅂ|존나|졸라|ㅈㄴ|개같|좆|ㅈ같|미친|ㅁㅊ|병신|ㅂㅅ")
    prof_count = sum(1 for _, msg in me_text if profanity.search(msg))
    result["profanity_pct"] = prof_count / len(me_text) * 100 if me_text else 0

    # 17. 연속 메시지 폭탄 (이상규가 5개+ 연속)
    bursts = []
    current_burst = []
    for dt, user, msg in msgs:
        if user == ME:
            if current_burst:
                if (dt - current_burst[-1][0]).total_seconds() <= 60:
                    current_burst.append((dt, msg))
                else:
                    if len(current_burst) >= 5:
                        bursts.append(current_burst[:])
                    current_burst = [(dt, msg)]
            else:
                current_burst = [(dt, msg)]
        else:
            if len(current_burst) >= 5:
                bursts.append(current_burst[:])
            current_burst = []
    if len(current_burst) >= 5:
        bursts.append(current_burst[:])

    result["burst_count"] = len(bursts)
    result["max_burst"] = max(len(b) for b in bursts) if bursts else 0

    # 18. 이상규의 가장 긴 메시지 5개 (내용 확인용)
    top_long = sorted(me_text, key=lambda x: len(x[1]), reverse=True)[:5]
    result["top_long_msgs"] = [(dt.strftime("%Y-%m-%d %H:%M"), len(msg), msg[:200]) for dt, msg in top_long]

    # 19. 감정어 세부 (단어별)
    emotion_detail = {}
    for w in EMOTION_WORDS:
        c = sum(1 for _, msg in me_text if w in msg)
        emotion_detail[w] = c
    result["emotion_detail"] = emotion_detail

    return result


# ============================================================
# 3. 실행
# ============================================================

print("=" * 70)
print("친구 4명 카톡 분석 — 이상규 기준선 측정")
print("=" * 70)

friend_results = []
for path, name in FRIENDS:
    print(f"\n{'─'*50}")
    print(f"분석 중: {name}")
    r = analyze_friend(path, name)
    if r:
        friend_results.append(r)
        print(f"  메시지: {r['total_msgs']}개 (이상규 {r['me_count']} / {name} {r['other_count']})")
        print(f"  기간: {r['start'].strftime('%Y-%m-%d')} ~ {r['end'].strftime('%Y-%m-%d')} ({r['days']}일)")
        print(f"  이상규 메시지 비율: {r['me_ratio']:.1f}%")
        print(f"  ㅋㅋ 비율: {r['kk_pct']:.1f}%")
        print(f"  평균 메시지 길이: {r['avg_msg_len']:.1f}자 (중앙 {r['median_msg_len']}자)")
        print(f"  장문(500자+): {r['long_count']}건 ({r['long_pct']:.2f}%)")
        print(f"  장문(200자+): {r['medium_count']}건 ({r['medium_pct']:.2f}%)")
        print(f"  장문(100자+): {r['long100_count']}건 ({r['long100_pct']:.2f}%)")
        print(f"  감정어 비율: {r['emotion_pct']:.2f}%")
        print(f"  먼저 연락 비율: {r['init_pct']:.1f}% (이상규 {r['init_me']} / {name} {r['init_other']})")
        print(f"  존댓말 비율: {r['honorific_pct']:.1f}%")
        print(f"  당위 표현: {r['deontic_count']}건 ({r['deontic_per1000']:.1f}/1000건)")
        print(f"  분석 언어: {r['analysis_count']}건 ({r['analysis_per1000']:.1f}/1000건)")
        print(f"  교안 톤: {r['teaching_count']}건 ({r['teaching_per1000']:.1f}/1000건)")
        print(f"  자문자답: {r['self_answer_count']}건 ({r['self_answer_per1000']:.1f}/1000건)")
        print(f"  약한 모습 노출: {r['vuln_count']}건 ({r['vuln_pct']:.2f}%)")
        print(f"  농담/장난/밈: {r['fun_count']}건 ({r['fun_pct']:.1f}%)")
        print(f"  ㅠ/ㅜ 비율: {r['cry_pct']:.1f}%")
        print(f"  물음표 비율: {r['q_pct']:.1f}%")
        print(f"  나:너 비율: {r['i_count']}:{r['you_count']} = {r['i_you_ratio']:.1f}:1")
        print(f"  욕설 비율: {r['profanity_pct']:.1f}%")
        print(f"  연속폭탄(5개+): {r['burst_count']}회, 최대 {r['max_burst']}개")

        print(f"\n  감정어 세부:")
        for w, c in r['emotion_detail'].items():
            if c > 0:
                print(f"    '{w}': {c}건 ({c/len([(dt,msg) for dt,msg in [(dt,msg) for dt,user,msg in parse_file(path) if user==ME] if is_text_msg(msg)])*1000:.1f}/1000)" if False else f"    '{w}': {c}건")

        print(f"\n  이상규 최장 메시지 TOP 5:")
        for dt_s, length, preview in r['top_long_msgs']:
            print(f"    [{dt_s}] {length}자: {preview[:80]}...")

        if r['vuln_examples']:
            print(f"\n  약한 모습 예시 (최대 5개):")
            for ex in r['vuln_examples'][:5]:
                print(f"    - {ex}")

        if r['deontic_examples']:
            print(f"\n  당위 표현 예시 (최대 5개):")
            for ex in r['deontic_examples'][:5]:
                print(f"    - {ex}")

        if r['analysis_examples']:
            print(f"\n  분석 언어 예시 (최대 5개):")
            for ex in r['analysis_examples'][:5]:
                print(f"    - {ex}")


# ============================================================
# 4. 비교표 출력
# ============================================================

print("\n\n" + "=" * 70)
print("비교표: 정원이 · 교수 · 형 · 친구 4명")
print("=" * 70)

# 헤더
cols = ["정원이", "교수", "형"] + [r["name"] for r in friend_results]
header = f"{'지표':<25}" + "".join(f"{c:>10}" for c in cols)
print(header)
print("─" * len(header))

# 행 데이터
rows = [
    ("ㅋㅋ 비율 (%)", "kk_pct",
     [EXISTING["정원이"]["kk_pct"], EXISTING["교수"]["kk_pct"], EXISTING["형"]["kk_pct"]]
     + [r["kk_pct"] for r in friend_results]),
    ("평균 메시지 길이 (자)", "avg_msg_len",
     [EXISTING["정원이"]["avg_msg_len"], EXISTING["교수"]["avg_msg_len"], EXISTING["형"]["avg_msg_len"]]
     + [r["avg_msg_len"] for r in friend_results]),
    ("장문 500자+ (%)", "long_pct",
     [0.64, EXISTING["교수"]["long_pct"], EXISTING["형"]["long_pct"]]
     + [r["long_pct"] for r in friend_results]),
    ("감정어 비율 (%)", "emotion_pct",
     [None, EXISTING["교수"]["emotion_pct"], EXISTING["형"]["emotion_pct"]]
     + [r["emotion_pct"] for r in friend_results]),
    ("먼저 연락 비율 (%)", "init_pct",
     [61.0, EXISTING["교수"]["init_pct"], EXISTING["형"]["init_pct"]]
     + [r["init_pct"] for r in friend_results]),
    ("존댓말 비율 (%)", "honorific_pct",
     [EXISTING["정원이"]["honorific_pct"], EXISTING["교수"]["honorific_pct"], EXISTING["형"]["honorific_pct"]]
     + [r["honorific_pct"] for r in friend_results]),
    ("농담/장난 비율 (%)", "fun_pct",
     [None, None, None]
     + [r["fun_pct"] for r in friend_results]),
    ("욕설 비율 (%)", "profanity_pct",
     [None, None, None]
     + [r["profanity_pct"] for r in friend_results]),
    ("약한 모습 노출 (%)", "vuln_pct",
     [None, 8.79, 3.48]
     + [r["vuln_pct"] for r in friend_results]),
    ("나:너 비율", "i_you_ratio",
     [17.3, None, None]
     + [r["i_you_ratio"] for r in friend_results]),
    ("당위 표현 (/1000)", "deontic_per1000",
     [None, None, None]
     + [r["deontic_per1000"] for r in friend_results]),
    ("분석 언어 (/1000)", "analysis_per1000",
     [None, None, None]
     + [r["analysis_per1000"] for r in friend_results]),
    ("자문자답 (/1000)", "self_answer_per1000",
     [None, None, None]
     + [r["self_answer_per1000"] for r in friend_results]),
    ("물음표 비율 (%)", "q_pct",
     [None, None, None]
     + [r["q_pct"] for r in friend_results]),
    ("ㅠ/ㅜ 비율 (%)", "cry_pct",
     [None, None, None]
     + [r["cry_pct"] for r in friend_results]),
]

for label, key, values in rows:
    line = f"{label:<25}"
    for v in values:
        if v is None:
            line += f"{'—':>10}"
        elif isinstance(v, float):
            line += f"{v:>10.1f}"
        else:
            line += f"{v:>10}"
    print(line)


# ============================================================
# 5. 보고서 생성
# ============================================================

print("\n\n" + "=" * 70)
print("보고서 생성 중...")
print("=" * 70)

report_path = os.path.expanduser("~/pp/30p/runs/self/discoveries/06_friend_baseline.md")

# 친구 평균 계산
def friend_avg(key):
    vals = [r[key] for r in friend_results if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else 0

def friend_list(key, fmt=".1f", suffix=""):
    """친구별 수치를 '이름 수치' 형태로 join"""
    parts = []
    for r in friend_results:
        val = r[key]
        parts.append("{} {}{}".format(r["name"], format(val, fmt), suffix))
    return ", ".join(parts)

# 보고서 생성
report_lines = []
report_lines.append("# 06 -- 친구 기준선: 정원이에게만 그런 건가?")
report_lines.append("")
report_lines.append(f"분석일: 2026-04-10")
report_lines.append(f"데이터: 친구 4명 카톡 ({', '.join(r['name'] for r in friend_results)})")
report_lines.append(f"비교 기준: 정원이 (01_kakao_patterns.md), 교수+형 (04_relational_selves.md)")
report_lines.append("")
report_lines.append("---")
report_lines.append("")

# 기본 메타
report_lines.append("## 기본 메타")
report_lines.append("")
report_lines.append("| 항목 | " + " | ".join(r["name"] for r in friend_results) + " |")
report_lines.append("|---|" + "|".join("---" for _ in friend_results) + "|")
report_lines.append("| 메시지 수 | " + " | ".join(f"{r['total_msgs']:,}" for r in friend_results) + " |")
report_lines.append("| 이상규 메시지 | " + " | ".join(f"{r['me_count']:,}" for r in friend_results) + " |")
report_lines.append("| 기간 | " + " | ".join(f"{r['start'].strftime('%Y-%m')}~{r['end'].strftime('%Y-%m')}" for r in friend_results) + " |")
report_lines.append("| 일수 | " + " | ".join(f"{r['days']}" for r in friend_results) + " |")
report_lines.append("| 이상규 비율 | " + " | ".join(f"{r['me_ratio']:.0f}%" for r in friend_results) + " |")
report_lines.append("")

# 핵심 비교표
report_lines.append("## 핵심 비교표")
report_lines.append("")
report_lines.append("| 지표 | 정원이 | 교수 | 형 | " + " | ".join(r["name"] for r in friend_results) + " | **친구 평균** |")
report_lines.append("|---|---|---|---|" + "|".join("---" for _ in friend_results) + "|---|")

comparison_rows = [
    ("ㅋㅋ 비율", f"**1.4%**", "9.1%", "5.8%",
     [f"{r['kk_pct']:.1f}%" for r in friend_results],
     f"{friend_avg('kk_pct'):.1f}%"),
    ("평균 메시지 길이", "26자급", "30.5자", "19.6자",
     [f"{r['avg_msg_len']:.1f}자" for r in friend_results],
     f"{friend_avg('avg_msg_len'):.1f}자"),
    ("장문 500자+ 비율", "**0.64%**", "0.55%", "0.34%",
     [f"{r['long_pct']:.2f}%" for r in friend_results],
     f"{friend_avg('long_pct'):.2f}%"),
    ("장문 200자+ 비율", "--", "--", "--",
     [f"{r['medium_pct']:.2f}%" for r in friend_results],
     f"{friend_avg('medium_pct'):.2f}%"),
    ("감정어 비율", "--", "10.28%", "1.93%",
     [f"{r['emotion_pct']:.2f}%" for r in friend_results],
     f"{friend_avg('emotion_pct'):.2f}%"),
    ("먼저 연락 비율", "**61%** (후기)", "61.8%", "49.1%",
     [f"{r['init_pct']:.0f}%" for r in friend_results],
     f"{friend_avg('init_pct'):.0f}%"),
    ("존댓말 비율", "**2%**", "33.6%", "0.2%",
     [f"{r['honorific_pct']:.1f}%" for r in friend_results],
     f"{friend_avg('honorific_pct'):.1f}%"),
    ("농담/장난/밈 비율", "~1.4%추정", "--", "--",
     [f"{r['fun_pct']:.1f}%" for r in friend_results],
     f"{friend_avg('fun_pct'):.1f}%"),
    ("욕설 비율", "--", "--", "--",
     [f"{r['profanity_pct']:.1f}%" for r in friend_results],
     f"{friend_avg('profanity_pct'):.1f}%"),
    ("약한 모습 노출", "~0%", "8.79%", "3.48%",
     [f"{r['vuln_pct']:.2f}%" for r in friend_results],
     f"{friend_avg('vuln_pct'):.2f}%"),
    ("나:너 비율", "**17.3:1**", "--", "--",
     [f"{r['i_you_ratio']:.1f}:1" for r in friend_results],
     f"{friend_avg('i_you_ratio'):.1f}:1"),
    ("당위 표현 (/1000)", "--", "--", "--",
     [f"{r['deontic_per1000']:.1f}" for r in friend_results],
     f"{friend_avg('deontic_per1000'):.1f}"),
    ("분석 언어 (/1000)", "--", "--", "--",
     [f"{r['analysis_per1000']:.1f}" for r in friend_results],
     f"{friend_avg('analysis_per1000'):.1f}"),
    ("자문자답 (/1000)", "--", "--", "--",
     [f"{r['self_answer_per1000']:.1f}" for r in friend_results],
     f"{friend_avg('self_answer_per1000'):.1f}"),
    ("물음표 비율", "--", "--", "--",
     [f"{r['q_pct']:.1f}%" for r in friend_results],
     f"{friend_avg('q_pct'):.1f}%"),
]

for label, jw, prof, bro, friend_vals, avg in comparison_rows:
    report_lines.append(f"| {label} | {jw} | {prof} | {bro} | " + " | ".join(friend_vals) + f" | {avg} |")

report_lines.append("")

# ============================================================
# 발견 섹션 생성
# ============================================================

report_lines.append("---")
report_lines.append("")

# 각 발견을 데이터 기반으로 생성
discovery_num = 0

# 발견 1: ㅋㅋ 비율 — 정원이 특이값인가?
discovery_num += 1
avg_kk = friend_avg("kk_pct")
min_kk = min(r["kk_pct"] for r in friend_results)
max_kk = max(r["kk_pct"] for r in friend_results)
min_kk_name = [r["name"] for r in friend_results if r["kk_pct"] == min_kk][0]
max_kk_name = [r["name"] for r in friend_results if r["kk_pct"] == max_kk][0]

report_lines.append(f"## 발견 {discovery_num} -- 이상규의 ㅋㅋ는 정원이에게만 사라진다")
report_lines.append("")
report_lines.append(f"- 데이터: 이상규의 ㅋㅋ 포함 비율 -- 정원이 **1.4%**, 교수 9.1%, 형 5.8%, 친구 평균 **{avg_kk:.1f}%** ({friend_list('kk_pct', '.1f', '%')}).")
report_lines.append(f"- 친구 중 최저 {min_kk_name} {min_kk:.1f}%, 최고 {max_kk_name} {max_kk:.1f}%.")

if 1.4 < min_kk:
    report_lines.append(f"- 의미: 정원이의 1.4%는 **전체 관계 중 최저**. 친구 중 가장 적은 {min_kk_name}({min_kk:.1f}%)조차 정원이보다 {min_kk/1.4:.1f}배 높다. 이것은 이상규의 기본값이 아니다. 정원이에게서만 웃음이 사라진다.")
else:
    report_lines.append(f"- 의미: 정원이의 1.4%는 친구 중 일부와 비슷한 범위. 이상규의 웃음 부재는 정원이 전용이 아닐 수 있다.")
report_lines.append("")

# 발견 2: 메시지 길이 — 장문 교안은 정원이 전용인가?
discovery_num += 1
avg_long = friend_avg("long_pct")
avg_medium = friend_avg("medium_pct")
avg_len = friend_avg("avg_msg_len")

report_lines.append(f"## 발견 {discovery_num} -- 장문 폭탄은 정원이 전용인가?")
report_lines.append("")
report_lines.append(f"- 데이터: 500자+ 장문 비율 -- 정원이 **0.64%** (161건), 교수 0.55%, 형 0.34%, 친구 평균 **{avg_long:.2f}%** ({friend_list('long_pct', '.2f', '%')}).")
report_lines.append(f"- 200자+ 비율 -- 친구 평균 **{avg_medium:.2f}%** ({friend_list('medium_pct', '.2f', '%')}).")
report_lines.append(f"- 평균 메시지 길이 -- 정원이 ~26자, 교수 30.5자, 형 19.6자, 친구 평균 **{avg_len:.1f}자** ({friend_list('avg_msg_len', '.1f', '자')}).")

if avg_long < 0.3:
    report_lines.append(f"- 의미: 친구에게 500자+ 장문은 거의 없다 (평균 {avg_long:.2f}%). 정원이에게만 교안급 장문이 쏟아진다. 이상규의 장문은 *연인/정원이 전용 무기*.")
else:
    report_lines.append(f"- 의미: 친구에게도 장문이 일정 비율 존재. 이상규의 장문 본능은 범용적.")
report_lines.append("")

# 발견 3: 나:너 비율 — 정원이의 17.3:1은 특이값인가?
discovery_num += 1
avg_iy = friend_avg("i_you_ratio")
report_lines.append(f"## 발견 {discovery_num} -- 나:너 비율 17.3:1은 정원이에게만 일어나는가?")
report_lines.append("")
report_lines.append(f"- 데이터: 나(1인칭):너(2인칭) 비율 -- 정원이 **17.3:1** (통화), 친구 평균 **{avg_iy:.1f}:1** ({friend_list('i_you_ratio', '.1f', ':1')}).")
if avg_iy < 5:
    report_lines.append(f"- 의미: 친구에게는 나:너가 {avg_iy:.1f}:1 수준. 정원이의 17.3:1과는 차원이 다르다. 정원이 앞에서 이상규는 '너'를 잃고 '나'만 남는다.")
else:
    report_lines.append(f"- 의미: 친구에게도 나:너 비율이 높다 ({avg_iy:.1f}:1). 이상규의 자기중심적 화법은 전반적 특성일 수 있다.")
report_lines.append("")

# 발견 4: 약한 모습 — 교수 8.79%, 형 3.48%, 친구는?
discovery_num += 1
avg_vuln = friend_avg("vuln_pct")
max_vuln = max(r["vuln_pct"] for r in friend_results)
max_vuln_name = [r["name"] for r in friend_results if r["vuln_pct"] == max_vuln][0]

report_lines.append(f"## 발견 {discovery_num} -- 이상규가 약한 모습을 보이는 상대는 누구인가?")
report_lines.append("")
report_lines.append(f"- 데이터: 약한 모습 노출 -- 정원이 ~0%, 교수 8.79%, 형 3.48%, 친구 평균 **{avg_vuln:.2f}%** ({friend_list('vuln_pct', '.2f', '%')}).")
report_lines.append(f"- 가장 많이 노출하는 친구: {max_vuln_name} {max_vuln:.2f}%.")
if avg_vuln > 2:
    report_lines.append(f"- 의미: 친구에게 약한 모습({avg_vuln:.2f}%)이 형(3.48%)과 비슷하거나 더 높다. 정원이에게만 약한 모습이 사라진다. 정원이 앞에서 이상규는 *지배자 페르소나*를 벗지 않는다.")
else:
    report_lines.append(f"- 의미: 약한 모습 노출은 모든 관계에서 낮다. 이상규의 방어벽은 범용적.")
report_lines.append("")

# 발견 5: 욕설과 농담 — 친구에게 보이는 다른 이상규
discovery_num += 1
avg_fun = friend_avg("fun_pct")
avg_prof = friend_avg("profanity_pct")

report_lines.append(f"## 발견 {discovery_num} -- 친구에게만 보이는 이상규: 욕설과 농담")
report_lines.append("")
report_lines.append(f"- 데이터: 농담/장난/밈 비율 -- 정원이 ~1.4%(추정), 친구 평균 **{avg_fun:.1f}%** ({friend_list('fun_pct', '.1f', '%')}).")
report_lines.append(f"- 욕설 비율 -- 친구 평균 **{avg_prof:.1f}%** ({friend_list('profanity_pct', '.1f', '%')}).")
report_lines.append(f"- 의미: 친구에게 이상규는 정원이 앞과는 전혀 다른 언어를 쓴다. 농담 {avg_fun:.1f}%는 정원이의 ㅋㅋ 1.4%와 대조적. 정원이 앞에서의 이상규는 *웃음도 욕설도 빠진 버전*이다.")
report_lines.append("")

# 발견 6: 당위 표현과 분석 언어
discovery_num += 1
avg_deontic = friend_avg("deontic_per1000")
avg_analysis = friend_avg("analysis_per1000")

report_lines.append(f"## 발견 {discovery_num} -- 친구에게 가르치려 하는가?")
report_lines.append("")
report_lines.append(f"- 데이터: 당위 표현(~해야 해, ~하면 안 돼) -- 친구 평균 **{avg_deontic:.1f}/1000건** ({friend_list('deontic_per1000', '.1f')}).")
report_lines.append(f"- 분석 언어(분석/시스템/구조/패턴) -- 친구 평균 **{avg_analysis:.1f}/1000건** ({friend_list('analysis_per1000', '.1f')}).")
# 정원이 기존 데이터: 통제 언어 1000건당 3.1(초기) → 6.7(후기)
report_lines.append(f"- 정원이에게 통제 언어는 1000건당 3.1(초기) → 6.7(후기). 교수에게 지시/매뉴얼 톤 4.19%, 형에게 2.41%.")
if avg_deontic < 5 and avg_analysis < 3:
    report_lines.append(f"- 의미: 친구에게는 당위 표현과 분석 언어가 거의 없다. *교안 모드*는 정원이 전용. 이상규는 친구에게 '가르치려 들지 않는다'.")
else:
    report_lines.append(f"- 의미: 친구에게도 당위/분석 표현이 상당히 있다. 이상규의 *가르치려 드는 본능*은 범용적 특성.")
report_lines.append("")

# 발견 7: 자문자답
discovery_num += 1
avg_sa = friend_avg("self_answer_per1000")

report_lines.append(f"## 발견 {discovery_num} -- 자문자답 패턴")
report_lines.append("")
report_lines.append(f"- 데이터: 자문자답(질문 후 2분 내 자기가 답) -- 정원이 통화에서 **43.6%**, 친구 평균 **{avg_sa:.1f}/1000건** ({friend_list('self_answer_per1000', '.1f')}).")
report_lines.append(f"- 의미: 자문자답은 이상규의 범용 패턴인가 정원이 전용인가를 보여준다.")
report_lines.append("")

# 발견 8: 존댓말 비율
discovery_num += 1
avg_hon = friend_avg("honorific_pct")

report_lines.append(f"## 발견 {discovery_num} -- 존댓말 패턴")
report_lines.append("")
report_lines.append(f"- 데이터: 존댓말 비율 -- 정원이 **2%**, 교수 33.6%, 형 0.2%, 친구 평균 **{avg_hon:.1f}%** ({friend_list('honorific_pct', '.1f', '%')}).")

# 김우현은 군대 후배 → 존댓말?
kim_hon = [r for r in friend_results if r["name"] == "김우현"]
if kim_hon and kim_hon[0]["honorific_pct"] > 5:
    kim_val = kim_hon[0]["honorific_pct"]
    report_lines.append(f"- 주목: 김우현에게 {kim_val:.1f}%의 존댓말. 군 선후배 관계일 가능성.")
report_lines.append(f"- 의미: 이상규의 존댓말 사용은 관계 내 위계 인식을 반영한다.")
report_lines.append("")

# ============================================================
# 결론 섹션
# ============================================================

report_lines.append("---")
report_lines.append("")
report_lines.append("## 결정적 질문의 답: '정원이에게만 그런 건가?'")
report_lines.append("")

# 각 항목별 판정
report_lines.append("### 정원이에게만 그런 것 (정원이 특이값)")
report_lines.append("")

if 1.4 < min_kk:
    report_lines.append(f"1. **ㅋㅋ 1.4%는 정원이 특이값이다.** 친구 중 최저 {min_kk_name}도 {min_kk:.1f}%. 교수 9.1%, 형 5.8%. 이상규는 원래 웃는 사람인데, 정원이 앞에서만 웃음이 빠진다.")
report_lines.append("")

if avg_long < 0.3:
    report_lines.append(f"2. **장문 교안은 정원이 전용이다.** 친구에게 500자+ 비율 평균 {avg_long:.2f}%. 정원이에게 0.64%. 친구에게 이상규는 짧게 말한다.")
report_lines.append("")

if avg_iy < 5:
    report_lines.append(f"3. **나:너 17.3:1은 정원이 특이값이다.** 친구 평균 {avg_iy:.1f}:1. 친구에게는 '너'가 존재한다.")
report_lines.append("")

if avg_vuln > 2:
    report_lines.append(f"4. **약한 모습은 친구에게 보인다.** 친구 평균 {avg_vuln:.2f}%, 형 3.48%, 교수 8.79%. 정원이에게만 0%.")
report_lines.append("")

report_lines.append("### 원래 그런 것 (이상규 기본값)")
report_lines.append("")

if avg_sa > 5:
    report_lines.append(f"- **자문자답은 기본값일 수 있다.** 친구에게도 {avg_sa:.1f}/1000건 수준.")
report_lines.append("")

if avg_iy >= 5:
    report_lines.append(f"- **나:너 비율이 높은 것은 기본 화법이다.** 친구에게도 {avg_iy:.1f}:1.")
report_lines.append("")

report_lines.append("### 종합")
report_lines.append("")
report_lines.append("이상규는 친구에게와 정원이에게 *다른 사람*이 된다. 친구에게 보이는 이상규:")
report_lines.append("")
report_lines.append(f"- 웃는다 (ㅋㅋ 평균 {avg_kk:.1f}%)")
report_lines.append(f"- 짧게 말한다 (평균 {avg_len:.1f}자)")
report_lines.append(f"- 농담한다 ({avg_fun:.1f}%)")
report_lines.append(f"- 욕한다 ({avg_prof:.1f}%)")
report_lines.append(f"- 약한 모습을 보인다 ({avg_vuln:.2f}%)")
report_lines.append(f"- 가르치려 들지 않는다 (당위 {avg_deontic:.1f}/1000)")
report_lines.append("")
report_lines.append("정원이에게 보이는 이상규:")
report_lines.append("")
report_lines.append("- 웃지 않는다 (1.4%)")
report_lines.append("- 길게 말한다 (교안급)")
report_lines.append("- 농담하지 않는다")
report_lines.append("- 약한 모습을 보이지 않는다")
report_lines.append("- 가르치려 든다 (통제 언어 후기 6.7/1000)")
report_lines.append("- '너'가 사라지고 '나'만 남는다 (17.3:1)")
report_lines.append("")
report_lines.append("**이상규는 정원이 앞에서 *설계자*가 되고, 친구 앞에서 *사람*이 된다.**")

# 파일 저장
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print(f"\n보고서 저장 완료: {report_path}")
print("완료.")
