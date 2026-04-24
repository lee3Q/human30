# 30p 생성 프로토콜 (Generation Protocol)

> **대상**: `scripts/generate_seed.py` (stdlib-only Python). Claude는 호출·결과 검수만.
> **의존성 정책 재정의 (2026-04-08)**: 외부 패키지 0. 언어 무관. 공급망 공격 방어가 원칙이지 파이썬 기피 아님.
> 입력: 시드 번호(정수). 출력: `runs/seed_NNN.json` (30명 캐릭터 풀 프로필).
>
> **사용**: `python3 scripts/generate_seed.py 1` → `runs/seed_001.json` 생성. `random.seed(1)` 고정으로 **비트 단위 재현** 가능.
> 검증: `python3 scripts/verify_seed.py 1` | 요약: `python3 scripts/summarize_seed.py 1`

---

## 사용자 호출 형태

사용자가 *"시드 N으로 굴려"*라고 하면 Claude는:
```
python3 scripts/generate_seed.py N
```
을 실행하고 `runs/seed_NNN.json` 확인. 그 다음 `summarize_seed.py`로 30명 요약 + 특이 케이스 보고.

성비 / 나이 / 지역 오버라이드는 script 확장으로 처리 (현재 v0.1은 기본값 M15/F15/20세/한국 고정).

**현재 script 구현 범위**:
- 4층 28표 독립 샘플링
- M2 발생 시 M7 최소 1채널 보장 (유일한 cross-layer 상관)
- B2 sex_rank post-hoc 계산
- personas 30개에서 랜덤 2개 사후 라벨

정교한 상관(M9 climate ↔ M1 ACE, I1 g ↔ K1 tier 등)은 v0.2에서 첫 시뮬 결과 보고 결정.

---

## 0. 재현성 정책

- **같은 시드 = 같은 결과물** 원칙은 *저장된 JSON으로 확보*한다 (비트 단위 재현 아님)
- 시드 N에 대해 처음 호출되면 → 30명 굴림 → `runs/seed_N.json` 저장
- 이미 `runs/seed_N.json`이 존재하면 → 굴림 없이 해당 파일을 로드하여 사용
- **재굴림 필요 시** 사용자가 명시적으로 *"시드 N 재굴림"* 또는 파일 삭제 후 호출

시드 번호 자체는 Claude의 추론에 *무드 파라미터*로 작동한다. 시드 1과 시드 42는 *다른 분포의 30명*을 내보내게 된다. 완벽한 결정론은 아니지만 *결과물 저장*으로 실용적 재현성 충족.

---

## 1. 입력 해석

사용자가 호출한 시드 문자열에서 추출:
- `seed`: 정수 (예: 1, 42)
- `sex_ratio`: 기본 {M: 15, F: 15}, 사용자가 지정하면 오버라이드
- `special_constraints`: 예외 조건 리스트 (예: "한국 외 2명")

---

## 2. 옵션 표 4층 로드

순서대로 Read:
1. `tables/body.json` (11 서브테이블)
2. `tables/memory.json` (11 서브테이블)
3. `tables/identity.json` (3 서브테이블)
4. `tables/korea.json` (3 서브테이블)

4층 전부 메모리에 있어야 굴림 가능.

---

## 3. 캐릭터 30명 굴림 순서

각 캐릭터(id 1~30)를 순차적으로 굴리되, **한 캐릭터 안에서는 아래 층 순서를 지킨다** (상호작용 때문).

### 3.1 Body 층 (신체 — 가장 먼저)

