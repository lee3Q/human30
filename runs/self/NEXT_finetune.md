# 이 세션의 목적

31번 캐릭터(이상규)의 **파인튜닝 방향성**을 결정한다.

## 왜 여기 왔나

이전 세션에서 31번 에이전트를 프롬프트 스터핑(99_agent.md)으로 만들었다. 사용자가 직접 싸워본 결과:

- **"내가 아닌데"가 5건** — 흉내의 결이 틀림
- **"뻔해"가 3건** — 요약이 얕음. 정원이 축만 반복 (바나나우유 문제)
- **"몰랐는데"가 1~2건** — 발견 적음

사용자 직접 피드백: **"내 데이터와 대화하는 것 같다. 내가 아니라."**

프롬프트 스터핑의 한계: LLM이 *가중치 높은 데이터*를 모든 맥락에 반복 (정원이를 바나나우유처럼 씀). 맥락 판별 불가.

사용자가 원하는 건 **행동 예측**이 아니라 **가치관·사고방식의 복원**. "편의를 요하는 게 아니라, 더 불편하고 싶은 거. 앎이라는 고통을 받아들이고 싶은 거지."

## 결정해야 할 것

1. **파인튜닝할 것인가** — 의존성 정책 예외 (PyTorch+transformers) 확정
2. **베이스 모델** — 한국어 소형 LLM 선택 (LLaMA-Ko, KULLM, Polyglot-Ko, sLLM 등)
3. **학습 데이터 구성** — 어떤 데이터를 어떤 형태로 넣을지
   - 카톡 원본 ~90K줄 (정원이/앤두/말랑이 = 동일인)
   - 통화녹음 텍스트 200개+ (UTF-16 인코딩)
   - 블로그 "Pedantic" 98개 글
   - Claude 세션 백업 211개
   - 이미 정제된 파일들: 03_memory(274KB), 04_identity(38KB), 05_shadow(46KB), 06_communications(53KB), 07_blog(27KB)
4. **학습 환경** — MacBook M칩 로컬 가능 여부, 또는 클라우드
5. **학습 방법** — Full finetune vs LoRA/QLoRA vs 다른 방식
6. **평가 기준** — "내가 아닌데" / "뻔해" / "몰랐는데" 3기준

## 먼저 읽어야 할 파일

- `/Users/sanggyulee/pp/30p/runs/self/99_agent.md` — 현재 프롬프트 스터핑 버전 (v0.3, 25KB). 파인튜닝 후에도 이 파일의 *운영체제 층*은 유지
- `/Users/sanggyulee/pp/30p/runs/self/README.md` — 31번 캐릭터 프로토콜
- `/Users/sanggyulee/.claude/projects/-Users-sanggyulee-pp/memory/user_core_drive.md` — "앎이라는 고통"
- `/Users/sanggyulee/.claude/projects/-Users-sanggyulee-pp/memory/feedback_dependency_policy.md` — 의존성 정책 (외부 패키지 0 원칙, 예외 논의 필요)

## 사용자에게 묻지 않고 시작할 것

이 파일들을 읽고, 파인튜닝 방향성 제안을 *먼저* 내놓는다. 사용자는 제안을 듣고 결정한다. "뭐부터 할까요?"가 아니라 "이렇게 하는 게 맞다, 이유는 이거다"로 시작.
