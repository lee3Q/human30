# Human30 빠른 시작 가이드 (1분 실행)

`Human30`은 **외부 패키지 설치나 유료 API 키 없이** Python 3.11+ 표준 라이브러리만으로 즉시 실행됩니다.

---

## 1. 인터랙티브 웹 스튜디오 실행 (가장 추천)

```bash
python3 -m human30 studio --port 8000
```

브라우저에서 **http://127.0.0.1:8000** 을 열면:
- **01. 군상 탐색 & 차트**: 30명의 임상 차트 열람, 새로운 시드 생성, 특이 케이스(고ACE+고IQ, 외모 1위, 디지털 강박 등) 필터링
- **02. 무대 시뮬레이터 & 4-렌즈**: 5개 무대 × 6개 시나리오(무기명 투표, 기명 공개 투표, 만장일치 딜레마 등) 즉시 시뮬레이션, `Surface`/`X-Ray`/`Phone`/`Subconscious` 4-렌즈 비교, **1:1 캐릭터 심문**
- **03. 반사실적 단일축 실험실**: 특정 캐릭터의 `body`/`memory`/`identity`/`world_model` 중 1개 축만 바꾸어 행동 변화 비교
- **04. 포터블 프롬프트 번들**: Claude, ChatGPT, Gemini에 바로 붙여넣을 수 있는 단일 프롬프트 생성

---

## 2. 터미널 CLI로 실행

```bash
# 1) 새 코호트 생성 (예: 시드 7)
python3 -m human30 generate 7

# 2) 30명 1줄 요약 및 특이 케이스 탐지
python3 -m human30 summary 1

# 3) 특정 캐릭터(예: 9번) 임상 차트 카드 보기
python3 -m human30 card 1 9

# 4) 무대 시뮬레이션 즉시 실행 (시드 1 × 기숙학원 강당 × 무기명 퇴출 투표)
python3 -m human30 simulate --seed 1 --stage S01 --scenario SC01 --char 9

# 5) 5회 반복 실행으로 구조적 표적 수렴(분산) 확인
python3 -m human30 simulate --seed 1 --stage S01 --scenario SC01 --runs 5

# 6) 캐릭터 1:1 심문 (입으로 하는 말 vs 실제 X-Ray 속마음 대조)
python3 -m human30 interrogate 1 9 "왜 21번에게 투표했나요?"

# 7) 반사실적 단일축 실험 (9번 캐릭터의 memory 층만 변이)
python3 -m human30 counterfactual --seed 1 --char 9 --axis memory
```
