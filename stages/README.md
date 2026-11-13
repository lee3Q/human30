# 무대 카탈로그 (Stages)

`Human30`의 무대는 30명의 캐릭터가 동시에 놓이는 물리적·사회적 공간입니다. 각 무대는 고유한 **시선 노출도(`visibility`)**, **탈출 난이도(`escape_difficulty`)**, **감각 단서(`sensory_cues`)**를 가지며, 이 감각 단서는 캐릭터들의 트라우마 채널(`M7_trauma_trigger_channel`) 및 위협 반사(`M8_default_reflex`)와 상호작용합니다.

| ID | 무대명 | 영문명 | 감각 단서 | 노출도 |
|---|---|---|---|---|
| `S01` | 기숙 재수학원 대강당 | Boarding Prep Academy Auditorium | 형광등 소음, 소독약·분필 냄새, 밀폐된 공기, 출입문 잠김 | High |
| `S02` | 심야 정차된 지하철 객차 | Stopped Late-Night Subway Car | 비상등 붉은 불빛, 환기 장치 정지, 땀·체취, 금속 마찰음 | Medium |
| `S03` | 구조조정 태스크포스 대회의실 | Corporate Layoff Conference Room | 식이성 커피 향, 프로젝터 팬 소음, 유리벽 시선 노출, 에어컨 한기 | Extreme |
| `S04` | 폭우 고립 산장 대피소 | Isolated Storm Shelter | 양철 지붕 빗소리, 젖은 옷·흙냄새, 한기, 배터리 경고음 | Low Light |
| `S05` | 격리된 배심원 평의실 | Sequestered Jury Deliberation Room | 종이 넘기는 소리, 시계 초침 소리, 정적, 닫힌 중문 | High |

CLI에서 목록을 확인하려면:
```bash
python3 -m human30 catalog
```
