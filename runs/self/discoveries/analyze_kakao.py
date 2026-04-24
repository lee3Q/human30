#!/usr/bin/env python3
"""
카카오톡 대화 통계 분석 — 이상규의 대화 패턴 발견
stdlib만 사용. python3 analyze_kakao.py 로 실행.
"""

import csv
import re
import os
import io
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ============================================================
# 0. 파일 경로 및 설정
# ============================================================

FILES_JUNGWON = [
    # (path, partner_names, description)
    (
        os.path.expanduser(
            "~/pp/동결/작업실/시스템/아카이브/2026-03-14/폴더/사랑/원본데이터/"
            "KakaoTalk_Chat_나의 소중한 말랑이♥_2025-11-18-15-40-47.csv"
        ),
        {"廷沅"},
        "말랑이 (2025-05 ~ 2025-11)",
    ),
    (
        os.path.expanduser(
            "~/Downloads/통화녹음텍스트/"
            "KakaoTalk_Chat_앤두_2026-03-26-20-21-48.csv"
        ),
        {"앤두"},
        "앤두 (2025-11 ~ 2026-03)",
    ),
]

FILE_PROFESSOR = (
    os.path.expanduser(
        "~/Downloads/KakaoTalk_Chat_박현경 교수님_2026-04-09-18-53-29.csv"
    ),
    {"박현경 교수님"},
    "교수님 (2022-11 ~ 2026-04)",
)

FILE_BROTHER = (
    os.path.expanduser(
        "~/Downloads/KakaoTalk_Chat_형_2026-03-15-23-22-23.csv"
    ),
    {"형"},
    "형 (2022-03 ~ 2026-03)",
)

ME = "이상규"

# ============================================================
# 1. 파서
# ============================================================

# Two CSV formats:
# A) 2025-05-14 20:57:43,"廷沅","메시지"   (quoted, YYYY-MM-DD HH:MM:SS)
# B) 2025.11.27 0:06,이상규,메시지          (unquoted, YYYY.MM.DD H:MM)


def try_read(path):
    """파일 읽기 — 인코딩 자동 감지"""
    for enc in ("utf-8-sig", "utf-8", "euc-kr", "cp949"):
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            return text
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"인코딩 감지 실패: {path}")


# Regex for format A: 2025-05-14 20:57:43,"user","msg"
RE_FORMAT_A = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),"([^"]+)","(.*)"$',
    re.DOTALL,
)

# Regex for format B: 2025.11.27 0:06,user,msg  (date may have single digit month/day)
RE_FORMAT_B = re.compile(
    r'^(\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{2}),([^,]+),(.*)$',
    re.DOTALL,
)

# New line start patterns
RE_NEWLINE_A = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},"')
RE_NEWLINE_B = re.compile(r'^\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{2},')


