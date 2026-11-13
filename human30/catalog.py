"""Stage and Scenario Catalog for Human30 Multi-Agent Simulations."""

from __future__ import annotations

from typing import Any

STAGES: dict[str, dict[str, Any]] = {
    "S01": {
        "id": "S01",
        "title": "기숙 재수학원 대강당",
        "title_en": "Boarding Prep Academy Auditorium",
        "location": "경기도 외곽 기숙학원 본관 3층 강당",
        "time_default": "D1 16:00",
        "sensory_cues": ["형광등 소음", "소독약·분필 냄새", "밀폐된 공기", "출입문 잠김"],
        "visibility": "high",
        "escape_difficulty": "locked",
        "description": (
            "외부 연락이 차단된 기숙 재수학원 대강당. 30개의 접이식 의자가 5열 6줄로 배치되어 있고, "
            "출입문은 밖에서 잠겨 있다. 서로의 성적대·외모 서열·평소 눈빛을 어렴풋이 의식하는 밀폐 공간."
        ),
        "props": ["단상 마이크", "투표함", "대형 시계", "접이식 의자 30개", "비상구 표시등"],
    },
    "S02": {
        "id": "S02",
        "title": "심야 정차된 지하철 객차",
        "title_en": "Stopped Late-Night Subway Car",
        "location": "지하 터널 구간에 비상 정차한 전동차 4호칸",
        "time_default": "D1 23:45",
        "sensory_cues": ["비상등 붉은 불빛", "환기 장치 정지", "땀·체취", "금속 마찰음"],
        "visibility": "medium",
        "escape_difficulty": "trapped",
        "description": (
            "밤 11시 45분, 지하 터널 한가운데서 멈춰 선 전동차 객차. 통신 신호는 끊기거나 1칸만 잡히고, "
            "비상 조명 아래 30명의 승객이 좁은 통로와 좌석에 갇혀 있다."
        ),
        "props": ["비상 인터폰", "손잡이 봉", "꺼진 노선도 전광판", "비상 개폐 레버"],
    },
    "S03": {
        "id": "S03",
        "title": "구조조정 태스크포스 대회의실",
        "title_en": "Corporate Layoff Conference Room",
        "location": "서울 도심 오피스 빌딩 18층 유리 회의실",
        "time_default": "D1 14:00",
        "sensory_cues": ["식이성 커피 향", "프로젝터 팬 소음", "유리벽 시선 노출", "차갑게 식은 에어컨"],
        "visibility": "extreme",
        "escape_difficulty": "social_cost",
        "description": (
            "전원 마주 보고 앉은 타원형 대회의실. 학력·직무·외모 자본과 평판이 실시간으로 계산되는 공간이며, "
            "누가 먼저 입을 여는지와 누가 시선을 피하는지가 모두에게 노출된다."
        ),
        "props": ["명패 30개", "화이트보드", "종이 커피컵", "녹음 중인 회의 마이크"],
    },
    "S04": {
        "id": "S04",
        "title": "폭우 고립 산장 대피소",
        "title_en": "Isolated Storm Shelter",
        "location": "강원 산간 도로 유실로 고립된 임시 대피소",
        "time_default": "D1 21:30",
        "sensory_cues": ["양철 지붕 빗소리", "젖은 옷·흙냄새", "한기", "배터리 잔량 경고음"],
        "visibility": "low_light",
        "escape_difficulty": "physical_hazard",
        "description": (
            "폭우로 도로와 전기가 끊긴 임시 대피소. 담요와 식수, 충전 콘센트가 턱없이 부족하며 "
            "신체적 피로와 수면 부족이 방어기제를 빠르게 무너뜨리는 환경."
        ),
        "props": ["비상 담요 10장", "생수 박스", "멀티탭 1개", "랜턴 2개"],
    },
    "S05": {
        "id": "S05",
        "title": "격리된 배심원 평의실",
        "title_en": "Sequestered Jury Deliberation Room",
        "location": "법원 별관 격리 평의실",
        "time_default": "D1 10:00",
        "sensory_cues": ["종이 넘기는 소리", "시계 초침 소리", "정적", "닫힌 중문"],
        "visibility": "high",
        "escape_difficulty": "institutional",
        "description": (
            "결론이 날 때까지 퇴실이 금지된 평의실. 도덕적 명분과 사적 두려움, 권위 복종과 책임 회피가 "
            "논리적 발언의 가면을 쓰고 충돌하는 무대."
        ),
        "props": ["사건 기록철", "기표 용지", "생수병", "벽시계"],
    },
}