1. `sex` 결정 (남 또는 여, 성비 맞춤)
2. `B1_height`: 분포에서 굴림 (M 173.7±5.7 / F 160.9±5.3)
3. `B2_face_attractiveness`: 1~10 점수 + 성별 내 서열 (30명 모두 굴린 후 재계산)
4. `B3_body_composition`: bmi, muscle_mass, grip_strength, whr/shr, waist_cm
5. `B4_face_features`: face_shape, eyelid, nose_bridge, teeth, asymmetry_mm, marks, early_hair_recession
6. `B5_sex_characteristics`: sex에 따라 `fields_M` 또는 `fields_F` 사용 + `fields_common`
7. `B5b_self_image`: B5 위에 얹는 *주관적 평가*. **중요**: `focused_concern`은 B4·B5의 *실제 값*과 *일관성* 있게 굴림 (예: B4 `asymmetry_mm` 6mm면 `focused_concern`에 "얼굴 비대칭" 가능성 높임)
8. `B6_chronic_health`: 0~3개의 만성 상태 + severity. 여성이면 `심한 생리통`도 pool에 포함
9. `B7_sleep`: habitual_duration, chronotype, current_debt, insomnia
10. `B8_sensory_profile`: visual_acuity + correction (안경/렌즈/라식 이력)
11. `B9_vocal`: pitch_hz (성별 차), volume, speech_rate, voice_quirks
12. `B10_skin_hair`: skin_type, skin_tone, visible_scars, hair_density, hair_texture, tattoos

### 3.2 Memory 층 (기억)

순서가 중요 — 앞 필드가 뒤 필드의 활성화 조건이 됨.

1. `M9_formative_family`: SES 분위, 부모 직업, 형제 구조, 경제 안정성, 거주 이력, 가정 분위기 **(먼저 굴림 — 다른 기억의 토양)**
2. `M1_ace_cumulative`: 10 카테고리 각각 boolean + 누적 점수. M9의 `family_emotional_climate`와 일관성 (예: 정서 금기 가정 → 정서적 학대·방임 확률↑)
3. `M3_parental_loss`: parental_status, event_age, primary_caregiver_after, contact_with_absent_parent, narrative_around_loss. M1의 "부모 별거·이혼" 카테고리와 일관성
4. `M2_childhood_sexual_abuse`: 발생 여부 결정 (prevalence: F 13% / M 5%). 발생 시 모든 하위 필드 굴림. **카페라떼 시나리오 코어** — `primary_sensory_channel`이 M7과 연결됨
5. `M4_bullying_history`: victim/perpetrator/bystander 각 역할 + 시기 + 형태 + 이중 역할 전환
6. `M5_attachment_style`: 4유형 + 불안·회피 차원 + 트리거 임계. M1·M3·M9와 일관성 (ACE 높고 양육자 불안정 → disorganized 확률↑)
7. `M10_parent_voice`: mother_pattern, father_pattern, consistency_between_parents, intergenerational_pressure, transmission_mechanism. M9 가정 분위기와 일관성
8. `M6_embedded_sentences`: 0~3개. 발화자·메시지 타입·활성화 트리거·의식 정도
9. `M11_embedded_reactions`: 0~3개. **충돌 지점**. 얼굴/체형/성기/가슴 등 대상 속성 → 반응 종류(표정·침묵·시선) → 관계(첫 연인/가족/친구) → 나이 → *사건 전 자기 인식* → 균열 깊이 → 처리 상태. **B5b 자기 이미지와 강하게 상호작용**
10. `M7_trauma_trigger_channel`: 0~2 채널. M2 발생 시 그 `primary_sensory_channel`이 자동 후보 (확정 아님 — 다른 기억과 결합 가능). 없으면 독립 굴림
11. `M8_default_reflex`: primary (Fight 15/Flight 25/Freeze 30/Fawn 30) + secondary + activation_threshold + polyvagal_state + visible_signature. M1 고ACE → Fawn/Freeze 확률↑

### 3.3 Identity 층 (인지·성·충동)

