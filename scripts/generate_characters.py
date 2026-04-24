"""
30명 캐릭터의 풀 프로필 생성.

data/personas.json (1층: 동기/두려움)을 읽고
LLM에게 추가 속성(집안/신체/성격/컨디션)을 채우게 한다.
결과는 data/characters.json에 저장.

사용법:
    cd ~/pp/lab/cls30
    uv run python scripts/generate_characters.py

비용: Sonnet 4.6 1회 호출, 약 $0.05~0.20 추정.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PERSONAS_FILE = DATA / "personas.json"
CHARACTERS_FILE = DATA / "characters.json"


SYSTEM_PROMPT = """\
너는 한 사고실험의 캐릭터 디자이너다.

목표: 30명의 18세 인간을 디자인한다. 이들은 사회화의 외피를 벗긴 상태로
시뮬레이션된다 — 도덕, 예의, 체면, 자제심이 행동을 막지 않는 인간. 자신의
동기와 두려움에만 따라 움직이는 인간.

입력으로 30명 각자의 1층(내면의 목소리, 핵심 동기, 근원적 두려움)이 주어진다.

각 캐릭터마다 다음 4개 속성을 채워라. 캐릭터의 동기/두려움과 *내적으로 일관성*
있고 *인과적으로 그럴듯하게* — 즉, "왜 이런 동기를 가지게 됐는가"가 자연스럽게
설명되도록 — 설계해라:

1. family (집안 환경): 1~2문장. 부모/형제/경제/분위기 중 핵심만. 클리셰 피하기.
   동기/두려움의 *기원*이 보이게.
2. body (신체): 1문장. 키/체격/특이점. 미화하지도 비하하지도 말 것. 사실적으로.
3. traits (성격 특질): 한국어 단어/구 3~4개를 배열로. 동기/두려움과 일관성 있되
   너무 뻔하지 않게. 예: ["과민함", "관찰자 시선", "갑작스런 충동"]
4. condition (시작 컨디션): 1문장. 시뮬레이션이 시작되는 순간의 즉각적 상태 —
   졸림/허기/긴장/평안/짜증/들뜸/멍함 등. 30명이 *서로 다른 상태*로 시작하게 분배.

중복 회피: 30명이 서로 다른 집안과 몸과 컨디션을 갖게 해라. 빈곤과 부유,
화목과 파편, 마름과 통통, 건강과 병약 — 다양하게.

사회화 없음 원칙: 이들의 자제심/도덕은 *시뮬레이션 단계에서* 시스템 프롬프트로
제거된다. 디자인 단계에서는 그들의 동기/두려움의 *기원과 토양*을 만든다고
생각해라.

반드시 다음 JSON 형식으로만 응답해라. 다른 텍스트 없이:

```json
{
  "characters": [
    {
      "id": 1,
      "family": "...",
      "body": "...",
      "traits": ["...", "...", "..."],
      "condition": "..."
    },
    ... 30명 ...
  ]
}
```
"""


def extract_json(text: str) -> str:
    """LLM 응답에서 JSON 본문만 뽑는다."""
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    return text.strip()


def main() -> None:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY가 설정되지 않았다. .env를 확인해라.")

    if not PERSONAS_FILE.exists():
        sys.exit(f"{PERSONAS_FILE}가 없다.")

    personas = json.loads(PERSONAS_FILE.read_text(encoding="utf-8"))
    print(f"1층 데이터 로드: {len(personas)}명")

    user_prompt = (
        "다음 30명의 1층이다. 각자의 4개 속성을 채워라:\n\n"
        + json.dumps(personas, ensure_ascii=False, indent=2)
    )

    model = os.environ.get("CLS30_MODEL", "claude-sonnet-4-6")
    client = Anthropic(api_key=api_key)
    print(f"모델: {model}")
    print("호출 중... (수십 초 소요 가능)")

    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = "".join(b.text for b in resp.content if b.type == "text")
    payload = extract_json(text)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        debug = ROOT / "data" / "_last_response.txt"
        debug.write_text(text, encoding="utf-8")
        sys.exit(f"JSON 파싱 실패: {e}\n원본 응답을 저장했다: {debug}")

    if "characters" not in data:
        sys.exit(f"응답에 'characters' 키 없음: {payload[:200]}")

    additions = {c["id"]: c for c in data["characters"]}
    if len(additions) != 30:
        sys.exit(f"30명이 아님: {len(additions)}명 생성됨")

    merged = []
    for p in personas:
        a = additions.get(p["id"])
        if not a:
            sys.exit(f"id {p['id']} 누락")
        merged.append({
            **p,
            "family": a["family"],
            "body": a["body"],
            "traits": a["traits"],
            "condition": a["condition"],
        })

    DATA.mkdir(exist_ok=True)
    CHARACTERS_FILE.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"저장: {CHARACTERS_FILE}")
    print(f"입력 토큰: {resp.usage.input_tokens}, 출력 토큰: {resp.usage.output_tokens}")
    print()
    print("샘플 (3명):")
    print()
    for c in merged[:3]:
        print(f"  #{c['id']:02d} \"{c['voice']}\"  ({c['domain']})")
        print(f"      집안   : {c['family']}")
        print(f"      신체   : {c['body']}")
        print(f"      특질   : {', '.join(c['traits'])}")
        print(f"      컨디션 : {c['condition']}")
        print()


if __name__ == "__main__":
    main()
