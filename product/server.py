#!/usr/bin/env python3
"""
카톡 → 발견 → 반박 웹앱 서버
stdlib만 사용. python3 server.py [--port 8000]

브라우저에서 http://localhost:8000 접속
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 같은 디렉토리 모듈
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import parse_file, parse_text, try_decode, detect_users, guess_me, analyze_all
from prompt import (
    SYSTEM_PROMPT,
    make_user_prompt,
    REBUTTAL_SYSTEM,
    make_rebuttal_prompt,
    DEEPER_SYSTEM,
    make_deeper_prompt,
)

# ============================================================
# 설정
# ============================================================

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

PRODUCT_DIR = os.path.dirname(os.path.abspath(__file__))

# 메모리 세션 저장소 (1시간 후 자동 만료)
SESSION_TTL_SECONDS = 3600
sessions = {}
sessions_created = {}  # session_id → creation timestamp


def cleanup_expired_sessions():
    """만료된 세션 정리"""
    now = datetime.now().timestamp()
    expired = [
        sid for sid, created in sessions_created.items()
        if now - created > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        sessions.pop(sid, None)
        sessions_created.pop(sid, None)


# ============================================================
# Claude API
# ============================================================

def call_claude(system: str, user_message: str) -> str:
    if not API_KEY:
        return '[{"title":"API 키 미설정","data":"ANTHROPIC_API_KEY 환경변수를 설정해주세요","meaning":"서버 시작 전에 export ANTHROPIC_API_KEY=sk-... 실행","surprise":"API 키 없이는 발견을 생성할 수 없습니다","question":"API 키를 설정하셨나요?"}]'

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
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        for block in data.get("content", []):
            if block.get("type") == "text":
                return block["text"]
    return ""


def parse_discoveries(text: str) -> list:
    import re
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    text = text.strip()
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return []



# ============================================================
# HTTP 핸들러
# ============================================================

class Handler(SimpleHTTPRequestHandler):
    # 정적 파일 MIME 매핑
    STATIC_FILES = {
        "/": ("index.html", "text/html"),
        "/index.html": ("index.html", "text/html"),
        "/manifest.json": ("manifest.json", "application/json"),
        "/sw.js": ("sw.js", "application/javascript"),
        "/icon.svg": ("icon.svg", "image/svg+xml"),
        "/icon-192.png": ("icon-192.png", "image/png"),
        "/icon-512.png": ("icon-512.png", "image/png"),
    }

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in self.STATIC_FILES:
            filename, content_type = self.STATIC_FILES[parsed.path]
            self.serve_file(filename, content_type)
        elif parsed.path == "/api/status":
            self.json_response({"ok": True, "has_api_key": bool(API_KEY)})
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/upload":
                self.handle_upload()
            elif parsed.path == "/api/discover":
                self.handle_discover()
            elif parsed.path == "/api/rebut":
                self.handle_rebut()
            elif parsed.path == "/api/deeper":
                self.handle_deeper()
            elif parsed.path == "/api/save":
                self.handle_save()
            else:
                self.send_error(404)
        except Exception as e:
            # 내부 에러 상세를 클라이언트에 노출하지 않음
            sys.stderr.write(f"[ERROR] {e}\n")
            self.json_response({"error": "처리 중 오류가 발생했습니다."}, status=500)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # 보안 헤더
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filename, content_type):
        filepath = os.path.join(PRODUCT_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error(404)
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(content)

    # ---- 업로드 + 분석 ----
    def handle_upload(self):
        # 만료 세션 정리
        cleanup_expired_sessions()

        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" in content_type:
            # multipart 파싱
            boundary = content_type.split("boundary=")[1].strip()
            body = self.read_body()
            csv_data, me_name = self._parse_multipart(body, boundary)
        else:
            # JSON body (파일 내용 직접)
            data = json.loads(self.read_body())
            csv_data = data.get("csv_content", "")
            me_name = data.get("me", "")

        # 메모리에서 직접 파싱 — 디스크에 저장하지 않음
        text = try_decode(csv_data)
        messages = parse_text(text)
        if not messages:
            self.json_response({"error": "메시지를 파싱할 수 없습니다."}, status=400)
            return

        user_counts = detect_users(messages)
        if me_name:
            # 확인
            if me_name not in user_counts:
                # 가장 비슷한 이름 찾기
                me_name = guess_me(user_counts)
        else:
            me_name = guess_me(user_counts)

        stats = analyze_all(messages, me_name)

        # 세션 생성 (메모리 전용, 디스크 저장 안 함)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = ts
        sessions[session_id] = {

            "stats": stats,
            "discoveries": [],
            "responses": [],
            "deeper_question": None,
            "deeper_answer": None,
        }
        sessions_created[session_id] = datetime.now().timestamp()

        # 사용자 목록 (선택용)
        users = [{"name": n, "count": c} for n, c in user_counts.most_common()]

        self.json_response({
            "session_id": session_id,
            "meta": stats["meta"],
            "users": users,
            "detected_me": me_name,
        })

    def _parse_multipart(self, body, boundary):
        """간단한 multipart/form-data 파서"""
        boundary_bytes = boundary.encode("utf-8") if isinstance(boundary, str) else boundary
        parts = body.split(b"--" + boundary_bytes)
        csv_data = b""
        me_name = ""

        for part in parts:
            if b"Content-Disposition" not in part:
                continue
            # 헤더와 바디 분리
            header_end = part.find(b"\r\n\r\n")
            if header_end == -1:
                continue
            headers = part[:header_end].decode("utf-8", errors="replace")
            content = part[header_end + 4:]
            # trailing \r\n 제거
            if content.endswith(b"\r\n"):
                content = content[:-2]

            if 'name="file"' in headers or 'name="csv"' in headers:
                csv_data = content
            elif 'name="me"' in headers:
                me_name = content.decode("utf-8", errors="replace").strip()

        return csv_data, me_name

    # ---- 발견 생성 ----
    def handle_discover(self):
        data = json.loads(self.read_body())
        session_id = data.get("session_id", "")

        if session_id not in sessions:
            self.json_response({"error": "세션을 찾을 수 없습니다."}, status=404)
            return

        session = sessions[session_id]

        # me 이름 변경 가능
        new_me = data.get("me", "")
        if new_me and new_me != session["stats"]["meta"]["me"]:
            # 재분석은 안 하고 meta만 뒤집기 (간이)
            pass

        stats_json = json.dumps(session["stats"], ensure_ascii=False)
        raw = call_claude(SYSTEM_PROMPT, make_user_prompt(stats_json))
        discoveries = parse_discoveries(raw)

        session["discoveries"] = discoveries
        session["responses"] = [{"action": "pending"} for _ in discoveries]

        self.json_response({
            "discoveries": discoveries,
            "count": len(discoveries),
        })

    # ---- 반박 처리 ----
    def handle_rebut(self):
        data = json.loads(self.read_body())
        session_id = data.get("session_id", "")
        index = data.get("index", 0)
        action = data.get("action", "skip")  # agree | rebut | skip
        text = data.get("text", "")

        if session_id not in sessions:
            self.json_response({"error": "세션 없음"}, status=404)
            return

        session = sessions[session_id]
        if index >= len(session["discoveries"]):
            self.json_response({"error": "인덱스 초과"}, status=400)
            return

        response = {"action": action, "text": text}

        followup = ""
        if action == "rebut" and text:
            discovery = session["discoveries"][index]
            followup = call_claude(
                REBUTTAL_SYSTEM,
                make_rebuttal_prompt(discovery, text),
            )
            response["followup"] = followup

        # 응답 저장
        while len(session["responses"]) <= index:
            session["responses"].append({"action": "pending"})
        session["responses"][index] = response

        self.json_response({
            "action": action,
            "followup": followup,
        })

    # ---- 깊은 질문 ----
    def handle_deeper(self):
        data = json.loads(self.read_body())
        session_id = data.get("session_id", "")
        answer = data.get("answer", "")

        if session_id not in sessions:
            self.json_response({"error": "세션 없음"}, status=404)
            return

        session = sessions[session_id]

        if not session.get("deeper_question"):
            # 첫 호출: 깊은 질문 생성
            question = call_claude(
                DEEPER_SYSTEM,
                make_deeper_prompt(session["discoveries"], session["responses"]),
            )
            session["deeper_question"] = question
            self.json_response({"question": question})
        else:
            # 답변 저장
            session["deeper_answer"] = answer
            self.json_response({"saved": True})

    # ---- 세션 내보내기 (디스크 저장 안 함 — 클라이언트에서 다운로드) ----
    def handle_save(self):
        data = json.loads(self.read_body())
        session_id = data.get("session_id", "")

        if session_id not in sessions:
            self.json_response({"error": "세션 없음"}, status=404)
            return

        session = sessions[session_id]
        save_data = {
            "meta": session["stats"]["meta"],
            "discoveries": session["discoveries"],
            "responses": session["responses"],
            "deeper_question": session.get("deeper_question"),
            "deeper_answer": session.get("deeper_answer"),
        }

        # 서버 디스크에 저장하지 않음 — 데이터를 클라이언트에 반환
        self.json_response({"session_data": save_data})

    def log_message(self, format, *args):
        # 깔끔한 로그
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}\n")


# ============================================================
# 메인
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="카톡 분석 웹앱 서버")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if not API_KEY:
        print("⚠️  ANTHROPIC_API_KEY 미설정. 발견 생성이 작동하지 않습니다.")
        print("   export ANTHROPIC_API_KEY=sk-ant-... 후 재시작하세요.")
        print()

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"🌐 서버 시작: http://localhost:{args.port}")
    print(f"   Ctrl+C로 종료")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료.")
        server.server_close()


if __name__ == "__main__":
    main()
