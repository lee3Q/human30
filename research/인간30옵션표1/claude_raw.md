# 인간30 옵션표 리서치 — Claude 자체 결과

> 태그: 인간30옵션표1
> 날짜: 2026-04-08
> 소스: Claude (general-purpose 서브에이전트 + WebSearch)
> 상태: Phase 1 완료 — Gemini/Perplexity 결과 대기 중

---

## 1. 가장 강한 예측 변수 (효과 크기 순)

메타분석 수준의 효과 크기 순. 해석 기준: r<0.1 무시, 0.1~0.2 약, 0.2~0.3 중, 0.3+ 강, 0.5+ 매우 강.

| 순위 | 변수 | 효과 크기 | 주요 연구 | 예측 대상 | 메모 |
|---|---|---|---|---|---|
| 1 | **IQ → 교육성취** | r = .56 | Strenze 2007 (k=59, N=84,828) | 학력 | 단일 변수 중 가장 강함 |
| 2 | **IQ → 직업성취** | r = .43 | Strenze 2007 (k=45, N=72,290) | 직업 지위 | |
| 3 | **신장 → 사회적 존경** | ρ = .41 | Judge & Cable 2004 (JAP) | 지도자 부상, 평판 | 남성(ρ=.29) > 여성(ρ=.21) |
| 4 | **얼굴 매력도 → 전반적 사회 평가** | d ~ 0.5~0.7 | Langlois et al. 2000 (11개 메타분석) | 대인 대우, 판단, 행동 | "미녀의 신화는 사실" — 관찰자 간 일치 매우 높음 |
| 5 | **애착 안정성 → 관계 만족도** | r ≈ .35 | Fraley 2002; Li & Chan 2012 | 성인 낭만 관계 | 회피/불안 모두 음의 상관 |
| 6 | **아동기 성학대 → 성인 정신병리** | OR ~ 2.5~3.0 (d ~ .3~.5) | Maniglio 2009 (14개 review, N=270k+) | 우울·PTSD·불안·성기능장애 | 비특이적 광범위 위험 |
| 7 | **아동기 괴롭힘 → 성인 정신건강** | OR ~ 2.0~4.0 | Takizawa 2014 (45년 추적) | 우울, 자살성, 사회적 고립 | 40년 후에도 유의 |
| 8 | **ACE (4개 이상) → 성인 우울** | OR ~ 4~12 (자살시도 30~50배) | Felitti 1998; Hughes 2017 Lancet | 건강, 정신건강, 만성질환 | 용량-반응 관계 |
| 9 | **IQ → 수명/사망률** | HR: IQ 1SD ↓ = 79% 생존율 | Calvin 2011 (N=1.1M) | 전체 사망률 | SES 통제해도 30%만 설명 |
| 10 | **ACE → 정서적 웰빙** | r = -.32 | Thurston et al. 2025 | 성인 주관적 웰빙 | |
| 11 | **수면 손실 → 긍정 정서** | g = -0.94 | Tomaso 2021 (Psych Bulletin) | 기분, 정서 조절 | 긍정 기분이 먼저 무너짐 |
| 12 | **부모 사별 → 성인 우울** | OR = 2.16 | Berg 2016 meta; Luecken 2008 | 성인 우울증 | 후속 돌봄 질이 강력한 조절 |
| 13 | **IQ → 소득** | r = .20 | Strenze 2007 | 임금 | 교육·직업보다 낮음 |
| 14 | **부모 SES → 아동 심리병리** | g = 0.19~0.32 | Peverill 2021 (k=120, N=26,715) | 아동 정신건강 | 공공부조 수급(g=.32)이 최대 |
| 15 | **신장 → 임금** | β = .26 | Judge & Cable 2004 | 소득 | 성별/나이/체중 통제 후 |
| 16 | **BMI (여성) → 임금 페널티** | -5.8% ~ -24% | Averett & Korenman 1996 | 임금, 고용 | 백인 여성에서 특히 강함 |
| 17 | **얼굴 매력도 → 평생 수입** | 10~15% (≈ $230k) | Hamermesh & Biddle 1994 | 소득 | 못생김 페널티 > 미인 프리미엄 |
| 18 | **발기부전 ↔ 우울 (양방향)** | ED→우울 OR=2.92; 우울→ED OR=1.39 | Liu et al. 2018 (JSM) | 우울, 관계 질 | |
| 19 | **신장 → 수행평가** | ρ = .18 | Judge & Cable 2004 | 직무 수행 | |
| 20 | **Conscientiousness → 직무 수행** | ρ = .15~.29 | Barrick & Mount 1991 | 직무 수행 | Big 5 중 가장 강함 — 그래도 약~중 |

