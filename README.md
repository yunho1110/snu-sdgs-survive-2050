# 순천대 SDGs 어드벤처 — 캠퍼스 미션

순천대학교 SDGs/ESG 실천 아이소메트릭 웹 게임 프로토타입.

## 바로 실행
의존성 없음. `game/index.html`을 더블클릭하면 브라우저에서 바로 실행됩니다.

- PC: 방향키 / WASD 이동, Space 또는 E 로 상호작용
- 모바일: 화면 방향패드 + 상호작용 버튼
- 진행상황은 브라우저 localStorage에 자동 저장

## Claude Code에서 이어 개발하기
1. 이 폴더를 열고 터미널에서:
   ```bash
   cd snu-sdgs-game
   claude
   ```
2. Claude Code가 `CLAUDE.md`를 읽고 구조·데이터 모델·확장 방법을 파악합니다.
3. 예시 요청:
   - "퀘스트 3개 더 추가해줘 (체리니 1, 우송이 2)"
   - "도서관 옆에 학생식당 건물 추가하고 음식물 쓰레기 줄이기 미션 연결"
   - "분리수거 미니게임 난이도 단계 추가"

## 스프라이트 재생성
마스코트 원본은 `assets/mascots/source/*.ai` (Illustrator=PDF 호환).
```bash
# 요구: poppler-utils, Pillow
pip install pillow
python tools/build_sprites.py
```
→ `assets/mascots/*.png` 갱신 + `game/index.html`에 base64 자동 주입.

## 핵심 기능 (구현됨, 일부 모의)
- 아이소메트릭 캠퍼스 맵 탐험 (정문·대학본부·도서관·공과대학·학생회관·생활관·박물관)
- 마스코트 NPC 퀘스트 (E/S/G) + 완료 시 SDGs/ESG 학습 카드
- O2O 인증 플로우 (사진/QR/영수증 — 모의)
- 미니게임 2종 (분리수거 분류, ESG 퀴즈)
- 에코포인트·경험치·레벨, 캐릭터 꾸미기 상점
- 학과 ESG 랭킹(모의), 소셜 광장 채팅(모의)
- SDG 공식 컬러 간판, 게임 UI(퀘스트 패널·체력/에너지·인벤토리·미니맵)

자세한 구조와 로드맵은 `CLAUDE.md` 참고.