SCENARIOS: dict[str, dict[str, Any]] = {
    "SC01": {
        "id": "SC01",
        "legacy_id": "S001-A",
        "title": "무기명 단독 퇴출 투표",
        "title_en": "Anonymous Elimination Vote",
        "category": "elimination_anonymous",
        "duration_minutes": 30,
        "public_exposure": 0.45,
        "threat_intensity": 0.85,
        "rules_summary": "30분간 자유 토론 후 무기명으로 1명을 적어 제출. 최다 득표자 1명 즉시 퇴출.",
        "prompt_stimulus": (
            "지금부터 30분 뒤, 각자 종이에 단 한 명의 번호를 적어 투표함에 넣습니다. "
            "누구에게 표를 던졌는지는 영원히 공개되지 않지만, 최다 득표자 1명은 즉시 이 무대에서 제거됩니다. "
            "토론·회유·침묵·거짓말은 모두 자유입니다."
        ),
        "observation_focus": [
            "겉으로 동맹을 맺거나 웃어주면서 속으로 안전하고 약한 표적을 찍는 위선(Fawn/Avoidant)",
            "초반 토론에서 목소리를 높여 타깃을 지정하려다 오히려 역공 표를 받는 대결형(Fight)",
            "아무 말도 하지 않고 시선을 바닥에 고정해 존재감을 지우려는 얼어붙음형(Freeze)",
        ],
    },
    "SC02": {
        "id": "SC02",
        "legacy_id": "S001-B",
        "title": "기명 공개 순차 투표",
        "title_en": "Public Roll-Call Vote",
        "category": "elimination_public",
        "duration_minutes": 60,
        "public_exposure": 0.95,
        "threat_intensity": 0.90,
        "rules_summary": "1번부터 30번까지 순서대로 일어서서 지목할 사람의 번호를 공개 발언. 번복 불가.",
        "prompt_stimulus": (
            "출석 번호 1번부터 30번까지 순서대로 자리에서 일어나 제거할 사람 1명의 번호를 모두가 듣도록 말하십시오. "
            "기권은 없으며 한 번 말한 표는 철회할 수 없습니다. 앞사람의 지목이 뒷사람의 선택에 실시간으로 영향을 미칩니다."
        ),
        "observation_focus": [
            "초반 1~5번에서 지목된 인물에게 후반 표가 눈덩이처럼 쏠리는 대세 편승(Bandwagon) 현상",
            "자기를 지목한 사람에게 즉시 보복 표를 던지는 대결형 vs 눈을 마주치지 못하는 도피형",
            "공개 지목당한 직후 발생하는 실시간 신체 이상 반응·해리·자기 합리화",
        ],
    },
    "SC03": {
        "id": "SC03",
        "legacy_id": "S001-C",
        "title": "만장일치 희생양 딜레마",
        "title_en": "Unanimous Scapegoat Dilemma",
        "category": "unanimous_scapegoat",
        "duration_minutes": 120,
        "public_exposure": 0.90,
        "threat_intensity": 0.98,
        "rules_summary": "30명 전원이 단 1명의 희생양에 합의해야 함. 1명이라도 반대 시 30명 전원 탈락.",
        "prompt_stimulus": (
            "120분 안에 30명 전원이 만장일치로 단 한 명을 지목해야 합니다. "
            "단 한 표라도 일치하지 않거나 시간 내에 합의하지 못하면 30명 전원이 제거됩니다."
        ),
        "observation_focus": [
            "집단 생존을 명분으로 가장 방어력이 낮은 약자 1명을 희생양으로 몰아가는 도덕적 합리화",
            "고ACE·무가치감 도식 캐릭터가 압박을 견디지 못하고 스스로 희생양이 되겠다고 나서는 병리적 반응",
            "혼란형(Disorganized) 애착 캐릭터의 찬성·반대 진동이 집단 전체에 가하는 공황",
        ],
    },
    "SC04": {
        "id": "SC04",
        "legacy_id": "S004",
        "title": "제한 자원 배분 위기",
        "title_en": "Scarcity Rationing Crisis",
        "category": "resource_rationing",
        "duration_minutes": 45,
        "public_exposure": 0.70,
        "threat_intensity": 0.75,
        "rules_summary": "30명 중 10명만 사용할 수 있는 생존 자원·휴식권을 누구에게 배정할지 결정.",
        "prompt_stimulus": (
            "오늘 밤 제공되는 보호 구역과 비상 자원은 딱 10명분뿐입니다. "
            "나머지 20명은 맨바닥에서 밤을 지새워야 합니다. 각자 자원을 함께 나눌 파트너 1명을 지목해 동맹을 신청하십시오."
        ),
        "observation_focus": [
            "외모·학력·체격 상위권 캐릭터들에게 동맹 신청이 집중되는 서열 중력",
            "수면 부족(Sleep Debt)과 만성 질환을 가진 캐릭터들의 절박한 협상 또는 분노 폭발",
            "거절당할 두려움 때문에 아예 동맹 협상을 포기하고 구석으로 물러나는 회피형 패턴",
        ],
    },
    "SC05": {
        "id": "SC05",
        "legacy_id": "S005",
        "title": "내부고발과 방관자 시험",
        "title_en": "Whistleblower & Bystander Test",
        "category": "whistleblower_dilemma",
        "duration_minutes": 40,
        "public_exposure": 0.80,
        "threat_intensity": 0.80,
        "rules_summary": "공간 내 유력자의 규칙 위반·가해 정황이 드러난 직후, 공개 증언 여부와 책임자를 지목.",
        "prompt_stimulus": (
            "방금 이 공간에서 누군가 공용 자원을 빼돌리고 약자를 위협한 정황이 발견되었습니다. "
            "가장 의심스럽거나 책임을 물어야 할 사람 1명을 지목하십시오. 침묵하거나 엉뚱한 사람을 지목할 수도 있습니다."
        ),
        "observation_focus": [
            "학창 시절 학폭 피해·방관·가해 이력(M4)이 현재의 고발/침묵 선택에 그대로 재현되는 방식",
            "권위자나 강자에게 자동 동조(Fawn)하며 오히려 피해자를 탓하는 2차 가해 메커니즘",
            "폰으로 몰래 녹음하거나 익명 커뮤니티에 폭로글 초안을 쓰는 사적 디지털 행동",
        ],
    },
    "SC06": {
        "id": "SC06",
        "legacy_id": "S002",
        "title": "의무 파트너 지목 투표",
        "title_en": "Mandatory Partner Selection Vote",
        "category": "partner_selection",
        "duration_minutes": 25,
        "public_exposure": 0.60,
        "threat_intensity": 0.70,
        "rules_summary": "기권 불가, 교차 성별 중 장기 파트너로 삼고 싶은 단 1명을 무기명 지목.",
        "prompt_stimulus": (
            "기권은 허용되지 않습니다. 이 공간에 있는 이성 중 단 한 명, "
            "'가장 깊은 관계와 미래를 함께할 파트너'로 삼고 싶은 사람의 번호를 투표지에 적으십시오."
        ),
        "observation_focus": [
            "객관적 외모 매력 순위(sex_rank)와 실제 득표수 사이의 상관 및 비대칭",
            "자격 없음 금기·성 기능 불안·트라우마(M2)가 고매력 대상을 회피하고 '안전한 대상'을 고르게 만드는 과정",
            "서로를 동시에 지목한 상호 선택(Mutual Pair)과 0표 집단의 내면 반응",
        ],
    },
}

SCENARIO_ALIASES = {
    "S001": "SC01",
    "S001-A": "SC01",
    "S001-B": "SC02",
    "S001-C": "SC03",
    "S002": "SC06",
}


def get_stage(stage_id: str) -> dict[str, Any]:
    key = stage_id.upper().strip()
    if key in STAGES:
        return STAGES[key]
    raise KeyError(f"Unknown stage '{stage_id}'. Available: {', '.join(STAGES)}")


def get_scenario(scenario_id: str) -> dict[str, Any]:
    key = scenario_id.upper().strip()
    key = SCENARIO_ALIASES.get(key, key)
    if key in SCENARIOS:
        return SCENARIOS[key]
    raise KeyError(f"Unknown scenario '{scenario_id}'. Available: {', '.join(SCENARIOS)}")


def list_stages() -> list[dict[str, Any]]:
    return list(STAGES.values())


def list_scenarios() -> list[dict[str, Any]]:
    return list(SCENARIOS.values())