**핵심 통찰**: IQ, 키, 얼굴 매력도, 애착 안정성, ACE — 이 다섯 묶음이 실질적으로 가장 강력한 예측 변수. Big Five는 유명한 만큼 대단치 않다 (ρ=.1~.3).

---

## 2. 한국 특화 변수

| 변수 | 효과 | 근거 |
|---|---|---|
| **수능 등급 기반 대학 서열 → 소득** | 5그룹 vs 1그룹: 25~29세 +25%, 40~44세 +51% | KDI 연구 |
| **외모 → 고용** | HR 50%가 외모 기반 결정, 구직자 65%가 외모 영향 인식 | "취업 성형" 문화 |
| **교육 일치 → 결혼·이혼** | 최근 코호트에서 뚜렷 | Park & Raymo |
| **사교육비 → 부모 우울** | 소득·교육과 상호작용 | KoWePS 2015, 2018 |
| **가구 소득 (저-저 지속) → 우울** | 저-저 그룹이 최대 | KoWePS 종단 (Chung 2016) |
| **아동 ACE → 성인 자살 행동** | 아동학대 → 우울 매개 → 자살 시도 유의 | Lee & Park 2023 (N=1,048) |
| **한국 아동학대 → 성인 정신질환** | 감정적 방치·정서적·신체 학대 모두 강한 상관 | Nationwide Community (N=5,102) |
| **학교폭력 → 우울·자살성** | 피해자 스트레스·우울·자살 모두 증가 | KNHANES; 다문화 청소년 (N=3,627) |
| **혈액형 성격 신앙** | 75% 한국인 믿음, but 분산의 <0.3%만 설명 | Nawata (N=10k+) |

**한국 특화 핵심**: 수능/대학 서열, 외모 노동, 사교육 부담, 학교폭력. 네 가지가 일반 메타분석 효과 크기를 초과.

---

## 3. 과대평가 변수 (예측력 낮음)

| 변수 | 실제 효과 | 평가 |
|---|---|---|
| MBTI → 직무 수행 | 메타분석 포함 실패, 재검사 신뢰도 50% | 거의 무의미 |
| 혈액형 → 성격 | r² < 0.003 | 자기충족 예언만 |
| 출생 순서 → 성격 | r ≈ .02 (Damian & Roberts 2015, N=377k) | Sulloway 예측의 1/10 |
| 별자리 | 메타분석 증거 없음 | |
| Big Five 개별 | 각 ρ = .10~.19 (C 제외) | "성격이 전부" 통념보다 훨씬 작음 |

---

## 4. 트라우마 각인 모달리티 (카페라떼 시나리오 재료)

**감각 채널별 트라우마 재활성화 강도**:

1. **후각이 가장 강력** — 후각 신경은 시상(thalamus) 우회, 편도체·해마 직결. 다른 감각은 시상 경유. 해부학적 "지름길" 때문에:
   - 더 강한 정서적 회상
   - 더 어린 시절까지 거슬러 올라감
   - 의식적 통제 없이 자동 발동
   - Ressler (McLean): "트라우마 연관 냄새는 거의 확실히 가장 강력한 트리거"

2. **PTSD 특이 후각 트리거 사례**: 연료, 피, 화약, 타는 머리카락 → 참전 용사 PTSD 가장 빈번 (Vermetten & Bremner 2003)

3. **후각 민감도 상승**: 트라우마 연합 냄새는 신경전달물질 방출 4배 (Rutgers)

4. **시각/청각**: 플래시백 형태지만 의식 외 자동성은 후각만큼 강하지 않음. 재해석 여지 있음.

5. **신체 감각(interoception)**: van der Kolk 신체화 이론 — 단, 학술 비판 있음. 폴리바갈도 방법론 비판.

6. **Freeze/Fawn**: 아동기·관계적 트라우마에서 가장 흔함. Pete Walker F4 모델. 사회 교전 + 교감/부교감 "동시 활성" — 과잉 사회성(super social engagement) 생존 전략.

**카페라떼 시사**: 가장 강력한 트리거 채널 = 후각 (+ 미각). 학술적으로 방어 가능. 캐릭터별 "트리거 감각 채널" 옵션화가 카페라떼 시나리오의 핵심 재료.