1. `I1_cognitive_ability`: g_iq (정규분포), cognitive_profile_strength/weakness, academic_performance (M9 SES와 약한 상관), metacognition, thinking_style, intellectual_curiosity
2. `I2_sexuality`: orientation (이성애 78% 기본), out_status, experience_status, first_experience_age, desire_intensity, desire_pattern_grain, internalized_taboos (poisson 1.5), function_satisfaction 3 하위, consent_history_marker. B5·B5b·M2와 일관성
3. `I3_impulse_and_footprint`:
   - **[A] 충동·중독**: digital_hours (평균 6.5±2.5), primary_platform_mix (poisson 4.0), digital_compulsion, substance_patterns (alcohol/smoking 성별 차/caffeine/others), eating_impulse, impulse_control, reward_sensitivity, escape_default, self_awareness
   - **[B] 사적 발자국**: favorite_games (poisson 1.2), journal_tone, sns_public_face, private_vs_public_gap, frequent_communities (poisson 1.5), playlist_tone, photo_album_theme (poisson 2.5), recent_search_pattern (poisson 2.5), bookmarks (poisson 2.0)
   - **상호작용**: I2·M1·M8·B7과 강하게. 예: M1 ACE 고점 + M2 발생 → escape_default가 *자해·성적 출구·디지털* 등으로 쏠림. B7 수면 부족 → digital_compulsion ↑ → recent_search에 "자살 방법" 가능성 ↑

### 3.4 Korea 층 (한국 특화 — 가장 나중)

1. `K1_korea_education`: high_school → suneung_grade → university_tier → major → retake → private_education → **academic_self_concept** (I1 g와 상관 있되 일관성 아님, M10 압력과도 상관) → parental_pressure
2. `K2_korea_appearance_experience`: discrimination_frequency, discrimination_domain (poisson 1.8), appearance_management_level, cosmetic_surgery_history, diet_history, lookism_internalization, appearance_capital_awareness. B2·B5b·M11과 강하게
3. `K3_korea_region_voice`: birth_region, current_residence_match, accent_intensity, accent_self_consciousness, family_politics, personal_politics_alignment, family_religion, personal_religion_alignment, regional_discrimination_experienced. M9와 일부 상관 (지역·SES)

---

## 4. Cross-layer 일관성 체크리스트

한 캐릭터 굴림 끝나면 다음 체크:

- [ ] M2 발생했는데 M7 `primary_sensory_channel` 없음? → M7 활성화
- [ ] M1 ACE 4+ 인데 M8 default_reflex가 Fight? → *가능하지만 드묾*. 확률 체크, 필요 시 Freeze/Fawn으로 조정
- [ ] I1 g 상위 5% 인데 K1 university_tier가 고졸? → *가능* (환경 요인). M9 SES 최하위이면 설명 가능
- [ ] B5b `genital_self_image` = 수치·회피 인데 I2 `function_satisfaction` = 충만? → 모순, 재굴림 또는 조정
- [ ] B7 current_debt 철야 + I3 digital_compulsion 통제 용이? → 모순, 재굴림
- [ ] K3 birth_region = 조선족 + M9 SES 5분위? → *가능하지만 드묾*. 특이 케이스로 유지 OK

**판단 기준**: 모순되면 재굴림, *드문 조합*이면 유지 (드문 케이스가 시뮬레이션의 재미).

---

## 5. 30명 전체 굴린 후 후처리

1. **B2 face_attractiveness 성별 내 서열 계산**: 남 15명 / 여 15명 각각 절대 점수 기준 1~15위 부여 (`sex_rank` 필드에 기록)
2. **누적 점수·상관 검증**: ACE 누적 평균, IQ 분포, 학력 분포가 일반 한국 20대 분포와 크게 벗어나지 않는지 체크 (예: 30명 중 ACE 4+가 15명이면 재굴림)
3. **사후 분류 격자 매칭**: `data/personas.json`의 30개 라벨 중 각 캐릭터와 가장 가까운 라벨 1~2개 붙이기 (*참고용*, 본질 아님)

---

## 6. 결과물 저장 형식

**파일**: `runs/seed_{N}.json` (N = 정수, 예: `seed_001.json`, `seed_042.json`)