def parse_datetime_a(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def parse_datetime_b(s):
    # "2025.11.27 0:06" or "2026.3.22 3:33"
    parts = s.split(" ")
    date_parts = parts[0].split(".")
    time_parts = parts[1].split(":")
    return datetime(
        int(date_parts[0]),
        int(date_parts[1]),
        int(date_parts[2]),
        int(time_parts[0]),
        int(time_parts[1]),
    )


def detect_format(text):
    """첫 데이터 줄로 포맷 감지"""
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
    """카톡 CSV 파싱 → [(datetime, user, message), ...]"""
    text = try_read(path)
    fmt = detect_format(text)

    lines = text.split("\n")
    messages = []

    if fmt == "A":
        # Format A: quoted CSV. Multiline messages are inside quotes.
        # Strategy: join lines until we see a new message start
        i = 1  # skip header
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Accumulate lines until we have a complete record
            # A complete record in format A starts with date and has balanced quotes
            if RE_NEWLINE_A.match(line):
                full_line = line
                # Check if quotes are balanced (for multiline messages)
                while full_line.count('"') % 2 != 0 and i + 1 < len(lines):
                    i += 1
                    full_line += "\n" + lines[i]

                m = RE_FORMAT_A.match(full_line)
                if m:
                    dt = parse_datetime_a(m.group(1))
                    user = m.group(2)
                    msg = m.group(3)
                    messages.append((dt, user, msg))
                else:
                    # fallback: try csv reader for tricky cases
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
        # Format B: unquoted CSV, but messages can contain commas and newlines
        i = 1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            if RE_NEWLINE_B.match(line):
                full_line = line
                # If message starts with quote, accumulate until closing quote
                m_start = RE_FORMAT_B.match(line)
                if m_start:
                    msg_part = m_start.group(3)
                    if msg_part.startswith('"') and not msg_part.endswith('"'):
                        # multiline quoted message
                        while i + 1 < len(lines) and not RE_NEWLINE_B.match(lines[i + 1]):
                            i += 1
                            full_line += "\n" + lines[i]

                m2 = RE_FORMAT_B.match(full_line)
                if m2:
                    try:
                        dt = parse_datetime_b(m2.group(1))
                        user = m2.group(2)
                        msg = m2.group(3)
                        # strip surrounding quotes from multiline msgs
                        if msg.startswith('"') and msg.endswith('"'):
                            msg = msg[1:-1]
                        messages.append((dt, user, msg))
                    except Exception:
                        pass
            else:
                # continuation of previous multiline message (shouldn't happen often after fix above)
                if messages:
                    dt, user, prev_msg = messages[-1]
                    messages[-1] = (dt, user, prev_msg + "\n" + line)
            i += 1
    else:
        print(f"  [WARN] 포맷 감지 실패: {path}")
        return []

    return messages


# ============================================================
# 2. 데이터 로드
# ============================================================

print("=" * 60)
print("카카오톡 통계 분석 시작")
print("=" * 60)

# 정원이 대화 (두 파일 합침, 중복 제거)
all_jw_msgs = []
for path, partner_names, desc in FILES_JUNGWON:
    print(f"\n로딩: {desc}")
    msgs = parse_file(path)
    print(f"  파싱 완료: {len(msgs)}개 메시지")
    if msgs:
        print(f"  기간: {msgs[0][0].strftime('%Y-%m-%d')} ~ {msgs[-1][0].strftime('%Y-%m-%d')}")
    all_jw_msgs.extend(msgs)

# 중복 제거 (같은 시간+사용자+메시지)
seen = set()
jw_msgs_dedup = []
for dt, user, msg in sorted(all_jw_msgs, key=lambda x: x[0]):
    key = (dt.strftime("%Y-%m-%d %H:%M"), user if user == ME else "P", msg[:50])
    if key not in seen:
        seen.add(key)
        jw_msgs_dedup.append((dt, user, msg))

print(f"\n정원이 대화 총 (중복제거 후): {len(jw_msgs_dedup)}개")

# 정원이 이름 정규화
PARTNER_NAMES = {"廷沅", "앤두", "앵두", "말랑이"}


def normalize_user(user):
    if user == ME:
        return ME
    return "정원"


jw_msgs = [(dt, normalize_user(user), msg) for dt, user, msg in jw_msgs_dedup]

# 교수 대화
print(f"\n로딩: {FILE_PROFESSOR[2]}")
prof_msgs = parse_file(FILE_PROFESSOR[0])
print(f"  파싱 완료: {len(prof_msgs)}개 메시지")

# 형 대화
print(f"\n로딩: {FILE_BROTHER[2]}")
bro_msgs = parse_file(FILE_BROTHER[0])
print(f"  파싱 완료: {len(bro_msgs)}개 메시지")


# ============================================================
# 3. 분석 함수들
# ============================================================

def split_by_user(msgs):
    me_msgs = [(dt, msg) for dt, user, msg in msgs if user == ME]
    other_msgs = [(dt, msg) for dt, user, msg in msgs if user != ME]
    return me_msgs, other_msgs


def week_key(dt):
    """ISO week key"""
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def month_key(dt):
    return dt.strftime("%Y-%m")


def period_label(dt, start_date, end_date):
    """3등분 시기"""
    total = (end_date - start_date).days
    if total == 0:
        return "전체"
    third = total / 3
    elapsed = (dt - start_date).days
    if elapsed < third:
        return "초기"
    elif elapsed < third * 2:
        return "중기"
    else:
        return "후기"


# ============================================================
# 4. 분석 실행
# ============================================================

results = []  # (title, data_str, meaning, surprise)

# --- 시기 구분 ---
jw_start = jw_msgs[0][0]
jw_end = jw_msgs[-1][0]

me_jw, partner_jw = split_by_user(jw_msgs)

print(f"\n이상규 메시지: {len(me_jw)}개")
print(f"정원이 메시지: {len(partner_jw)}개")
print(f"기간: {jw_start.strftime('%Y-%m-%d')} ~ {jw_end.strftime('%Y-%m-%d')}")

# ============================================================
# 분석 1: 메시지 빈도 시계열 + 급변 지점
# ============================================================
print("\n\n--- 분석 1: 메시지 빈도 시계열 ---")

daily_me = defaultdict(int)
daily_partner = defaultdict(int)

for dt, msg in me_jw:
    daily_me[dt.strftime("%Y-%m-%d")] += 1
for dt, msg in partner_jw:
    daily_partner[dt.strftime("%Y-%m-%d")] += 1

all_dates = sorted(set(list(daily_me.keys()) + list(daily_partner.keys())))

# 주간 집계
weekly_me = defaultdict(int)
weekly_partner = defaultdict(int)
for d in all_dates:
    dt = datetime.strptime(d, "%Y-%m-%d")
    wk = week_key(dt)
    weekly_me[wk] += daily_me[d]
    weekly_partner[wk] += daily_partner[d]

# 급변 지점 찾기 (이동평균 대비)
def find_spikes(daily_counts, window=7, threshold=2.0):
    """이동평균 대비 threshold배 이상인 날"""
    dates = sorted(daily_counts.keys())
    spikes = []
    for i, d in enumerate(dates):
        # 이전 window일의 평균
        start = max(0, i - window)
        window_vals = [daily_counts[dates[j]] for j in range(start, i)] or [1]
        avg = sum(window_vals) / len(window_vals)
        count = daily_counts[d]
        if avg > 0 and count >= avg * threshold and count >= 10:
            spikes.append((d, count, avg, count / avg))
    return sorted(spikes, key=lambda x: -x[3])


spikes_me = find_spikes(daily_me)
spikes_partner = find_spikes(daily_partner)

print(f"이상규 급변 지점 (상위 5):")
for d, cnt, avg, ratio in spikes_me[:5]:
    print(f"  {d}: {cnt}건 (평소 평균 {avg:.1f}건의 {ratio:.1f}배)")

print(f"정원이 급변 지점 (상위 5):")
for d, cnt, avg, ratio in spikes_partner[:5]:
    print(f"  {d}: {cnt}건 (평소 평균 {avg:.1f}건의 {ratio:.1f}배)")

# 급변 지점 주변 메시지 샘플
spike_samples = {}
if spikes_me:
    top_spike = spikes_me[0][0]
    spike_dt = datetime.strptime(top_spike, "%Y-%m-%d")
    nearby = [
        (dt, user, msg)
        for dt, user, msg in jw_msgs
        if abs((dt - spike_dt).days) <= 1
    ][:10]
    spike_samples["이상규_최대급변"] = (top_spike, nearby)

# 최고/최저 대화량 주간
weeks_sorted = sorted(weekly_me.keys())
if weeks_sorted:
    total_weekly = {w: weekly_me[w] + weekly_partner[w] for w in weeks_sorted}
    max_week = max(total_weekly, key=total_weekly.get)
    min_week_candidates = [w for w in weeks_sorted if total_weekly[w] > 0]
    min_week = min(min_week_candidates, key=lambda w: total_weekly[w]) if min_week_candidates else None

    print(f"\n최다 대화 주간: {max_week} ({total_weekly[max_week]}건)")
    if min_week:
        print(f"최소 대화 주간: {min_week} ({total_weekly[min_week]}건)")


# ============================================================
# 분석 2: 응답 시간 분석
# ============================================================
print("\n\n--- 분석 2: 응답 시간 분석 ---")


def compute_response_times(msgs):
    """연속 발화 그룹 → 상대방 첫 응답까지 시간"""
    # 연속된 같은 사용자 메시지를 하나의 발화로 묶고,
    # 다른 사용자의 첫 메시지까지의 시간을 응답시간으로 계산
    if len(msgs) < 2:
        return [], []

    me_to_partner = []  # 이상규 발화 후 정원이가 답할 때까지
    partner_to_me = []  # 정원이 발화 후 이상규가 답할 때까지

    prev_user = msgs[0][1]
    prev_time = msgs[0][0]
    group_start = msgs[0][0]

    for i in range(1, len(msgs)):
        dt, user, msg = msgs[i]
        if user != prev_user:
            # 사용자 전환! 응답 시간 = 현재 메시지 시간 - 이전 그룹 마지막 메시지 시간
            gap = (dt - prev_time).total_seconds()
            # 합리적 범위만 (1초 ~ 6시간)
            if 1 <= gap <= 21600:
                if prev_user == ME:
                    me_to_partner.append((dt, gap, period_label(dt, jw_start, jw_end)))
                else:
                    partner_to_me.append((dt, gap, period_label(dt, jw_start, jw_end)))
            group_start = dt
        prev_user = user
        prev_time = dt

    return me_to_partner, partner_to_me


me_to_p, p_to_me = compute_response_times(jw_msgs)

# 시기별 평균 응답 시간
for label in ["초기", "중기", "후기"]:
    m2p = [gap for _, gap, p in me_to_p if p == label]
    p2m = [gap for _, gap, p in p_to_me if p == label]
    if m2p and p2m:
        avg_m2p = sum(m2p) / len(m2p)
        avg_p2m = sum(p2m) / len(p2m)
        med_m2p = sorted(m2p)[len(m2p) // 2]
        med_p2m = sorted(p2m)[len(p2m) // 2]
        print(
            f"  [{label}] 정원→이상규 응답: 평균 {avg_p2m:.0f}초 (중앙 {med_p2m:.0f}초) | "
            f"이상규→정원 응답: 평균 {avg_m2p:.0f}초 (중앙 {med_m2p:.0f}초)"
        )

# 비대칭 역전 지점 (주별)
weekly_resp_me = defaultdict(list)
weekly_resp_partner = defaultdict(list)
for dt, gap, _ in p_to_me:
    weekly_resp_me[week_key(dt)].append(gap)
for dt, gap, _ in me_to_p:
    weekly_resp_partner[week_key(dt)].append(gap)

reversals = []
prev_faster = None
common_weeks = sorted(set(weekly_resp_me.keys()) & set(weekly_resp_partner.keys()))
for w in common_weeks:
    avg_me = sum(weekly_resp_me[w]) / len(weekly_resp_me[w])
    avg_p = sum(weekly_resp_partner[w]) / len(weekly_resp_partner[w])
    faster = ME if avg_me < avg_p else "정원"
    if prev_faster and faster != prev_faster:
        reversals.append((w, prev_faster, faster, avg_me, avg_p))
    prev_faster = faster

print(f"\n응답 속도 역전 횟수: {len(reversals)}")
for w, prev, curr, avg_me, avg_p in reversals[:5]:
    print(
        f"  {w}: {prev}→{curr}로 역전 "
        f"(이상규 응답 {avg_me:.0f}초, 정원 응답 {avg_p:.0f}초)"
    )


# ============================================================
# 분석 3: 메시지 길이 분석
# ============================================================
print("\n\n--- 분석 3: 메시지 길이 분석 ---")

# 시기별 평균 길이
for label in ["초기", "중기", "후기"]:
    me_lens = [
        len(msg)
        for dt, msg in me_jw
        if period_label(dt, jw_start, jw_end) == label
        and msg not in ("사진", "이모티콘", "동영상", "보이스톡", "페이스톡")
        and not msg.startswith("파일:")
    ]
    p_lens = [
        len(msg)
        for dt, msg in partner_jw
        if period_label(dt, jw_start, jw_end) == label
        and msg not in ("사진", "이모티콘", "동영상", "보이스톡", "페이스톡")
        and not msg.startswith("파일:")
    ]
    if me_lens and p_lens:
        print(
            f"  [{label}] 이상규 평균 {sum(me_lens)/len(me_lens):.1f}자 "
            f"(중앙 {sorted(me_lens)[len(me_lens)//2]}자) | "
            f"정원이 평균 {sum(p_lens)/len(p_lens):.1f}자 "
            f"(중앙 {sorted(p_lens)[len(p_lens)//2]}자)"
        )

# 장문 폭발 (500자+)
long_msgs_me = [
    (dt, msg)
    for dt, msg in me_jw
    if len(msg) >= 500
    and msg not in ("사진", "이모티콘")
]
long_msgs_p = [
    (dt, msg)
    for dt, msg in partner_jw
    if len(msg) >= 500
    and msg not in ("사진", "이모티콘")
]

print(f"\n이상규 장문(500자+): {len(long_msgs_me)}건")
print(f"정원이 장문(500자+): {len(long_msgs_p)}건")

# 장문 시간대 분포
hour_dist_long_me = Counter()
hour_dist_long_p = Counter()
for dt, msg in long_msgs_me:
    hour_dist_long_me[dt.hour] += 1
for dt, msg in long_msgs_p:
    hour_dist_long_p[dt.hour] += 1

print(f"\n이상규 장문 시간대 분포:")
for h in sorted(hour_dist_long_me.keys()):
    pct = hour_dist_long_me[h] / len(long_msgs_me) * 100 if long_msgs_me else 0
    print(f"  {h:02d}시: {hour_dist_long_me[h]}건 ({pct:.1f}%)")

# 장문 직전 맥락
print(f"\n이상규 장문 직전 3메시지 (최근 5건):")
for dt_long, msg_long in long_msgs_me[-5:]:
    print(f"\n  [{dt_long.strftime('%Y-%m-%d %H:%M')}] 장문 ({len(msg_long)}자)")
    # 직전 메시지 찾기
    prev_msgs = [
        (dt, user, msg)
        for dt, user, msg in jw_msgs
        if dt < dt_long and (dt_long - dt).total_seconds() < 3600
    ][-3:]
    for dt, user, msg in prev_msgs:
        print(f"    [{user}] {msg[:80]}{'...' if len(msg) > 80 else ''}")

# 정원이 메시지 길이 트렌드 (월별)
monthly_p_len = defaultdict(list)
for dt, msg in partner_jw:
    if msg not in ("사진", "이모티콘", "동영상", "보이스톡", "페이스톡"):
        monthly_p_len[month_key(dt)].append(len(msg))

print(f"\n정원이 월별 평균 메시지 길이:")
for m in sorted(monthly_p_len.keys()):
    vals = monthly_p_len[m]
    print(f"  {m}: 평균 {sum(vals)/len(vals):.1f}자 ({len(vals)}건)")


# ============================================================
# 분석 4: 특정 단어/표현 빈도
# ============================================================
print("\n\n--- 분석 4: 단어/표현 빈도 ---")

WORD_GROUPS = {
    "사과": ["죄송", "미안", "잘못"],
    "복종": ["주인님", "복종", "소유"],
    "애정": ["사랑", "보고싶", "좋아"],
    "통제": ["분석", "시스템", "매뉴얼", "규칙"],
    "공포": ["무서", "겁나", "겁이", "불안"],
}


def count_words(msgs, words):
    """메시지 리스트에서 단어별 시기별 빈도"""
    counts = defaultdict(lambda: defaultdict(int))
    for dt, msg in msgs:
        p = period_label(dt, jw_start, jw_end)
        msg_lower = msg.lower()
        for w in words:
            c = msg_lower.count(w)
            if c > 0:
                counts[w][p] += c
    return counts


for group_name, words in WORD_GROUPS.items():
    print(f"\n[{group_name}]")
    me_counts = count_words(me_jw, words)
    p_counts = count_words(partner_jw, words)

    for w in words:
        me_total = sum(me_counts[w].values())
        p_total = sum(p_counts[w].values())
        if me_total + p_total == 0:
            continue
        print(f"  '{w}':")
        print(f"    이상규: 초기 {me_counts[w].get('초기',0)} / 중기 {me_counts[w].get('중기',0)} / 후기 {me_counts[w].get('후기',0)} (총 {me_total})")
        print(f"    정원이: 초기 {p_counts[w].get('초기',0)} / 중기 {p_counts[w].get('중기',0)} / 후기 {p_counts[w].get('후기',0)} (총 {p_total})")

# ㅋㅋ 빈도 (웃음)
kk_pattern = re.compile(r"ㅋ{2,}")


def count_kk(msgs):
    by_period = defaultdict(int)
    total = 0
    for dt, msg in msgs:
        found = kk_pattern.findall(msg)
        c = len(found)
        total += c
        by_period[period_label(dt, jw_start, jw_end)] += c
    return total, by_period


me_kk_total, me_kk_period = count_kk(me_jw)
p_kk_total, p_kk_period = count_kk(partner_jw)
print(f"\n[ㅋㅋ 빈도]")
print(f"  이상규: 초기 {me_kk_period.get('초기',0)} / 중기 {me_kk_period.get('중기',0)} / 후기 {me_kk_period.get('후기',0)} (총 {me_kk_total})")
print(f"  정원이: 초기 {p_kk_period.get('초기',0)} / 중기 {p_kk_period.get('중기',0)} / 후기 {p_kk_period.get('후기',0)} (총 {p_kk_total})")

# 월별 상세 (ㅋㅋ)
monthly_kk_me = defaultdict(int)
monthly_kk_p = defaultdict(int)
monthly_msg_me = defaultdict(int)
monthly_msg_p = defaultdict(int)
for dt, msg in me_jw:
    monthly_msg_me[month_key(dt)] += 1
    monthly_kk_me[month_key(dt)] += len(kk_pattern.findall(msg))
for dt, msg in partner_jw:
    monthly_msg_p[month_key(dt)] += 1
    monthly_kk_p[month_key(dt)] += len(kk_pattern.findall(msg))

print(f"\n월별 ㅋㅋ 비율 (ㅋㅋ 포함 비율):")
for m in sorted(set(list(monthly_kk_me.keys()) + list(monthly_kk_p.keys()))):
    me_rate = monthly_kk_me[m] / monthly_msg_me[m] * 100 if monthly_msg_me[m] else 0
    p_rate = monthly_kk_p[m] / monthly_msg_p[m] * 100 if monthly_msg_p[m] else 0
    print(f"  {m}: 이상규 {me_rate:.1f}% ({monthly_kk_me[m]}/{monthly_msg_me[m]}) | 정원이 {p_rate:.1f}% ({monthly_kk_p[m]}/{monthly_msg_p[m]})")


# ============================================================
# 분석 5: 침묵 구간
# ============================================================
print("\n\n--- 분석 5: 침묵 구간 (2시간+, 활동 시간대 10:00~03:00) ---")


def find_silence_gaps(msgs, min_gap_hours=2):
    """활동 시간대(10:00~03:00) 내 2시간+ 침묵"""
    gaps = []
    for i in range(1, len(msgs)):
        dt_prev = msgs[i - 1][0]
        dt_curr = msgs[i][0]
        gap_seconds = (dt_curr - dt_prev).total_seconds()
        gap_hours = gap_seconds / 3600

        if gap_hours < min_gap_hours:
            continue

        # 활동 시간대 확인: 두 메시지 모두 10:00~27:00(=03:00) 사이여야
        # 03:00~10:00 사이의 침묵은 수면으로 간주하여 제외
        h_prev = dt_prev.hour
        h_curr = dt_curr.hour

        # 수면 시간 (03:00~10:00) 중간에 걸치면 제외
        is_sleep = False
        if gap_hours < 12:  # 12시간 이상이면 무조건 포함
            if h_prev >= 0 and h_prev < 10 and h_curr >= 3 and h_curr < 10:
                is_sleep = True
            if h_prev >= 22 and h_curr >= 3 and h_curr <= 12:
                is_sleep = True
            # 새벽 종료 → 오전 시작
            if h_prev <= 3 and h_curr >= 10 and h_curr <= 14:
                is_sleep = True

        if not is_sleep:
            gaps.append((
                dt_prev,
                msgs[i - 1][1],
                msgs[i - 1][2],
                dt_curr,
                msgs[i][1],
                msgs[i][2],
                gap_hours,
            ))

    return sorted(gaps, key=lambda x: -x[6])


silence_gaps = find_silence_gaps(jw_msgs)

print(f"활동 시간대 침묵 구간 (상위 15):")
for dt_prev, user_prev, msg_prev, dt_curr, user_curr, msg_curr, hours in silence_gaps[:15]:
    print(
        f"  {dt_prev.strftime('%Y-%m-%d %H:%M')} ~ {dt_curr.strftime('%Y-%m-%d %H:%M')} "
        f"({hours:.1f}시간)"
    )
    print(f"    직전: [{user_prev}] {msg_prev[:60]}{'...' if len(msg_prev) > 60 else ''}")
    print(f"    직후: [{user_curr}] {msg_curr[:60]}{'...' if len(msg_curr) > 60 else ''}")


# ============================================================
# 분석 6: 대화 주도권 비율
# ============================================================
print("\n\n--- 분석 6: 대화 주도권 (먼저 말 건 사람) ---")


def find_initiator(msgs, gap_hours=2):
    """gap_hours 이상 침묵 후 먼저 말 건 사람"""
    initiators = []
    if not msgs:
        return initiators
    initiators.append((msgs[0][0], msgs[0][1]))  # 첫 메시지

    for i in range(1, len(msgs)):
        gap = (msgs[i][0] - msgs[i - 1][0]).total_seconds() / 3600
        if gap >= gap_hours:
            initiators.append((msgs[i][0], msgs[i][1]))

    return initiators


initiators = find_initiator(jw_msgs)

me_init = sum(1 for _, u in initiators if u == ME)
p_init = sum(1 for _, u in initiators if u != ME)
total_init = len(initiators)
print(f"총 대화 시작 횟수: {total_init}")
print(f"이상규 먼저: {me_init} ({me_init/total_init*100:.1f}%)")
print(f"정원이 먼저: {p_init} ({p_init/total_init*100:.1f}%)")

# 시기별
init_by_period = defaultdict(lambda: {"me": 0, "p": 0})
for dt, user in initiators:
    p = period_label(dt, jw_start, jw_end)
    if user == ME:
        init_by_period[p]["me"] += 1
    else:
        init_by_period[p]["p"] += 1

for label in ["초기", "중기", "후기"]:
    d = init_by_period[label]
    total = d["me"] + d["p"]
    if total:
        print(
            f"  [{label}] 이상규 {d['me']} ({d['me']/total*100:.1f}%) / "
            f"정원이 {d['p']} ({d['p']/total*100:.1f}%)"
        )

# 월별 주도권
monthly_init = defaultdict(lambda: {"me": 0, "p": 0})
for dt, user in initiators:
    m = month_key(dt)
    if user == ME:
        monthly_init[m]["me"] += 1
    else:
        monthly_init[m]["p"] += 1

print(f"\n월별 대화 시작 비율:")
for m in sorted(monthly_init.keys()):
    d = monthly_init[m]
    total = d["me"] + d["p"]
    if total:
        print(
            f"  {m}: 이상규 {d['me']}/{total} ({d['me']/total*100:.0f}%) / "
            f"정원이 {d['p']}/{total} ({d['p']/total*100:.0f}%)"
        )


# ============================================================
# 분석 7: 이모티콘/사진 vs 텍스트
# ============================================================
print("\n\n--- 분석 7: 이모티콘/사진 vs 텍스트 ---")

MEDIA_KEYWORDS = {"사진", "이모티콘", "동영상", "보이스톡", "페이스톡"}


def count_media(msgs):
    by_period = defaultdict(lambda: {"media": 0, "text": 0})
    monthly = defaultdict(lambda: {"media": 0, "text": 0})
    for dt, msg in msgs:
        p = period_label(dt, jw_start, jw_end)
        m = month_key(dt)
        is_media = msg.strip() in MEDIA_KEYWORDS or msg.startswith("파일:")
        if is_media:
            by_period[p]["media"] += 1
            monthly[m]["media"] += 1
        else:
            by_period[p]["text"] += 1
            monthly[m]["text"] += 1
    return by_period, monthly


me_media_period, me_media_monthly = count_media(me_jw)
p_media_period, p_media_monthly = count_media(partner_jw)

print("정원이 이모티콘/사진 비율 (시기별):")
for label in ["초기", "중기", "후기"]:
    d = p_media_period[label]
    total = d["media"] + d["text"]
    if total:
        print(
            f"  [{label}] 미디어 {d['media']}/{total} ({d['media']/total*100:.1f}%)"
        )

print("\n정원이 이모티콘/사진 비율 (월별):")
for m in sorted(p_media_monthly.keys()):
    d = p_media_monthly[m]
    total = d["media"] + d["text"]
    if total:
        print(
            f"  {m}: 미디어 {d['media']}/{total} ({d['media']/total*100:.1f}%)"
        )


# ============================================================
# 분석 8: 교수·형 비교
# ============================================================
print("\n\n--- 분석 8: 교수·형 대화 비교 ---")

me_prof = [(dt, msg) for dt, user, msg in prof_msgs if user == ME]
me_bro = [(dt, msg) for dt, user, msg in bro_msgs if user == ME]

# 평균 메시지 길이
def avg_len(msgs):
    text_msgs = [
        len(msg)
        for dt, msg in msgs
        if msg.strip() not in MEDIA_KEYWORDS and not msg.startswith("파일:")
    ]
    if not text_msgs:
        return 0, 0
    return sum(text_msgs) / len(text_msgs), sorted(text_msgs)[len(text_msgs) // 2]


avg_jw, med_jw = avg_len(me_jw)
avg_prof, med_prof = avg_len(me_prof)
avg_bro, med_bro = avg_len(me_bro)

print(f"이상규 평균 메시지 길이:")
print(f"  → 정원이: 평균 {avg_jw:.1f}자 (중앙 {med_jw}자) [{len(me_jw)}건]")
print(f"  → 교수님: 평균 {avg_prof:.1f}자 (중앙 {med_prof}자) [{len(me_prof)}건]")
print(f"  → 형:     평균 {avg_bro:.1f}자 (중앙 {med_bro}자) [{len(me_bro)}건]")

# 감정어 빈도 비교
emotion_words = ["사랑", "보고싶", "좋아", "미안", "죄송", "힘들", "슬프", "아프"]
print(f"\n감정어 빈도 (메시지 1000건당):")
for w in emotion_words:
    c_jw = sum(1 for _, msg in me_jw if w in msg)
    c_prof = sum(1 for _, msg in me_prof if w in msg)
    c_bro = sum(1 for _, msg in me_bro if w in msg)
    r_jw = c_jw / len(me_jw) * 1000 if me_jw else 0
    r_prof = c_prof / len(me_prof) * 1000 if me_prof else 0
    r_bro = c_bro / len(me_bro) * 1000 if me_bro else 0
    if c_jw + c_prof + c_bro > 0:
        print(f"  '{w}': 정원이 {r_jw:.1f} / 교수님 {r_prof:.1f} / 형 {r_bro:.1f}")

# ㅋㅋ 비교
kk_jw = sum(1 for _, msg in me_jw if kk_pattern.search(msg))
kk_prof = sum(1 for _, msg in me_prof if kk_pattern.search(msg))
kk_bro = sum(1 for _, msg in me_bro if kk_pattern.search(msg))
r_kk_jw = kk_jw / len(me_jw) * 100 if me_jw else 0
r_kk_prof = kk_prof / len(me_prof) * 100 if me_prof else 0
r_kk_bro = kk_bro / len(me_bro) * 100 if me_bro else 0
print(f"\nㅋㅋ 포함 메시지 비율:")
print(f"  → 정원이: {r_kk_jw:.1f}% ({kk_jw}/{len(me_jw)})")
print(f"  → 교수님: {r_kk_prof:.1f}% ({kk_prof}/{len(me_prof)})")
print(f"  → 형:     {r_kk_bro:.1f}% ({kk_bro}/{len(me_bro)})")


# ============================================================
# 추가 분석: 시간대별 활동 패턴
# ============================================================
print("\n\n--- 추가 분석: 시간대별 활동 ---")

hour_me = Counter()
hour_p = Counter()
for dt, msg in me_jw:
    hour_me[dt.hour] += 1
for dt, msg in partner_jw:
    hour_p[dt.hour] += 1

print("이상규 vs 정원이 시간대별 메시지 수:")
for h in range(24):
    bar_me = "#" * (hour_me[h] // 50)
    bar_p = "." * (hour_p[h] // 50)
    print(f"  {h:02d}시: 이상규 {hour_me[h]:5d} {bar_me}")
    print(f"        정원이 {hour_p[h]:5d} {bar_p}")

# 새벽(00~05시) 메시지 비율
dawn_me = sum(hour_me[h] for h in range(6))
dawn_p = sum(hour_p[h] for h in range(6))
dawn_me_pct = dawn_me / len(me_jw) * 100 if me_jw else 0
dawn_p_pct = dawn_p / len(partner_jw) * 100 if partner_jw else 0
print(f"\n새벽(00~05시) 메시지 비율: 이상규 {dawn_me_pct:.1f}% / 정원이 {dawn_p_pct:.1f}%")


# ============================================================
# 추가 분석: 연속 메시지 폭탄
# ============================================================
print("\n\n--- 추가 분석: 연속 메시지 (1분 내 연속) ---")


def find_bursts(msgs, user_filter, max_gap_seconds=60, min_burst=5):
    """1분 내 연속 메시지 그룹 찾기"""
    bursts = []
    current_burst = []

    for dt, user, msg in msgs:
        if user != user_filter:
            if len(current_burst) >= min_burst:
                bursts.append(current_burst[:])
            current_burst = []
            continue

        if current_burst:
            gap = (dt - current_burst[-1][0]).total_seconds()
            if gap > max_gap_seconds:
                if len(current_burst) >= min_burst:
                    bursts.append(current_burst[:])
                current_burst = [(dt, msg)]
            else:
                current_burst.append((dt, msg))
        else:
            current_burst = [(dt, msg)]

    if len(current_burst) >= min_burst:
        bursts.append(current_burst[:])

    return bursts


me_bursts = find_bursts(jw_msgs, ME)
p_bursts = find_bursts(jw_msgs, "정원")

print(f"이상규 연속 메시지 폭탄 (5개+): {len(me_bursts)}회")
if me_bursts:
    burst_lens = [len(b) for b in me_bursts]
    print(f"  평균 연속 수: {sum(burst_lens)/len(burst_lens):.1f}개")
    print(f"  최대 연속 수: {max(burst_lens)}개")
    # 최대 폭탄
    max_burst = max(me_bursts, key=len)
    print(f"  최대 폭탄 시점: {max_burst[0][0].strftime('%Y-%m-%d %H:%M')} ({len(max_burst)}개)")
    for dt, msg in max_burst[:5]:
        print(f"    [{dt.strftime('%H:%M')}] {msg[:60]}{'...' if len(msg) > 60 else ''}")
    if len(max_burst) > 5:
        print(f"    ... 외 {len(max_burst)-5}개")

print(f"\n정원이 연속 메시지 폭탄 (5개+): {len(p_bursts)}회")
if p_bursts:
    p_burst_lens = [len(b) for b in p_bursts]
    print(f"  평균 연속 수: {sum(p_burst_lens)/len(p_burst_lens):.1f}개")
    print(f"  최대 연속 수: {max(p_burst_lens)}개")


# ============================================================
# 추가 분석: 물음표 빈도 (질문 패턴)
# ============================================================
print("\n\n--- 추가 분석: 질문 패턴 (물음표) ---")

q_me = defaultdict(int)
q_p = defaultdict(int)
q_me_total = 0
q_p_total = 0
for dt, msg in me_jw:
    c = msg.count("?") + msg.count("？")
    q_me[period_label(dt, jw_start, jw_end)] += c
    q_me_total += c
for dt, msg in partner_jw:
    c = msg.count("?") + msg.count("？")
    q_p[period_label(dt, jw_start, jw_end)] += c
    q_p_total += c

print(f"물음표 사용:")
for label in ["초기", "중기", "후기"]:
    print(f"  [{label}] 이상규 {q_me.get(label,0)} / 정원이 {q_p.get(label,0)}")
print(f"  [총합] 이상규 {q_me_total} / 정원이 {q_p_total}")


# ============================================================
# 추가 분석: 메시지 수 비율 (일별 비대칭)
# ============================================================
print("\n\n--- 추가 분석: 일별 메시지 비율 비대칭 ---")

days_me_dominant = 0
days_p_dominant = 0
days_balanced = 0
max_ratio_day = None
max_ratio = 0

for d in all_dates:
    m = daily_me[d]
    p = daily_partner[d]
    total = m + p
    if total < 5:
        continue
    if m > p * 1.5:
        days_me_dominant += 1
    elif p > m * 1.5:
        days_p_dominant += 1
    else:
        days_balanced += 1

    ratio = m / p if p > 0 else m
    if ratio > max_ratio:
        max_ratio = ratio
        max_ratio_day = (d, m, p)

print(f"이상규 우세 일수 (1.5배+): {days_me_dominant}")
print(f"정원이 우세 일수 (1.5배+): {days_p_dominant}")
print(f"균형 일수: {days_balanced}")
if max_ratio_day:
    d, m, p = max_ratio_day
    print(f"최대 비대칭 날: {d} (이상규 {m} : 정원이 {p})")


# ============================================================
# 추가 분석: "ㅠ" 사용 빈도
# ============================================================
print("\n\n--- 추가 분석: ㅠ/ㅜ 사용 빈도 ---")

crying_pattern = re.compile(r"[ㅠㅜ]{2,}")

cry_me = defaultdict(int)
cry_p = defaultdict(int)
for dt, msg in me_jw:
    c = len(crying_pattern.findall(msg))
    cry_me[month_key(dt)] += c
for dt, msg in partner_jw:
    c = len(crying_pattern.findall(msg))
    cry_p[month_key(dt)] += c

print("월별 ㅠ/ㅜ 사용:")
for m in sorted(set(list(cry_me.keys()) + list(cry_p.keys()))):
    print(f"  {m}: 이상규 {cry_me[m]} / 정원이 {cry_p[m]}")


# ============================================================
# 추가 분석: 요일별 패턴
# ============================================================
print("\n\n--- 추가 분석: 요일별 메시지 패턴 ---")

DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
day_me = Counter()
day_p = Counter()
for dt, msg in me_jw:
    day_me[dt.weekday()] += 1
for dt, msg in partner_jw:
    day_p[dt.weekday()] += 1

for d in range(7):
    print(f"  {DAY_NAMES[d]}: 이상규 {day_me[d]} / 정원이 {day_p[d]}")


# ============================================================
# 추가 분석: "삭제된 메시지" 패턴
# ============================================================
print("\n\n--- 추가 분석: 삭제된 메시지 ---")

deleted_me = [(dt, msg) for dt, msg in me_jw if "삭제된 메시지" in msg or "삭제한 메시지" in msg]
deleted_p = [(dt, msg) for dt, msg in partner_jw if "삭제된 메시지" in msg or "삭제한 메시지" in msg]

print(f"이상규 삭제 메시지: {len(deleted_me)}건")
print(f"정원이 삭제 메시지: {len(deleted_p)}건")

if deleted_me:
    del_by_period = defaultdict(int)
    for dt, _ in deleted_me:
        del_by_period[period_label(dt, jw_start, jw_end)] += 1
    print(f"  이상규 시기별: {dict(del_by_period)}")
if deleted_p:
    del_by_period_p = defaultdict(int)
    for dt, _ in deleted_p:
        del_by_period_p[period_label(dt, jw_start, jw_end)] += 1
    print(f"  정원이 시기별: {dict(del_by_period_p)}")


# ============================================================
# 추가 분석: 통화(보이스톡/페이스톡) 패턴
# ============================================================
print("\n\n--- 추가 분석: 통화 패턴 ---")

calls = [(dt, user, msg) for dt, user, msg in jw_msgs if msg.strip() in ("보이스톡", "페이스톡")]
call_me = [(dt, msg) for dt, user, msg in calls if user == ME]
call_p = [(dt, msg) for dt, user, msg in calls if user != ME]

print(f"이상규 통화 시작: {len(call_me)}건")
print(f"정원이 통화 시작: {len(call_p)}건")

if calls:
    call_by_month = defaultdict(int)
    for dt, _, _ in calls:
        call_by_month[month_key(dt)] += 1
    print("월별 통화:")
    for m in sorted(call_by_month.keys()):
        print(f"  {m}: {call_by_month[m]}건")


# ============================================================
# 추가 분석: "~" 사용 (말투 변화)
# ============================================================
print("\n\n--- 추가 분석: 말투 패턴 ---")

# 존댓말 vs 반말 (요/세요/습니다 vs 해/야/어)
formal_me = defaultdict(int)
informal_me = defaultdict(int)
formal_p = defaultdict(int)
informal_p = defaultdict(int)

formal_endings = re.compile(r"(요|세요|습니다|합니다|입니다|께요|겠어요|줄게요|할게요|볼게요)\s*[.!?~]*\s*$")
informal_endings = re.compile(r"(해|야|어|지|냐|나|래|까|을까|자|네)\s*[.!?~]*\s*$")

for dt, msg in me_jw:
    p = period_label(dt, jw_start, jw_end)
    # Check each sentence
    if formal_endings.search(msg):
        formal_me[p] += 1
    if informal_endings.search(msg):
        informal_me[p] += 1

for dt, msg in partner_jw:
    p = period_label(dt, jw_start, jw_end)
    if formal_endings.search(msg):
        formal_p[p] += 1
    if informal_endings.search(msg):
        informal_p[p] += 1

print("존댓말 비율 (시기별):")
for label in ["초기", "중기", "후기"]:
    f_me = formal_me.get(label, 0)
    i_me = informal_me.get(label, 0)
    f_p = formal_p.get(label, 0)
    i_p = informal_p.get(label, 0)
    t_me = f_me + i_me
    t_p = f_p + i_p
    r_me = f_me / t_me * 100 if t_me else 0
    r_p = f_p / t_p * 100 if t_p else 0
    print(f"  [{label}] 이상규 존댓말 {r_me:.1f}% ({f_me}/{t_me}) | 정원이 존댓말 {r_p:.1f}% ({f_p}/{t_p})")


# ============================================================
# 추가 분석: 첫 메시지/마지막 메시지 시간 패턴
# ============================================================
print("\n\n--- 추가 분석: 일별 첫/마지막 메시지 시간 ---")

daily_first_me = {}
daily_last_me = {}
daily_first_p = {}
daily_last_p = {}

for dt, msg in me_jw:
    d = dt.strftime("%Y-%m-%d")
    if d not in daily_first_me or dt < daily_first_me[d]:
        daily_first_me[d] = dt
    if d not in daily_last_me or dt > daily_last_me[d]:
        daily_last_me[d] = dt

for dt, msg in partner_jw:
    d = dt.strftime("%Y-%m-%d")
    if d not in daily_first_p or dt < daily_first_p[d]:
        daily_first_p[d] = dt
    if d not in daily_last_p or dt > daily_last_p[d]:
        daily_last_p[d] = dt

# 이상규가 정원이보다 먼저 인사하는 비율
both_days = sorted(set(daily_first_me.keys()) & set(daily_first_p.keys()))
me_first_count = sum(1 for d in both_days if daily_first_me[d] < daily_first_p[d])
p_first_count = sum(1 for d in both_days if daily_first_p[d] < daily_first_me[d])
print(f"양쪽 모두 메시지 보낸 날: {len(both_days)}일")
print(f"이상규 먼저 시작: {me_first_count}일 ({me_first_count/len(both_days)*100:.1f}%)" if both_days else "")
print(f"정원이 먼저 시작: {p_first_count}일 ({p_first_count/len(both_days)*100:.1f}%)" if both_days else "")

# 이상규 마지막 메시지 시간 분포
late_me = [daily_last_me[d].hour for d in daily_last_me]
late_me_avg = sum(late_me) / len(late_me) if late_me else 0
print(f"\n이상규 마지막 메시지 평균 시각: {int(late_me_avg)}시")

# 새벽 3시 이후 대화 일수
after_3am_days = set()
for dt, msg in me_jw:
    if dt.hour >= 3 and dt.hour < 6:
        after_3am_days.add(dt.strftime("%Y-%m-%d"))
    elif dt.hour >= 0 and dt.hour < 3:
        after_3am_days.add(dt.strftime("%Y-%m-%d"))
print(f"이상규 새벽(00~06시) 메시지 보낸 날: {len(after_3am_days)}일 / 전체 {len(set(d for dt, msg in me_jw for d in [dt.strftime('%Y-%m-%d')]))}일")


# ============================================================
# 모든 분석 결과 종합 → 보고서 생성
# ============================================================
print("\n\n" + "=" * 60)
print("분석 완료. 보고서 생성 중...")
print("=" * 60)

# ---- 보고서 내용 수집 ----

report_lines = []
report_lines.append("# 카톡 통계 분석 결과\n")
report_lines.append(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
report_lines.append(f"데이터 기간: {jw_start.strftime('%Y-%m-%d')} ~ {jw_end.strftime('%Y-%m-%d')}")
report_lines.append(f"총 메시지: {len(jw_msgs)}개 (이상규 {len(me_jw)} / 정원이 {len(partner_jw)})")
report_lines.append(f"시기 구분: 초기(~{(jw_start + timedelta(days=(jw_end-jw_start).days//3)).strftime('%Y-%m-%d')}) / 중기(~{(jw_start + timedelta(days=(jw_end-jw_start).days*2//3)).strftime('%Y-%m-%d')}) / 후기(~{jw_end.strftime('%Y-%m-%d')})")
report_lines.append("")

discovery_num = 0


def add_discovery(title, data, meaning, surprise):
    global discovery_num
    discovery_num += 1
    report_lines.append(f"\n## 발견 {discovery_num} -- {title}\n")
    report_lines.append(f"- 데이터: {data}")
    report_lines.append(f"- 의미: {meaning}")
    report_lines.append(f"- 놀라운 이유: {surprise}")


# 발견 1: 장문 시간대
if long_msgs_me:
    dawn_long = sum(1 for dt, _ in long_msgs_me if dt.hour >= 0 and dt.hour < 6)
    dawn_pct = dawn_long / len(long_msgs_me) * 100
    # 정원이 장문 시간 분포
    p_dawn_long = sum(1 for dt, _ in long_msgs_p if dt.hour >= 0 and dt.hour < 6) if long_msgs_p else 0
    p_dawn_pct = p_dawn_long / len(long_msgs_p) * 100 if long_msgs_p else 0

    # 구체적으로 어느 시간대에 집중?
    top_hours = sorted(hour_dist_long_me.items(), key=lambda x: -x[1])[:3]
    top_hours_str = ", ".join(f"{h}시({c}건)" for h, c in top_hours)

    add_discovery(
        "이상규의 장문은 새벽에 폭발한다",
        f"이상규의 500자+ 장문 {len(long_msgs_me)}건 중 {dawn_long}건({dawn_pct:.0f}%)이 00~05시에 발생. "
        f"상위 집중 시간: {top_hours_str}. "
        f"반면 정원이의 장문 {len(long_msgs_p)}건 중 새벽은 {p_dawn_long}건({p_dawn_pct:.0f}%).",
        "이상규의 가장 긴 메시지들은 밤의 방어가 풀린 시간대에 나온다. "
        "낮에는 짧게 통제하다가, 새벽에 쏟아내는 패턴.",
        "본인은 '분석적으로 정리해서 보낸다'고 생각하겠지만, "
        "실제로는 수면 욕구와 싸우는 시간대에 가장 많은 말을 쏟아낸다. "
        "이성적 통제가 아니라 충동이 만든 장문.",
    )

# 발견 2: 대화 주도권 비대칭 변화
if init_by_period:
    early = init_by_period["초기"]
    late = init_by_period["후기"]
    e_total = early["me"] + early["p"]
    l_total = late["me"] + late["p"]
    if e_total and l_total:
        e_me_pct = early["me"] / e_total * 100
        l_me_pct = late["me"] / l_total * 100
        add_discovery(
            "이상규의 대화 시작 비율 변화",
            f"초기: 이상규 먼저 {early['me']}/{e_total}({e_me_pct:.0f}%) → "
            f"후기: 이상규 먼저 {late['me']}/{l_total}({l_me_pct:.0f}%). "
            f"정원이의 변화: 초기 {early['p']}/{e_total}({early['p']/e_total*100:.0f}%) → "
            f"후기 {late['p']}/{l_total}({late['p']/l_total*100:.0f}%).",
            "대화를 누가 먼저 시작하는지가 관계 에너지의 방향을 보여준다.",
            f"{'이상규가 점점 더 먼저 말을 걸게 되었다' if l_me_pct > e_me_pct else '정원이가 점점 더 먼저 말을 걸게 되었다'}"
            " -- 이 변화의 방향이 관계 역학의 실제 흐름.",
        )

# 발견 3: 응답시간 비대칭
if me_to_p and p_to_me:
    early_m2p = [gap for _, gap, p in me_to_p if p == "초기"]
    late_m2p = [gap for _, gap, p in me_to_p if p == "후기"]
    early_p2m = [gap for _, gap, p in p_to_me if p == "초기"]
    late_p2m = [gap for _, gap, p in p_to_me if p == "후기"]

    if early_m2p and late_m2p and early_p2m and late_p2m:
        avg_e_m2p = sum(early_m2p) / len(early_m2p)
        avg_l_m2p = sum(late_m2p) / len(late_m2p)
        avg_e_p2m = sum(early_p2m) / len(early_p2m)
        avg_l_p2m = sum(late_p2m) / len(late_p2m)

        add_discovery(
            "응답 속도의 시기별 역전",
            f"초기 - 정원이→이상규 응답: 평균 {avg_e_p2m:.0f}초 / 이상규→정원이 응답: 평균 {avg_e_m2p:.0f}초. "
            f"후기 - 정원이→이상규 응답: 평균 {avg_l_p2m:.0f}초 / 이상규→정원이 응답: 평균 {avg_l_m2p:.0f}초.",
            "응답 시간의 변화는 의식적 선택이 아니라 관계 안에서의 무의식적 거리 조절.",
            f"초기 대비 후기에 이상규의 응답 시간이 {avg_l_p2m/avg_e_p2m:.1f}배로 변했고, "
            f"정원이의 응답 시간은 {avg_l_m2p/avg_e_m2p:.1f}배로 변했다.",
        )

# 발견 4: ㅋㅋ 비교 (대상별)
add_discovery(
    "이상규의 웃음은 대상에 따라 완전히 다르다",
    f"ㅋㅋ 포함 메시지 비율 - 정원이에게: {r_kk_jw:.1f}% / 형에게: {r_kk_bro:.1f}% / 교수님에게: {r_kk_prof:.1f}%.",
    "같은 사람의 웃음 빈도가 대화 상대에 따라 이렇게까지 다르다.",
    f"{'형에게 가장 많이 웃고 정원이에게는 적다' if r_kk_bro > r_kk_jw else '정원이에게 가장 많이 웃는다'}"
    " -- 이상규가 어디서 가장 편하게 웃는지를 수치가 말해준다.",
)

# 발견 5: 메시지 길이 비교 (대상별)
add_discovery(
    "이상규의 메시지 길이는 대상별로 전혀 다른 사람",
    f"평균 메시지 길이 - 정원이에게: {avg_jw:.1f}자 / 교수님에게: {avg_prof:.1f}자 / 형에게: {avg_bro:.1f}자.",
    "같은 이상규가 보내는 메시지인데, 대상에 따라 완전히 다른 길이 분포. "
    "어떤 관계에서 더 '많은 말'을 하는지가 드러난다.",
    f"{'정원이에게 가장 길게 쓴다' if avg_jw > max(avg_prof, avg_bro) else '정원이에게 오히려 짧게 쓴다'}"
    " -- 길이가 곧 감정의 양이라면, 이 숫자가 의미하는 것.",
)

# 발견 6: 정원이 이모티콘 변화
if p_media_period:
    early_media = p_media_period["초기"]
    late_media = p_media_period["후기"]
    e_total = early_media["media"] + early_media["text"]
    l_total = late_media["media"] + late_media["text"]
    if e_total and l_total:
        e_rate = early_media["media"] / e_total * 100
        l_rate = late_media["media"] / l_total * 100
        add_discovery(
            "정원이의 이모티콘/사진 사용 변화",
            f"초기: 미디어 비율 {e_rate:.1f}% ({early_media['media']}/{e_total}) → "
            f"후기: {l_rate:.1f}% ({late_media['media']}/{l_total}).",
            "이모티콘과 사진은 관계의 '가벼운 터치' -- 이것이 줄어드는 것은 "
            "대화가 무거워지고 있다는 신호.",
            f"{'정원이의 미디어 사용이 후기에 줄었다' if l_rate < e_rate else '정원이의 미디어 사용이 오히려 늘었다'}"
            " -- 관계가 무거워졌는지 가벼워졌는지의 지표.",
        )

# 발견 7: 연속 메시지 폭탄 비대칭
if me_bursts and p_bursts:
    me_burst_avg = sum(len(b) for b in me_bursts) / len(me_bursts)
    p_burst_avg = sum(len(b) for b in p_bursts) / len(p_bursts)
    me_max_burst = max(len(b) for b in me_bursts)
    p_max_burst = max(len(b) for b in p_bursts)

    add_discovery(
        "이상규의 메시지 폭탄은 정원이의 몇 배인가",
        f"이상규 연속 메시지(1분 내 5개+): {len(me_bursts)}회, 평균 {me_burst_avg:.1f}개, 최대 {me_max_burst}개. "
        f"정원이: {len(p_bursts)}회, 평균 {p_burst_avg:.1f}개, 최대 {p_max_burst}개.",
        "연속으로 쏟아내는 메시지의 양이 대화에서의 '공간 점유'를 보여준다.",
        f"이상규가 정원이보다 {len(me_bursts)/len(p_bursts):.1f}배 더 자주 메시지 폭탄을 보낸다. "
        f"최대 연속도 {me_max_burst} vs {p_max_burst}개.",
    )

# 발견 8: 특정 단어 시기별 변화
# 사과 언어
sorry_me_counts = count_words(me_jw, ["죄송", "미안", "잘못"])
sorry_p_counts = count_words(partner_jw, ["죄송", "미안", "잘못"])

me_sorry_early = sum(sorry_me_counts[w].get("초기", 0) for w in ["죄송", "미안", "잘못"])
me_sorry_late = sum(sorry_me_counts[w].get("후기", 0) for w in ["죄송", "미안", "잘못"])
p_sorry_early = sum(sorry_p_counts[w].get("초기", 0) for w in ["죄송", "미안", "잘못"])
p_sorry_late = sum(sorry_p_counts[w].get("후기", 0) for w in ["죄송", "미안", "잘못"])

# 각 시기 메시지 수
me_early_cnt = sum(1 for dt, msg in me_jw if period_label(dt, jw_start, jw_end) == "초기")
me_late_cnt = sum(1 for dt, msg in me_jw if period_label(dt, jw_start, jw_end) == "후기")
p_early_cnt = sum(1 for dt, msg in partner_jw if period_label(dt, jw_start, jw_end) == "초기")
p_late_cnt = sum(1 for dt, msg in partner_jw if period_label(dt, jw_start, jw_end) == "후기")

add_discovery(
    "사과 언어의 비대칭 변화",
    f"'죄송/미안/잘못' 사용 - 이상규: 초기 {me_sorry_early}회(메시지 {me_early_cnt}건 중) → "
    f"후기 {me_sorry_late}회({me_late_cnt}건 중). "
    f"정원이: 초기 {p_sorry_early}회({p_early_cnt}건 중) → "
    f"후기 {p_sorry_late}회({p_late_cnt}건 중). "
    f"1000건당 비율: 이상규 초기 {me_sorry_early/me_early_cnt*1000:.1f} → 후기 {me_sorry_late/me_late_cnt*1000:.1f} / "
    f"정원이 초기 {p_sorry_early/p_early_cnt*1000:.1f} → 후기 {p_sorry_late/p_late_cnt*1000:.1f}.",
    "누가 더 많이 사과하는지, 그리고 그것이 시간에 따라 어떻게 변하는지.",
    "사과의 양이 곧 관계에서의 '죄책감 부담'의 위치를 알려준다.",
)

# 발견 9: 새벽 활동 비대칭
add_discovery(
    "새벽 대화 비율의 비대칭",
    f"00~05시 메시지 비율 - 이상규: {dawn_me_pct:.1f}% ({dawn_me}건) / 정원이: {dawn_p_pct:.1f}% ({dawn_p}건). "
    f"이상규 새벽 메시지 보낸 날: {len(after_3am_days)}일.",
    "새벽까지 대화하는 빈도가 관계에 투입하는 '수면 비용'을 보여준다.",
    f"이상규는 전체 메시지의 {dawn_me_pct:.1f}%를 새벽에 보낸다. "
    "이것은 선택이 아니라 패턴이다.",
)

# 발견 10: 질문 패턴
q_me_1000_early = q_me.get("초기", 0) / me_early_cnt * 1000 if me_early_cnt else 0
q_me_1000_late = q_me.get("후기", 0) / me_late_cnt * 1000 if me_late_cnt else 0
q_p_1000_early = q_p.get("초기", 0) / p_early_cnt * 1000 if p_early_cnt else 0
q_p_1000_late = q_p.get("후기", 0) / p_late_cnt * 1000 if p_late_cnt else 0

add_discovery(
    "질문의 방향이 바뀐다",
    f"물음표 사용 (1000건당) - 이상규: 초기 {q_me_1000_early:.1f} → 후기 {q_me_1000_late:.1f}. "
    f"정원이: 초기 {q_p_1000_early:.1f} → 후기 {q_p_1000_late:.1f}.",
    "질문은 '관심'의 형태다. 누가 더 물어보는지가 누가 더 알고 싶어하는지를 드러낸다.",
    "질문 빈도의 변화 방향이 관계에서 호기심의 이동 경로를 보여준다.",
)

# 발견 11: 정원이 메시지 길이 트렌드
monthly_keys = sorted(monthly_p_len.keys())
if len(monthly_keys) >= 2:
    first_month = monthly_keys[0]
    last_month = monthly_keys[-1]
    first_avg = sum(monthly_p_len[first_month]) / len(monthly_p_len[first_month])
    last_avg = sum(monthly_p_len[last_month]) / len(monthly_p_len[last_month])

    # 전체 트렌드 문자열
    trend_str = " / ".join(
        f"{m}: {sum(monthly_p_len[m])/len(monthly_p_len[m]):.1f}자"
        for m in monthly_keys
    )

    add_discovery(
        "정원이의 메시지가 점점 짧아지는가",
        f"정원이 월별 평균 메시지 길이: {trend_str}.",
        f"첫 달({first_month}) 평균 {first_avg:.1f}자 → 마지막 달({last_month}) 평균 {last_avg:.1f}자. "
        f"변화율: {((last_avg - first_avg) / first_avg * 100):.1f}%.",
        f"{'정원이의 메시지가 시간이 갈수록 짧아졌다' if last_avg < first_avg else '정원이의 메시지는 오히려 길어졌다'}"
        " -- 줄어드는 글자 수가 줄어드는 마음인지, 단순히 편해진 것인지.",
    )

# 발견 12: 통화 vs 텍스트 비율 변화
call_early = sum(1 for dt, _, _ in calls if period_label(dt, jw_start, jw_end) == "초기")
call_late = sum(1 for dt, _, _ in calls if period_label(dt, jw_start, jw_end) == "후기")
if call_early + call_late > 0:
    add_discovery(
        "통화 빈도의 시기별 변화",
        f"통화(보이스톡+페이스톡) - 초기: {call_early}건 / 후기: {call_late}건. "
        f"총 {len(calls)}건 중 이상규 시작 {len(call_me)}건, 정원이 시작 {len(call_p)}건.",
        "텍스트 대신 목소리를 선택하는 빈도가 친밀감의 다른 차원을 보여준다.",
        f"{'후기로 갈수록 통화가 줄었다' if call_late < call_early else '후기에 통화가 더 많아졌다'}"
        " -- 목소리로 연결되려는 욕구의 변화.",
    )

# 발견 13: 급변 지점과 이벤트 연결
if spikes_me:
    spike_data_lines = []
    for d, cnt, avg, ratio in spikes_me[:3]:
        spike_data_lines.append(f"{d}: {cnt}건 (평소 {avg:.1f}건의 {ratio:.1f}배)")

    add_discovery(
        "이상규의 메시지 폭증일",
        "평소 대비 급증한 날: " + " / ".join(spike_data_lines) + ".",
        "메시지가 갑자기 폭발하는 날은 '무언가가 일어난 날'이다. "
        "이 날짜들 주변에 무슨 일이 있었는지 기억해보라.",
        "평소의 2배 이상 메시지를 보낸 날은 감정적 사건의 지표. "
        "이상규의 감정이 가장 크게 움직인 날들의 목록.",
    )

# 발견 14: 감정어 비교 (대상별)
emotion_data = []
for w in emotion_words:
    c_jw = sum(1 for _, msg in me_jw if w in msg)
    c_prof = sum(1 for _, msg in me_prof if w in msg)
    c_bro = sum(1 for _, msg in me_bro if w in msg)
    r_jw = c_jw / len(me_jw) * 1000 if me_jw else 0
    r_prof = c_prof / len(me_prof) * 1000 if me_prof else 0
    r_bro = c_bro / len(me_bro) * 1000 if me_bro else 0
    if c_jw + c_prof + c_bro > 0:
        emotion_data.append((w, r_jw, r_prof, r_bro))

if emotion_data:
    emotion_str = " / ".join(
        f"'{w}': 정원 {r_jw:.1f} 교수 {r_prof:.1f} 형 {r_bro:.1f}"
        for w, r_jw, r_prof, r_bro in emotion_data
    )
    add_discovery(
        "이상규의 감정 언어는 정원이에게만 나온다",
        f"감정어 1000건당 빈도: {emotion_str}.",
        "같은 이상규인데 대화 상대에 따라 감정 단어의 출현 빈도가 완전히 달라진다.",
        "이상규가 정원이에게만 쓰는 단어들이 있다 -- 다른 관계에서는 존재하지 않는 언어.",
    )

# 발견 15: 대화 없는 날
all_date_range = set()
current = jw_start.date()
while current <= jw_end.date():
    all_date_range.add(current.strftime("%Y-%m-%d"))
    current += timedelta(days=1)

active_days = set(all_dates)
silent_days = sorted(all_date_range - active_days)

# 연속 무대화 구간
if silent_days:
    consecutive = []
    current_streak = [silent_days[0]]
    for i in range(1, len(silent_days)):
        prev = datetime.strptime(silent_days[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(silent_days[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            current_streak.append(silent_days[i])
        else:
            if len(current_streak) >= 1:
                consecutive.append(current_streak[:])
            current_streak = [silent_days[i]]
    if current_streak:
        consecutive.append(current_streak[:])

    longest = max(consecutive, key=len) if consecutive else []

    add_discovery(
        "완전한 침묵의 날들",
        f"총 대화 기간 {len(all_date_range)}일 중 대화 없는 날: {len(silent_days)}일 ({len(silent_days)/len(all_date_range)*100:.1f}%). "
        f"가장 긴 연속 무대화: {len(longest)}일 ({longest[0]}~{longest[-1]})." if longest else "",
        "매일 연락하는 관계에서 갑자기 며칠 사라지는 것은 단순한 바쁨이 아니다.",
        "연속 무대화 기간의 길이와 위치가 관계의 균열 지점을 정확히 가리킨다.",
    )

# ---- 보고서 쓰기 ----
report_path = os.path.expanduser(
    "~/pp/30p/runs/self/discoveries/01_kakao_patterns.md"
)
# 보고서가 이미 존재하면 덮어쓰지 않음 (수동 편집 보호)
if not os.path.exists(report_path) or os.path.getsize(report_path) == 0:
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n보고서 저장: {report_path}")
else:
    print(f"\n보고서 이미 존재 (덮어쓰지 않음): {report_path}")

print(f"총 {discovery_num}개 발견 기록됨.")
print("\n완료.")