---

## 5. 놓친 영역 / 추가 리서치 필요

1. 만성 질환 → 일상 회피 동선 효과 크기 (질환별 메타는 있으나 "일상 결정" 정량화 부족)
2. 생리주기·호르몬 → 의사결정 (드물고 논쟁적)
3. 초경 조기/늦은 시기 → 성인 결과 (Ellis 생명사 이론)
4. Big Five → 배우자 선택 (직무보다 관계 맥락 데이터)
5. 소수자 스트레스 모델 효과 크기 (Meyer)
6. 디지털 네이티브 SNS → 신체상/불안 (한국 청소년)
7. 한국 병역 경험 → 남성 대인 패턴
8. 지역(수도권/지방) 효과
9. 고시 경험의 성격/인지 영향
10. 여성 labial/유방 형태 → 대인 회피 (Veale는 BDD 임상 표본 중심, 일반 인구 부족)

---

## 6. 참고문헌 (핵심 20개)

1. **Judge & Cable (2004)**. Physical height on workplace success. *JAP* 89(3), 428-441.
2. **Langlois et al. (2000)**. Maxims or myths of beauty? *Psych Bulletin* 126(3), 390-423.
3. **Hamermesh & Biddle (1994)**. Beauty and the labor market. *AER*; Hamermesh (2011) *Beauty Pays*.
4. **Strenze (2007)**. Intelligence and socioeconomic success. *Intelligence* 35(5), 401-426.
5. **Felitti et al. (1998)**. ACE Study. *AJPM* 14(4), 245-258.
6. **Hughes et al. (2017)**. Multiple ACE meta. *Lancet Public Health* 2(8), e356-e366.
7. **Maniglio (2009)**. Child sexual abuse health review. *Clin Psych Review* 29(7), 647-657.
8. **Takizawa, Maughan & Arseneault (2014)**. Childhood bullying 45-year outcomes. *AJP* 171(7), 777-784.
9. **Wolke & Lereya (2015)**. Long-term effects of bullying. *ADC* 100(9), 879-885.
10. **Puhl & Heuer (2009)**. Stigma of obesity. *Obesity* 17(5), 941-964.
11. **Fraley (2002)**. Attachment stability meta. *PSPR* 6(2), 123-151.
12. **Barrick & Mount (1991)**. Big Five job performance. *Personnel Psych* 44(1), 1-26.
13. **Calvin, Deary et al. (2011)**. Intelligence and all-cause mortality. *IJE* 40(3), 626-644.
14. **Tomaso, Johnson & Nelson (2021)**. Sleep deprivation and emotion. *Sleep* 44(6).
15. **Veale et al. (2015)**. Penile BDD phenomenology. *Body Image* 13, 47-51.
16. **Iacovides, Avidon & Baker (2015)**. Primary dysmenorrhea review. *Hum Reprod Update* 21(6), 762-778.
17. **Lee & Park (2023)**. ACEs and Korean suicide. *JIV*.
18. **Vermetten & Bremner (2003)**. Olfaction as PTSD reminder. *J Clin Psychiatry* 64(2), 202-207.
19. **Berg, Rostila & Hjern (2016)**. Parental death and depression. *JCPP*.
20. **Peverill et al. (2021)**. SES and child psychopathology meta. *CPR* 83.

**보조 (한국·트라우마)**:
- Porges (2011). Polyvagal Theory [비판: Grossman 2023]
- van der Kolk (2014). Body Keeps the Score [학술적 비판 존재]
- KDI 대학 서열-소득 연구
- Chung, Kim & Subramanian (2016). Korean depression. *IJEH*

---

## 핵심 권고

- **옵션표 1순위 변수**: IQ, 키, 얼굴 매력도, ACE 점수, 애착 유형, 아동기 괴롭힘, 부모 SES, 만성 수면 부족
- **한국 추가**: 대학 서열(5단계), 외모 노동 경험, 학교폭력, 사교육 환경, 가구 소득 지속성
- **트라우마 트리거 채널**: 후각 > 시각 > 청각 > 촉각 (카페라떼 = 후각 시나리오 학술 기반 충분)
- **회피 함정**: MBTI, 혈액형, 출생순서, 별자리 — "통념상 중요하지만 예측력 ≈ 0"
- **Big 5 주의**: Conscientiousness만 ρ=.19, 나머지 그 이하