**구조**:
```json
{
  "seed": 1,
  "generated_at": "2026-04-08T20:00:00+09:00",
  "constraints": {
    "sex_ratio": { "M": 15, "F": 15 },
    "age": 20,
    "region": "한국"
  },
  "table_versions": {
    "body": "0.1",
    "memory": "0.1",
    "identity": "0.1",
    "korea": "0.1"
  },
  "characters": [
    {
      "id": 1,
      "sex": "M",
      "post_hoc_label": ["#17 왜? 어떻게? 정말?", "#21 ......"],
      "body": {
        "height_cm": 178.3,
        "face_attractiveness": { "absolute_score": 6, "sex_rank": 5 },
        "body_composition": { "bmi": 23.1, "muscle_mass": "평균 이상", "grip_kg": 46, "waist_cm": 78, "shr": 1.42 },
        "face_features": { ... },
        "sex_characteristics": { ... },
        "self_image": { ... },
        "chronic_health": [ { "condition": "알레르기성 비염", "severity": "계절성 중간" } ],
        "sleep": { ... },
        "sensory": { "visual_acuity": "중등도 근시", "correction": "콘택트 상시" },
        "vocal": { ... },
        "skin_hair": { ... }
      },
      "memory": {
        "ace": { "categories": [...], "total": 2, "primary": "정서 학대 단독" },
        "csa": null,
        "parental_loss": { "status": "이혼·별거 (어머니 양육)", "event_age": "초등", ... },
        "bullying": { ... },
        "attachment": { "style": "anxious-preoccupied", "anxiety": 4, "avoidance": 2, "threshold": 3 },
        "embedded_sentences": [ ... ],
        "embedded_reactions": [ ... ],
        "trauma_trigger": [ ... ],
        "default_reflex": { "primary": "Fawn", "secondary": "Freeze 보조", "threshold": 2, "polyvagal": "교감 우세", "signature": "..." },
        "formative_family": { ... },
        "parent_voice": { ... }
      },
      "identity": {
        "cognitive": { "iq": 112, "strength": "수리·논리 우세", "weakness": "없음", "academic": "중상위", "metacognition": "정확", ... },
        "sexuality": { ... },
        "impulse_footprint": {
          "A_impulse": { ... },
          "B_footprint": { ... }
        }
      },
      "korea": {
        "education": { ... },
        "appearance_experience": { ... },
        "region_voice": { ... }
      }
    },
    // ... id 2~30
  ],
  "post_generation_notes": [
    "시드 1의 특이 케이스: #7은 ACE 4+ 복합이면서 I1 g=128 — '고IQ+고ACE' 조합",
    "..."
  ]
}
```

**검증**: 저장 직후 JSON 파싱 확인 (`jq keys runs/seed_N.json` 실행).

---

## 7. 굴림 후 사용자에게 보고할 것

1. **30명 요약 1줄씩** — 각 캐릭터의 *가장 도드라진 조합* 한 문장 (예: *"#7 여, 키 155cm, 만성 불면, ACE 5+ 정서방임+부모사별, Fawn, 고독 추구"*)
2. **특이 케이스 3~5개 하이라이트** — 시뮬레이션에서 재밌을 조합
3. **다음 호출 제안** — "어떤 무대에서 굴릴까? (학원·회사·재난·...)"

---

## 8. 오류 처리

- **옵션 표 파일 없음**: 사용자에게 알리고 `tables/`에서 누락 확인
- **이미 `runs/seed_N.json` 존재**: *재굴림*이 아니면 기존 로드. 재굴림이면 사용자에게 *덮어쓰기 OK?* 확인
- **JSON 파싱 실패**: 어느 캐릭터에서 실패했는지 보고하고 그 캐릭터만 재굴림

---

## 9. 이 프로토콜 자체의 버전

`v0.1` — 2026-04-08. 첫 시뮬 돌리고 문제 발견되면 갱신.
