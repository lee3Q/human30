#!/usr/bin/env python3
"""
범용 카카오톡 대화 통계 분석기
stdlib만 사용. python3 analyze.py <csv_path> [--me <이름>]

출력: JSON (stdout) — LLM 해석 프롬프트에 그대로 먹일 수 있는 구조
"""

import csv
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta


# ============================================================
# 파서 — 카톡 CSV 두 가지 포맷 자동 감지
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


def try_decode(data):
    """바이트 데이터를 문자열로 디코딩 (파일 없이 메모리에서)"""
    if isinstance(data, str):
        return data
    for enc in ("utf-8-sig", "utf-8", "euc-kr", "cp949"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError("인코딩 감지 실패")


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


def parse_text(text):
    """텍스트에서 직접 파싱 (파일 저장 없이 메모리에서 처리)"""
    fmt = detect_format(text)
    return _parse_lines(text, fmt)


def parse_file(path):
    """카톡 CSV 파싱 → [(datetime, user, message), ...]"""
    text = try_read(path)
    fmt = detect_format(text)
    return _parse_lines(text, fmt)


def _parse_lines(text, fmt):
    """내부 파싱 로직"""
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
        raise RuntimeError(f"CSV 포맷 감지 실패: {path}")

    return messages


# ============================================================
# 사용자 감지
# ============================================================

def detect_users(messages):
    """메시지 빈도로 사용자 이름들 추출. {name: count}"""
    counts = Counter(user for _, user, _ in messages)
    return counts


def guess_me(user_counts):
    """가장 많이 말한 사람을 '나'로 추정"""
    return user_counts.most_common(1)[0][0]


# ============================================================
# 유틸
# ============================================================

MEDIA_KEYWORDS = {"사진", "이모티콘", "동영상", "보이스톡", "페이스톡"}


def is_media(msg):
    return msg.strip() in MEDIA_KEYWORDS or msg.startswith("파일:")


def week_key(dt):
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def month_key(dt):
    return dt.strftime("%Y-%m")


def period_label(dt, start, end):
    total = (end - start).days
    if total == 0:
        return "전체"
    third = total / 3
    elapsed = (dt - start).days
    if elapsed < third:
        return "초기"
    elif elapsed < third * 2:
        return "중기"
    return "후기"


def split_by_user(msgs, me_name):
    me = [(dt, msg) for dt, user, msg in msgs if user == me_name]
    other = [(dt, msg) for dt, user, msg in msgs if user != me_name]
    return me, other


def safe_div(a, b, default=0):
    return a / b if b else default


# ============================================================
# 분석 함수들
# ============================================================

def analyze_frequency(msgs, me_name, start, end):
    """메시지 빈도 + 급변 지점"""
    daily_me = defaultdict(int)
    daily_other = defaultdict(int)
    for dt, user, msg in msgs:
        d = dt.strftime("%Y-%m-%d")
        if user == me_name:
            daily_me[d] += 1
        else:
            daily_other[d] += 1

    all_dates = sorted(set(list(daily_me.keys()) + list(daily_other.keys())))

    # 주간 집계
    weekly_me = defaultdict(int)
    weekly_other = defaultdict(int)
    for d in all_dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        wk = week_key(dt)
        weekly_me[wk] += daily_me[d]
        weekly_other[wk] += daily_other[d]

    # 급변 지점
    def find_spikes(daily, window=7, threshold=2.0):
        dates = sorted(daily.keys())
        spikes = []
        for i, d in enumerate(dates):
            s = max(0, i - window)
            window_vals = [daily[dates[j]] for j in range(s, i)] or [1]
            avg = sum(window_vals) / len(window_vals)
            count = daily[d]
            if avg > 0 and count >= avg * threshold and count >= 10:
                spikes.append({"date": d, "count": count, "avg": round(avg, 1), "ratio": round(count / avg, 1)})
        return sorted(spikes, key=lambda x: -x["ratio"])[:5]

    # 월별 메시지 수
    monthly_me = defaultdict(int)
    monthly_other = defaultdict(int)
    for dt, user, msg in msgs:
        m = month_key(dt)
        if user == me_name:
            monthly_me[m] += 1
        else:
            monthly_other[m] += 1

    return {
        "total_days": len(all_dates),
        "daily_me_avg": round(sum(daily_me.values()) / max(len(all_dates), 1), 1),
        "daily_other_avg": round(sum(daily_other.values()) / max(len(all_dates), 1), 1),
        "spikes_me": find_spikes(daily_me),
        "spikes_other": find_spikes(daily_other),
        "monthly_me": dict(sorted(monthly_me.items())),
        "monthly_other": dict(sorted(monthly_other.items())),
    }


def analyze_response_time(msgs, me_name, start, end):
    """응답 시간 비대칭"""
    if len(msgs) < 2:
        return {}

    me_to_other = defaultdict(list)  # 내가 말한 뒤 상대 응답까지
    other_to_me = defaultdict(list)  # 상대가 말한 뒤 내 응답까지

    prev_user = msgs[0][1]
    prev_time = msgs[0][0]

    for i in range(1, len(msgs)):
        dt, user, msg = msgs[i]
        if user != prev_user:
            gap = (dt - prev_time).total_seconds()
            if 1 <= gap <= 21600:
                p = period_label(dt, start, end)
                if prev_user == me_name:
                    me_to_other[p].append(gap)
                else:
                    other_to_me[p].append(gap)
        prev_user = user
        prev_time = dt

    result = {}
    for label in ["초기", "중기", "후기"]:
        m2o = me_to_other.get(label, [])
        o2m = other_to_me.get(label, [])
        if m2o and o2m:
            result[label] = {
                "me_to_other_avg": round(sum(m2o) / len(m2o)),
                "me_to_other_median": round(sorted(m2o)[len(m2o) // 2]),
                "other_to_me_avg": round(sum(o2m) / len(o2m)),
                "other_to_me_median": round(sorted(o2m)[len(o2m) // 2]),
            }
    return result


def analyze_message_length(msgs_me, msgs_other, start, end):
    """메시지 길이 분석"""
    def stats_by_period(msgs):
        by_period = defaultdict(list)
        by_month = defaultdict(list)
        for dt, msg in msgs:
            if not is_media(msg):
                by_period[period_label(dt, start, end)].append(len(msg))
                by_month[month_key(dt)].append(len(msg))
        result = {}
        for label in ["초기", "중기", "후기"]:
            vals = by_period.get(label, [])
            if vals:
                result[label] = {
                    "avg": round(sum(vals) / len(vals), 1),
                    "median": sorted(vals)[len(vals) // 2],
                    "count": len(vals),
                }
        monthly = {}
        for m in sorted(by_month.keys()):
            vals = by_month[m]
            monthly[m] = round(sum(vals) / len(vals), 1)
        return result, monthly

    me_period, me_monthly = stats_by_period(msgs_me)
    other_period, other_monthly = stats_by_period(msgs_other)

    # 장문 (500자+)
    long_me = [(dt, msg) for dt, msg in msgs_me if len(msg) >= 500 and not is_media(msg)]
    long_other = [(dt, msg) for dt, msg in msgs_other if len(msg) >= 500 and not is_media(msg)]

    long_me_hours = Counter(dt.hour for dt, _ in long_me)
    dawn_long_me = sum(1 for dt, _ in long_me if 0 <= dt.hour < 6)

    return {
        "me_by_period": me_period,
        "other_by_period": other_period,
        "me_monthly_avg": me_monthly,
        "other_monthly_avg": other_monthly,
        "long_me_count": len(long_me),
        "long_other_count": len(long_other),
        "long_me_dawn_pct": round(safe_div(dawn_long_me, len(long_me)) * 100, 1),
        "long_me_top_hours": [{"hour": h, "count": c} for h, c in long_me_hours.most_common(3)],
    }


def analyze_kk(msgs_me, msgs_other, start, end):
    """ㅋㅋ 빈도"""
    kk_pat = re.compile(r"ㅋ{2,}")

    def count_kk(msgs):
        by_period = defaultdict(int)
        by_month = defaultdict(int)
        msg_by_month = defaultdict(int)
        total = 0
        for dt, msg in msgs:
            found = len(kk_pat.findall(msg))
            total += found
            by_period[period_label(dt, start, end)] += found
            by_month[month_key(dt)] += found
            msg_by_month[month_key(dt)] += 1

        monthly_rate = {}
        for m in sorted(by_month.keys()):
            monthly_rate[m] = round(safe_div(by_month[m], msg_by_month[m]) * 100, 1)

        return {
            "total": total,
            "by_period": dict(by_period),
            "monthly_rate_pct": monthly_rate,
        }

    return {
        "me": count_kk(msgs_me),
        "other": count_kk(msgs_other),
    }


def analyze_words(msgs_me, msgs_other, start, end):
    """주요 단어/표현 빈도"""
    groups = {
        "사과": ["죄송", "미안", "잘못"],
        "애정": ["사랑", "보고싶", "좋아"],
        "공포": ["무서", "겁나", "불안"],
        "감사": ["감사", "고마"],
    }

    def count_group(msgs, words):
        result = {}
        for w in words:
            by_period = defaultdict(int)
            for dt, msg in msgs:
                c = msg.lower().count(w)
                if c > 0:
                    by_period[period_label(dt, start, end)] += c
            result[w] = dict(by_period)
        return result

    out = {}
    for group_name, words in groups.items():
        out[group_name] = {
            "me": count_group(msgs_me, words),
            "other": count_group(msgs_other, words),
        }
    return out


def analyze_silence(msgs, start, end, min_gap_hours=2):
    """침묵 구간"""
    gaps = []
    for i in range(1, len(msgs)):
        dt_prev = msgs[i - 1][0]
        dt_curr = msgs[i][0]
        gap_hours = (dt_curr - dt_prev).total_seconds() / 3600
        if gap_hours < min_gap_hours:
            continue

        h_prev = dt_prev.hour
        h_curr = dt_curr.hour
        is_sleep = False
        if gap_hours < 12:
            if 0 <= h_prev < 10 and 3 <= h_curr < 10:
                is_sleep = True
            if h_prev >= 22 and 3 <= h_curr <= 12:
                is_sleep = True
            if h_prev <= 3 and 10 <= h_curr <= 14:
                is_sleep = True

        if not is_sleep:
            gaps.append({
                "start": dt_prev.strftime("%Y-%m-%d %H:%M"),
                "end": dt_curr.strftime("%Y-%m-%d %H:%M"),
                "hours": round(gap_hours, 1),
                "before_user": msgs[i - 1][1],
                "after_user": msgs[i][1],
            })

    gaps.sort(key=lambda x: -x["hours"])
    return gaps[:10]


def analyze_initiative(msgs, me_name, start, end, gap_hours=2):
    """대화 주도권 (먼저 말 건 사람)"""
    initiators = []
    if not msgs:
        return {}
    initiators.append((msgs[0][0], msgs[0][1]))
    for i in range(1, len(msgs)):
        gap = (msgs[i][0] - msgs[i - 1][0]).total_seconds() / 3600
        if gap >= gap_hours:
            initiators.append((msgs[i][0], msgs[i][1]))

    me_init = sum(1 for _, u in initiators if u == me_name)
    other_init = len(initiators) - me_init
    total = len(initiators)

    by_period = defaultdict(lambda: {"me": 0, "other": 0})
    for dt, user in initiators:
        p = period_label(dt, start, end)
        if user == me_name:
            by_period[p]["me"] += 1
        else:
            by_period[p]["other"] += 1

    by_month = defaultdict(lambda: {"me": 0, "other": 0})
    for dt, user in initiators:
        m = month_key(dt)
        if user == me_name:
            by_month[m]["me"] += 1
        else:
            by_month[m]["other"] += 1

    return {
        "total": total,
        "me": me_init,
        "me_pct": round(safe_div(me_init, total) * 100, 1),
        "other": other_init,
        "other_pct": round(safe_div(other_init, total) * 100, 1),
        "by_period": {k: dict(v) for k, v in by_period.items()},
        "by_month": {k: dict(v) for k, v in sorted(by_month.items())},
    }


def analyze_time_of_day(msgs_me, msgs_other):
    """시간대별 활동"""
    hour_me = Counter(dt.hour for dt, _ in msgs_me)
    hour_other = Counter(dt.hour for dt, _ in msgs_other)

    dawn_me = sum(hour_me[h] for h in range(6))
    dawn_other = sum(hour_other[h] for h in range(6))

    return {
        "me_by_hour": {h: hour_me.get(h, 0) for h in range(24)},
        "other_by_hour": {h: hour_other.get(h, 0) for h in range(24)},
        "dawn_me_pct": round(safe_div(dawn_me, len(msgs_me)) * 100, 1),
        "dawn_other_pct": round(safe_div(dawn_other, len(msgs_other)) * 100, 1),
    }


def analyze_bursts(msgs, me_name, max_gap_seconds=60, min_burst=5):
    """연속 메시지 폭탄"""
    def find_bursts(user_filter):
        bursts = []
        current = []
        for dt, user, msg in msgs:
            if user != user_filter:
                if len(current) >= min_burst:
                    bursts.append(current[:])
                current = []
                continue
            if current:
                gap = (dt - current[-1][0]).total_seconds()
                if gap > max_gap_seconds:
                    if len(current) >= min_burst:
                        bursts.append(current[:])
                    current = [(dt, msg)]
                else:
                    current.append((dt, msg))
            else:
                current = [(dt, msg)]
        if len(current) >= min_burst:
            bursts.append(current[:])
        return bursts

    me_bursts = find_bursts(me_name)
    # 상대방 이름들
    other_names = set(u for _, u, _ in msgs if u != me_name)
    other_bursts = []
    for name in other_names:
        other_bursts.extend(find_bursts(name))

    def summarize(bursts):
        if not bursts:
            return {"count": 0}
        lens = [len(b) for b in bursts]
        return {
            "count": len(bursts),
            "avg_length": round(sum(lens) / len(lens), 1),
            "max_length": max(lens),
        }

    return {
        "me": summarize(me_bursts),
        "other": summarize(other_bursts),
    }


def analyze_questions(msgs_me, msgs_other, start, end):
    """질문 패턴 (물음표)"""
    def count_q(msgs):
        by_period = defaultdict(int)
        total = 0
        for dt, msg in msgs:
            c = msg.count("?") + msg.count("？")
            by_period[period_label(dt, start, end)] += c
            total += c
        return {"total": total, "by_period": dict(by_period)}

    return {"me": count_q(msgs_me), "other": count_q(msgs_other)}


def analyze_crying(msgs_me, msgs_other, start, end):
    """ㅠ/ㅜ 사용"""
    pat = re.compile(r"[ㅠㅜ]{2,}")

    def count(msgs):
        by_month = defaultdict(int)
        total = 0
        for dt, msg in msgs:
            c = len(pat.findall(msg))
            by_month[month_key(dt)] += c
            total += c
        return {"total": total, "by_month": dict(sorted(by_month.items()))}

    return {"me": count(msgs_me), "other": count(msgs_other)}


def analyze_formality(msgs_me, msgs_other, start, end):
    """존댓말 vs 반말"""
    formal_pat = re.compile(r"(요|세요|습니다|합니다|입니다|께요|겠어요|줄게요|할게요|볼게요)\s*[.!?~]*\s*$")
    informal_pat = re.compile(r"(해|야|어|지|냐|나|래|까|을까|자|네)\s*[.!?~]*\s*$")

    def count(msgs):
        formal = defaultdict(int)
        informal = defaultdict(int)
        for dt, msg in msgs:
            p = period_label(dt, start, end)
            if formal_pat.search(msg):
                formal[p] += 1
            if informal_pat.search(msg):
                informal[p] += 1
        result = {}
        for label in ["초기", "중기", "후기"]:
            f = formal.get(label, 0)
            i = informal.get(label, 0)
            t = f + i
            result[label] = {
                "formal": f,
                "informal": i,
                "formal_pct": round(safe_div(f, t) * 100, 1),
            }
        return result

    return {"me": count(msgs_me), "other": count(msgs_other)}


def analyze_media(msgs_me, msgs_other, start, end):
    """이모티콘/사진 vs 텍스트"""
    def count(msgs):
        by_period = defaultdict(lambda: {"media": 0, "text": 0})
        for dt, msg in msgs:
            p = period_label(dt, start, end)
            if is_media(msg):
                by_period[p]["media"] += 1
            else:
                by_period[p]["text"] += 1
        result = {}
        for label in ["초기", "중기", "후기"]:
            d = by_period.get(label, {"media": 0, "text": 0})
            t = d["media"] + d["text"]
            result[label] = {
                "media": d["media"],
                "text": d["text"],
                "media_pct": round(safe_div(d["media"], t) * 100, 1),
            }
        return result

    return {"me": count(msgs_me), "other": count(msgs_other)}


def analyze_day_of_week(msgs_me, msgs_other):
    """요일별 패턴"""
    names = ["월", "화", "수", "목", "금", "토", "일"]
    me_days = Counter(dt.weekday() for dt, _ in msgs_me)
    other_days = Counter(dt.weekday() for dt, _ in msgs_other)
    return {
        names[d]: {"me": me_days.get(d, 0), "other": other_days.get(d, 0)}
        for d in range(7)
    }


def analyze_deleted(msgs_me, msgs_other, start, end):
    """삭제된 메시지"""
    def count(msgs):
        deleted = [dt for dt, msg in msgs if "삭제된 메시지" in msg or "삭제한 메시지" in msg]
        by_period = defaultdict(int)
        for dt in deleted:
            by_period[period_label(dt, start, end)] += 1
        return {"total": len(deleted), "by_period": dict(by_period)}

    return {"me": count(msgs_me), "other": count(msgs_other)}


def analyze_silent_days(msgs, start, end):
    """완전 침묵 날"""
    active = set(dt.strftime("%Y-%m-%d") for dt, _, _ in msgs)
    all_days = set()
    current = start.date()
    while current <= end.date():
        all_days.add(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    silent = sorted(all_days - active)

    # 연속 무대화 구간
    longest_streak = []
    if silent:
        streak = [silent[0]]
        for i in range(1, len(silent)):
            prev = datetime.strptime(silent[i - 1], "%Y-%m-%d")
            curr = datetime.strptime(silent[i], "%Y-%m-%d")
            if (curr - prev).days == 1:
                streak.append(silent[i])
            else:
                if len(streak) > len(longest_streak):
                    longest_streak = streak[:]
                streak = [silent[i]]
        if len(streak) > len(longest_streak):
            longest_streak = streak[:]

    return {
        "total_days": len(all_days),
        "active_days": len(active),
        "silent_days": len(silent),
        "silent_pct": round(safe_div(len(silent), len(all_days)) * 100, 1),
        "longest_streak": len(longest_streak),
        "longest_streak_period": f"{longest_streak[0]}~{longest_streak[-1]}" if longest_streak else "",
    }


def analyze_daily_asymmetry(msgs, me_name, start, end):
    """일별 메시지 비율 비대칭"""
    daily_me = defaultdict(int)
    daily_other = defaultdict(int)
    for dt, user, msg in msgs:
        d = dt.strftime("%Y-%m-%d")
        if user == me_name:
            daily_me[d] += 1
        else:
            daily_other[d] += 1

    all_dates = set(list(daily_me.keys()) + list(daily_other.keys()))
    me_dominant = 0
    other_dominant = 0
    balanced = 0
    max_ratio_day = None
    max_ratio = 0

    for d in all_dates:
        m = daily_me[d]
        o = daily_other[d]
        total = m + o
        if total < 5:
            continue
        if m > o * 1.5:
            me_dominant += 1
        elif o > m * 1.5:
            other_dominant += 1
        else:
            balanced += 1
        ratio = safe_div(m, o, m)
        if ratio > max_ratio:
            max_ratio = ratio
            max_ratio_day = {"date": d, "me": m, "other": o}

    return {
        "me_dominant_days": me_dominant,
        "other_dominant_days": other_dominant,
        "balanced_days": balanced,
        "max_asymmetry": max_ratio_day,
    }


# ============================================================
# 메인 분석 오케스트레이션
# ============================================================

def analyze_all(messages, me_name):
    """모든 분석 실행 → dict"""
    # 정렬
    messages.sort(key=lambda x: x[0])
    start = messages[0][0]
    end = messages[-1][0]

    # 사용자 분리
    msgs_me, msgs_other = split_by_user(messages, me_name)

    # 상대방 이름
    other_names = sorted(set(u for _, u, _ in messages if u != me_name))
    partner_name = other_names[0] if len(other_names) == 1 else "/".join(other_names)

    # 시기 구분 라벨
    third = (end - start).days // 3
    period_dates = {
        "초기": f"~{(start + timedelta(days=third)).strftime('%Y-%m-%d')}",
        "중기": f"~{(start + timedelta(days=third * 2)).strftime('%Y-%m-%d')}",
        "후기": f"~{end.strftime('%Y-%m-%d')}",
    }

    return {
        "meta": {
            "me": me_name,
            "partner": partner_name,
            "total_messages": len(messages),
            "me_messages": len(msgs_me),
            "other_messages": len(msgs_other),
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "total_days": (end - start).days,
            "period_dates": period_dates,
        },
        "frequency": analyze_frequency(messages, me_name, start, end),
        "response_time": analyze_response_time(messages, me_name, start, end),
        "message_length": analyze_message_length(msgs_me, msgs_other, start, end),
        "kk": analyze_kk(msgs_me, msgs_other, start, end),
        "words": analyze_words(msgs_me, msgs_other, start, end),
        "silence": analyze_silence(messages, start, end),
        "initiative": analyze_initiative(messages, me_name, start, end),
        "time_of_day": analyze_time_of_day(msgs_me, msgs_other),
        "bursts": analyze_bursts(messages, me_name),
        "questions": analyze_questions(msgs_me, msgs_other, start, end),
        "crying": analyze_crying(msgs_me, msgs_other, start, end),
        "formality": analyze_formality(msgs_me, msgs_other, start, end),
        "media": analyze_media(msgs_me, msgs_other, start, end),
        "day_of_week": analyze_day_of_week(msgs_me, msgs_other),
        "deleted": analyze_deleted(msgs_me, msgs_other, start, end),
        "silent_days": analyze_silent_days(messages, start, end),
        "daily_asymmetry": analyze_daily_asymmetry(messages, me_name, start, end),
    }


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="범용 카카오톡 대화 통계 분석기")
    parser.add_argument("csv_path", help="카톡 CSV 파일 경로")
    parser.add_argument("--me", help="내 이름 (미지정 시 자동 감지)")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="출력 형식")
    args = parser.parse_args()

    path = os.path.expanduser(args.csv_path)
    if not os.path.exists(path):
        print(f"파일 없음: {path}", file=sys.stderr)
        sys.exit(1)

    # 파싱
    print(f"파싱 중: {path}", file=sys.stderr)
    messages = parse_file(path)
    print(f"메시지 {len(messages)}개 파싱 완료", file=sys.stderr)

    if not messages:
        print("메시지가 없습니다.", file=sys.stderr)
        sys.exit(1)

    # 사용자 감지
    user_counts = detect_users(messages)
    if args.me:
        me_name = args.me
    else:
        me_name = guess_me(user_counts)
        print(f"자동 감지된 '나': {me_name} ({user_counts[me_name]}건)", file=sys.stderr)
        # 다른 사용자 표시
        for name, count in user_counts.most_common():
            if name != me_name:
                print(f"  상대: {name} ({count}건)", file=sys.stderr)

    # 분석
    print("분석 실행 중...", file=sys.stderr)
    result = analyze_all(messages, me_name)

    # 출력
    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 간단 텍스트 요약
        m = result["meta"]
        print(f"=== 카톡 분석 결과 ===")
        print(f"나: {m['me']} ({m['me_messages']}건)")
        print(f"상대: {m['partner']} ({m['other_messages']}건)")
        print(f"기간: {m['start_date']} ~ {m['end_date']} ({m['total_days']}일)")
        print(f"시기: {m['period_dates']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    print("분석 완료.", file=sys.stderr)


if __name__ == "__main__":
    main()
