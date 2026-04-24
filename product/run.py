#!/usr/bin/env python3
"""
카톡 → 발견 → 반박 루프   MVP
stdlib만 사용. Claude API 호출은 urllib.

사용법:
  python3 run.py <카톡.csv> [--me 이름] [--api-key KEY]

환경변수 ANTHROPIC_API_KEY가 있으면 --api-key 생략 가능.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# 같은 디렉토리의 모듈
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import parse_file, detect_users, guess_me, analyze_all
from prompt import (
    SYSTEM_PROMPT,
    make_user_prompt,
    REBUTTAL_SYSTEM,
    make_rebuttal_prompt,
    DEEPER_SYSTEM,
    make_deeper_prompt,
)


# ============================================================
# Claude API 호출 (urllib, stdlib only)
# ============================================================

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


def call_claude(system: str, user_message: str, api_key: str) -> str:
    """Claude API 호출 → 텍스트 응답 반환"""
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system,
        "messages": [{"role": "user", "content": user_message}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # content 배열에서 text 추출
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return ""
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"\n[API 오류] {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


def parse_discoveries(text: str) -> list:
    """LLM 응답에서 JSON 배열 추출"""
    # ```json ... ``` 블록이 있으면 그 안의 내용을 추출
    import re
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    # 또는 직접 배열인 경우
    text = text.strip()
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    # 마지막 시도: 전체 텍스트에서 [ ... ] 추출
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    print(f"\n[경고] 발견 JSON 파싱 실패. 원본:\n{text[:500]}", file=sys.stderr)
    return []


# ============================================================
# 터미널 UI
# ============================================================

DIVIDER = "─" * 50


def print_header():
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   카톡 → 발견 → 반박   MVP                  ║")
    print("║   카톡을 넣으면, 네가 몰랐던 너를 보여준다   ║")
    print("╚══════════════════════════════════════════════╝")
    print()


def print_discovery(i, total, d):
    print(f"\n{DIVIDER}")
    print(f"  발견 {i}/{total} — {d.get('title', '?')}")
    print(DIVIDER)
    print(f"\n  📊 데이터: {d.get('data', '?')}")
    print(f"\n  💡 의미: {d.get('meaning', '?')}")
    print(f"\n  ❗ 놀라운 이유: {d.get('surprise', '?')}")
    if d.get("question"):
        print(f"\n  ❓ {d['question']}")
    print()


def get_response():
    """사용자 응답 받기: 동의/반박/건너뛰기"""
    while True:
        print("  [1] 동의  [2] 반박  [3] 건너뛰기  [q] 종료")
        try:
            choice = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit", ""

        if choice == "1":
            return "agree", ""
        elif choice == "2":
            print("\n  반박 내용을 적어주세요 (Enter로 완료):")
            try:
                text = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return "quit", ""
            return "rebut", text
        elif choice == "3":
            return "skip", ""
        elif choice.lower() == "q":
            return "quit", ""
        else:
            print("  1, 2, 3, q 중 선택해주세요.")


# ============================================================
# 세션 저장
# ============================================================

def save_session(session_dir, meta, discoveries, responses, deeper_question=None):
    """세션 결과를 JSON + Markdown으로 저장"""
    os.makedirs(session_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON (기계용)
    session_data = {
        "timestamp": ts,
        "meta": meta,
        "discoveries": discoveries,
        "responses": responses,
        "deeper_question": deeper_question,
    }
    json_path = os.path.join(session_dir, f"session_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    # Markdown (사람용)
    md_lines = [
        f"# 카톡 분석 세션 — {ts}",
        f"",
        f"- 나: {meta['me']} ({meta['me_messages']}건)",
        f"- 상대: {meta['partner']} ({meta['other_messages']}건)",
        f"- 기간: {meta['start_date']} ~ {meta['end_date']}",
        f"",
    ]

    for i, (d, r) in enumerate(zip(discoveries, responses)):
        action = r.get("action", "skip")
        md_lines.append(f"## 발견 {i+1} — {d.get('title', '?')}")
        md_lines.append(f"")
        md_lines.append(f"- 데이터: {d.get('data', '?')}")
        md_lines.append(f"- 의미: {d.get('meaning', '?')}")
        md_lines.append(f"- 놀라운 이유: {d.get('surprise', '?')}")
        md_lines.append(f"")
        if action == "agree":
            md_lines.append(f"→ **동의**")
        elif action == "rebut":
            md_lines.append(f"→ **반박**: {r.get('text', '')}")
            if r.get("followup"):
                md_lines.append(f"→ **후속**: {r['followup']}")
        else:
            md_lines.append(f"→ *건너뜀*")
        md_lines.append(f"")

    if deeper_question:
        md_lines.append(f"## 깊은 질문")
        md_lines.append(f"")
        md_lines.append(deeper_question)

    md_path = os.path.join(session_dir, f"session_{ts}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return json_path, md_path


# ============================================================
# 메인
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="카톡 → 발견 → 반박 루프")
    parser.add_argument("csv_path", help="카톡 CSV 파일 경로")
    parser.add_argument("--me", help="내 이름 (미지정 시 자동 감지)")
    parser.add_argument("--api-key", help="Anthropic API 키 (또는 ANTHROPIC_API_KEY 환경변수)")
    parser.add_argument("--session-dir", default=None, help="세션 저장 디렉토리")
    args = parser.parse_args()

    # API 키
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY 환경변수를 설정하거나 --api-key를 지정해주세요.", file=sys.stderr)
        sys.exit(1)

    # 파일 확인
    csv_path = os.path.expanduser(args.csv_path)
    if not os.path.exists(csv_path):
        print(f"파일 없음: {csv_path}", file=sys.stderr)
        sys.exit(1)

    print_header()

    # ---- Phase 1: 파싱 ----
    print("📁 카톡 파싱 중...")
    messages = parse_file(csv_path)
    if not messages:
        print("메시지가 없습니다.", file=sys.stderr)
        sys.exit(1)
    print(f"   {len(messages)}개 메시지 로드 완료")

    # 사용자 감지
    user_counts = detect_users(messages)
    if args.me:
        me_name = args.me
    else:
        me_name = guess_me(user_counts)
    other_names = [n for n, _ in user_counts.most_common() if n != me_name]
    partner_name = other_names[0] if other_names else "상대"

    print(f"   나: {me_name} ({user_counts[me_name]}건)")
    for n in other_names:
        print(f"   상대: {n} ({user_counts[n]}건)")

    # ---- Phase 2: 통계 분석 ----
    print("\n📊 통계 분석 중...")
    stats = analyze_all(messages, me_name)
    stats_json = json.dumps(stats, ensure_ascii=False)
    print(f"   분석 완료 (데이터 {len(stats_json)} bytes)")

    # ---- Phase 3: LLM 발견 생성 ----
    print("\n🔍 패턴에서 발견 추출 중... (Claude API 호출)")
    raw_response = call_claude(
        SYSTEM_PROMPT,
        make_user_prompt(stats_json),
        api_key,
    )
    discoveries = parse_discoveries(raw_response)
    if not discoveries:
        print("발견 생성 실패. 원본 응답:")
        print(raw_response[:1000])
        sys.exit(1)
    print(f"   {len(discoveries)}개 발견 생성 완료")

    # ---- Phase 4: 반박 루프 ----
    print(f"\n{DIVIDER}")
    print(f"  {len(discoveries)}개 발견을 하나씩 보여드립니다.")
    print(f"  각 발견에 동의, 반박, 또는 건너뛸 수 있습니다.")
    print(f"  반박은 그 자체가 데이터입니다.")
    print(DIVIDER)

    responses = []
    for i, d in enumerate(discoveries, 1):
        print_discovery(i, len(discoveries), d)

        action, text = get_response()
        if action == "quit":
            print("\n세션 종료.")
            break

        response = {"action": action, "text": text}

        if action == "rebut" and text:
            print("\n  💬 반박 반영 중...")
            followup = call_claude(
                REBUTTAL_SYSTEM,
                make_rebuttal_prompt(d, text),
                api_key,
            )
            print(f"\n  {followup}")
            response["followup"] = followup

        responses.append(response)

    # ---- Phase 5: 깊은 질문 ----
    deeper_question = None
    if len(responses) >= 3:
        print(f"\n{DIVIDER}")
        print("  세션 종합 중...")
        print(DIVIDER)

        deeper_question = call_claude(
            DEEPER_SYSTEM,
            make_deeper_prompt(discoveries[:len(responses)], responses),
            api_key,
        )
        print(f"\n  🔥 깊은 질문:")
        print(f"  {deeper_question}")

        # 사용자 답변 받기
        print(f"\n  답하고 싶으면 적어주세요 (Enter로 건너뛰기):")
        try:
            deep_answer = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            deep_answer = ""

        if deep_answer:
            deeper_question += f"\n\n사용자 답변: {deep_answer}"

    # ---- Phase 6: 저장 ----
    session_dir = args.session_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sessions"
    )
    json_path, md_path = save_session(
        session_dir, stats["meta"], discoveries, responses, deeper_question
    )

    print(f"\n{DIVIDER}")
    print(f"  세션 저장 완료")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(DIVIDER)
    print()


if __name__ == "__main__":
    main()
