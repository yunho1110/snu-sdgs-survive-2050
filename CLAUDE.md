# CLAUDE.md — 순천대 SDGs 어드벤처

Claude Code가 이 프로젝트를 이어서 개발할 때 참고하는 문서입니다.

## 프로젝트 개요
순천대학교 SDGs/ESG 실천을 유도하는 **아이소메트릭(2.5D) 웹 캠퍼스 게임** 프로토타입.
실제 캠퍼스를 누비며 마스코트에게 퀘스트를 받고, 현실 활동을 인증해 에코포인트를 모은다.
원 기획은 기능명세서(PRD) 기반이며, 핵심 5대 기능을 단일 HTML 파일로 동작 구현했다.

- 마스코트: **우송이**(낙우송·환경 E), **체리니**(벚나무·사회 S), **총장님**(고양이·지배구조 G)
- 마스코트 아트는 학교 제공 원본 일러스트(`assets/mascots/source/*.ai`)에서 추출해 사용.

## 파일 구조
```
snu-sdgs-game/
├─ game/index.html          # 게임 본체 (단일 파일, 의존성 없음, 더블클릭 실행)
├─ assets/mascots/
│   ├─ usong.png cheri.png chong.png   # 게임용 스프라이트(투명·64색)
│   ├─ sprites_b64.json                # 위 PNG의 base64 data URI
│   └─ source/*.ai                      # 원본 캐릭터 가이드(재생성 소스)
├─ tools/build_sprites.py   # .ai → 스프라이트 → index.html 주입 파이프라인
├─ README.md
└─ CLAUDE.md (이 문서)
```

## 아키텍처 (game/index.html)
순수 HTML+CSS+JS, 외부 라이브러리 없음. Canvas 2D로 직접 렌더.
마스코트 이미지는 `SPRITES` 객체에 **base64 data URI로 인라인**되어 있어 파일 하나로 완결된다.

### 좌표계 (아이소메트릭)
- 타일: `TW=64, TH=32` (HW=32, HH=16). 그리드 `GW=GH=30`.
- 변환: `iso(gx,gy) = {x:(gx-gy)*HW, y:(gx+gy)*HH}`
- 화면: `toScr(gx,gy)` = iso − 카메라 + 화면중앙. 카메라는 매 프레임 플레이어 위치로.
- **깊이 정렬**: 모든 엔티티를 `gx+gy` (건물은 앞 모서리 `(gx+w)+(gy+d)`) 키로 정렬해 painter's order. 이게 앞뒤 가림(occlusion)을 자연스럽게 만든다.

### 데이터 주도 설계 (여기만 고치면 콘텐츠가 바뀜)
모두 스크립트 상단의 배열/객체로 정의됨:
- `ground[][]` — 타일 타입(0 잔디·1 광장·2 길·3 물·4 정원). `setRect()`로 영역 지정.
- `buildings[]` — `{id,name,code,cat,icon,gx,gy,w,d,h,solar,top/l/r/roof(색),poi}`
- `npcs[]` — 마스코트 `{id,name,kind(E/S/G),img,gx,gy,sc}`
- `sdg[]` — SDG 간판 `{gx,gy,n(번호),c(공식컬러),label}`
- `decor[]` — 나무/울타리/벤치/가로등/분리수거함/꽃밭/표지판/분수 (seedDecor에서 생성)
- `QUESTS[]` — 퀘스트 `{id,npc,cat,title,cert(photo/receipt/qr/none),desc,pts,xp,quiz?,learn{k,tip,link}}`
- `QUIZ{}` — 퀴즈 문항, `SHOP[]` — 꾸미기 아이템, `RANK_BASE[]` — 학과 랭킹(모의)

### 렌더 파이프라인 (`render()`)
`drawSky()`(하늘·산·구름) → `drawGround()`(다이아몬드 타일+엠블럼) → 엔티티 깊이정렬 draw → `drawMini()`(미니맵).
건물은 `drawBuilding()`이 좌/우 측면 + 지붕 3면 음영, `faceWindows()` 창문, `solarRoof()` 태양광.

### 상태 / 저장
- `State` 객체에 닉네임·포인트·xp·레벨·완료퀘스트·보유아이템 등.
- `localStorage('sce3')`에 자동 저장. 도움말의 "진행 초기화"로 리셋.

### UI 크롬 (HTML 오버레이, CSS class `.ui`)
배너(좌상), 에코포인트 칩, 퀘스트 패널·메뉴(우상), 채팅(좌하), 체력/에너지 바, 인벤토리 핫바(하단), 미니맵(우하).

## 픽셀아트 + 실제 캠퍼스맵 파이프라인 (2026-06 추가)
- **렌더 톤**: 캔버스를 화면의 1/`PXZOOM`(기본 2) 해상도 백버퍼에 그린 뒤 `image-rendering:pixelated`로 확대 → 전체가 도트 느낌. `ctx.imageSmoothingEnabled=false`로 스프라이트도 또렷.
- **마스코트 픽셀화**: `tools/pixelate.py` — 공식 일러스트(usong/cheri/chong.png)를 가장자리 flood-fill 투명화 → NEAREST 다운스케일(높이 48px) → 팔레트 양자화 → 외곽선 강조. 결과 `*_px.png`, `sprites_px_b64.json`.
- **실제 캠퍼스맵**: `tools/build_campus.py` — 제공된 순천대 캠퍼스맵의 라벨 화면좌표(px,py)를 아이소 그리드로 변환해 A1~F4 전 건물 + 운동장(트랙)/체육관/정문·남문·북문/도로/연못/정원 자동 배치. `index.html`의 `/*CAMPUS_DATA_START*/…/*CAMPUS_DATA_END*/` 블록을 치환(GW/GH/GROUND_OPS/buildings/npcs/sdg/DECOR/PLAYER_SPAWN/PLAZA 생성)하고 마스코트 base64도 주입.
- **재생성**: `python3 tools/pixelate.py && python3 tools/build_campus.py`. 건물 좌표·이름·카테고리는 `build_campus.py`의 `B[]` 리스트에서만 수정.
- **신규 지면 타입**: 5=운동장(field). 트랙 오벌은 decor `stadium`가 그림.

## 도트 비주얼 시스템 (2026-06 고도화)
- **통일 팔레트**: `index.html` 상단 `PAL`/`WALLS`/`ROOFS`/`CATSTYLE`. 따뜻·저채도 고정색만 사용(색 튐 방지). 건물·지면·하늘·데코 전부 여기서만 색을 가져옴.
- **건물 변주(palette swap)**: `variantFor(b)`가 건물 code 해시로 벽/지붕 램프, 창문 밀도, 점등 패턴, 옥상 구조물(`roofProp` 0~3), 높이 지터, 좌우반전을 결정 → 같은 카테고리도 수십 가지 외형. **부호없는 `>>>` 사용 필수**(>> 쓰면 음수 인덱스 버그).
- **건물 렌더(`drawBuilding`)**: 평면 3톤(지붕>좌벽>우벽) + 굽(plinth) + 처마 overhang(`expand`) + 용마루 하이라이트 + 2톤 창문(`faceWindows`, 일부 점등) + 출입문 + 전체 외곽선(`PAL.out`). 좌표는 `Rp()`로 정수 스냅.
- **마스코트 팔레트 통일**: `pixelate.py`의 `PALETTE`(씬과 같은 톤)로 nearest 매핑. 우송이=청록(낙우송), 체리니=핑크, 총장님=크림.
- **데코**: 나무/울타리/벤치/가로등/꽃밭 모두 평면+외곽선 도트로 재작성. 그라데이션 금지.
- **밀도**: `build_campus.py`의 `SX/SY`(작을수록 간격↑, 현재 21.5/13.0)로 건물 사이 숨통 조절. 나무 95개로 빈 잔디 채움.

## 캐릭터 8방향 모션 (2026-06, 코드 렌더)
- **방향**: `dir8(dx,dy)` — 그리드 이동벡터를 `iso()`로 화면각 변환 후 8섹터(S/SE/E/NE/N/NW/W/SW) 매핑. 플레이어·군중 모두 사용. `dir` 기본값 'S'.
- **렌더**: `drawChibi(x,y,col,hair,dir,frame,moving,name)`. `FVMAP`로 facing 단위벡터를 얻어 — 앞쪽=얼굴+눈+볼, 측면(E/W)=눈 1개, 뒤쪽(N계열)=얼굴 숨김(뒤통수). 외곽선 `PAL.out`, 옷/머리 음영은 `mul()`.
- **리듬감(딱딱한 도트)**: 보간 없이 **4프레임 스텝**(`floor(t/5)%4` 플레이어, `floor(t/6)%4` 군중). 다리·팔 교차 = `[1,0,-1,0]`.
- **반동(bounce)**: 패스 프레임에 몸통·머리만 정수 `-2px`(`[0,-2,0,-2]`), **발은 지면 고정 + 그림자 축소** → 통통 튀는 느낌. 정지 시 가벼운 idle bob.
- 참고: 헤드리스 미리보기는 rAF가 멈춰 자동 루프가 안 도므로, 검증 시 `loop()`를 수동 호출하거나 실제 브라우저에서 확인.

## 분위기/연출/필터 (2026-06)
- **마스코트 배회**: `loop()`에서 각 NPC가 `home` 주변(±2.5칸)으로 천천히 걸어다님(`n.mv/tx/ty/wt/face`). `drawMascot`이 걸을 때 통통 반동+세로 스쿼시+진행방향 좌우반전(`scale(face,1)`).
- **이펙트**: `fx[]` 파티클(별/플로팅텍스트) + `spawnSparkle/spawnText/updateFX/drawFX`. `drawBubble`=말풍선(팝). 가까운 NPC 머리 위 `♥`/`!` 표시.
- **점프**: `playerHop`(HOPDUR) → `drawChibi`의 `lift` 인자(발·몸·머리 상승, 그림자 축소). 퀘스트 수락 시 `hop()`, 보상 받을 때 `celebrate()`.
- **보상 연출 트리거**: `addReward`가 `pendingCelebrate` 예약 → `closeOv()`(모달 닫힐 때) `celebrate()`+`+점수` 팝. 맵에서 보이게.
- **낮/밤**: `nightFactor()`(주기 `DAYLEN` 2분, 0낮~1밤) → `NF`. `drawSky` 색 보간+별+해/달, `render` 끝에 밤 틴트. **창문/가로등 야간 점등**: 위치를 `nightLights[]`에 모아 틴트 *위에서* `globalCompositeOperation='lighter'`로 발광. `faceWindows`는 밤엔 소등(어둡게)+일부 점등.
- **비속어 필터**: `BADWORDS`/`BADRE`/`cleanText()`. `sendChat`에서 매칭 시 `◯`로 치환 + 경고 토스트.

## 전용 플레이어 스프라이트시트 (2026-06)
- **생성기**: `tools/build_character.py` — 32x32 타일, **4프레임(걷기) × 3행(정면 down / 측면 side·우향 / 뒷면 up)** 의 '에코 학생' 캐릭터를 픽셀 단위로 작도(파트 채색 → `outline()` 자동 외곽선 → 얼굴/엠블럼). 결과 `assets/character/hero.png` + 확대 미리보기 `hero_preview.png`, base64를 `index.html`의 `const HERO_SRC="…"`에 주입.
- **게임 연결**: `HERO`(이미지/FW/FH), `HERO_ROW`(8방향→행: S/SE/SW=정면, E/W=측면, N계열=뒷면), `HERO_FLIP`(W/SW/NW=좌우반전). `drawPlayer`가 `drawImage(시트, frame*FW, row*FH, …)`로 렌더(걷기 `floor(t/6)%4`, 정지=0프레임). 미로딩 시 `drawChibi` 폴백.
- **렌더 상수**: `HSCALE`(확대), `FEET`(타일 내 발 y=30) 기준으로 발을 지면(`s.y`)에 정렬, `playerHop`은 y오프셋으로 점프. 그림자/이름표/착용아이템은 코드로 덧그림.
- **군중(crowd)**은 그대로 `drawChibi`(팔레트 변주) 사용 — 주인공만 전용 시트.
- **재생성**: `python3 tools/build_character.py` (디자인 수정은 스크립트의 `build_down/build_side`와 `CLR` 팔레트에서).

## 마스코트 워크 시트 / 팀컬러 / 꾸미기 / 맵확장 (2026-06)
- **마스코트 전용 워크시트**: `tools/build_mascots.py` — 우송이(낙우송 원뿔)/체리니(핑크 블롭+새싹)/총장님(고양이) 각 32x40, 3행(down/side/up)×4프레임. `assets/mascots/<key>_sheet.png` + `MASCOT_SHEETS`(base64) 주입. `drawMascot`가 `MIMG`로 로드해 `n.dir`(배회 시 `dir8`로 갱신)·걷기프레임(`floor(wk/8)%4`)으로 샘플, `MSCALE/MFEET`로 지면 정렬. 미로딩 시 기존 픽셀 PNG 폴백.
- **팀 컬러(멀티 대비)**: `TEAMS`(후디 3톤 램프) + `heroSheet()` — `State.team`에 따라 시트의 후디 원본 3색(`HERO_BASE`)을 캔버스에서 팔레트 스왑해 `HERO_VAR`에 캐시. 설정 `🎨 팀 컬러`(`openTeam/setTeam`)에서 선택.
- **꾸미기 레이어**: `drawCosmetic(id,cx,hyTop,shY,grp,fdir)` — 학사모/나뭇잎관/안경/벚꽃핀은 머리 앞, 에코망토는 캐릭터 뒤(이미지 전에), star_fx는 loop에서 반짝이. `grp`(front/side/back)·`fdir`(반전)로 방향 대응. 상점 착용(`State.owned[id]==='worn'`)과 연동.
- **맵 확장**: `build_campus.py` `SX/SY=16/9.6`, `MARGIN=7` → GW/GH≈58×68. 둘레 산책로(루프) + 가로수 170, 플레이어 `spd=0.11`로 넓은 맵 이동.

## 실측 지도 반영 / 대형맵 / 운동장 개선 (2026-06)
- **정밀 좌표**: `build_campus.py` `B[]`의 px,py를 실제 캠퍼스맵 핀 좌표로 교체(F동은 동남쪽이 정위치). `SX/SY=13.5/9.0`, `PX0/PY0=820/100`, `MARGIN=8` → **GW/GH≈125×98**(아주 넓음). 가로수 420.
- **운동장**: `FIELD=(A15 px,py)`, `FIELD_W/FIELD_D=12/9` 타일 영역(지면 type5). 이 영역엔 건물 미배치(실측 좌표라 겹침 없음). `drawStadium`이 `d.fw/d.fd`로 크기 받아 트랙(다중 레인)+잔디 인필드+축구장(센터서클/하프라인)을 영역에 맞춰 그림.
- **대형맵 성능**: `drawGround`는 카메라 주변 윈도우(±36타일)만 순회. 미니맵은 정적 레이어(지면+건물)를 `miniBG` 캔버스에 1회 캐시 후 매 프레임 blit + 동적 점만 갱신. (지도 바꾸면 `miniBG=null`로 무효화 필요)

## 자주 하는 작업 (How-to)
- **퀘스트 추가**: `QUESTS[]`에 객체 1개 추가. `npc`로 마스코트 연결, `cat`로 건물 연결, `quiz:true`면 `QUIZ{}`에 문항 추가.
- **건물 추가/이동**: `buildings[]` 수정. 좌표가 겹치지 않게 주의(충돌 타일 자동 등록됨).
- **마스코트 교체/추가**: `assets/mascots/source/`에 .ai 넣고 `tools/build_sprites.py`의 JOBS에 추가 → 실행.
- **스프라이트 재생성**: `python tools/build_sprites.py` (poppler-utils + Pillow 필요).
- **지도 배치 검증**: 좌표만 바꾸면 빠르게 PIL로 top-down/iso 미리보기 스크립트를 만들어 겹침을 확인하는 패턴을 권장.

## 알려진 한계 / 의도적 단순화
- 인증(사진/QR/영수증), 채팅, 멀티플레이, 학과 랭킹은 **모의(mock)** 동작. 실제 백엔드 없음.
- 그래픽은 코드로 그린 벡터형 아이소메트릭. "메이플스토리급" 픽셀 도트는 **전용 스프라이트시트(타일/캐릭터)** 가 있어야 도달 가능.
- 단일 파일이라 규모가 커지면 모듈 분리 필요.

## 로드맵 (다음 단계 제안)
1. **에셋 고도화**: 픽셀 타일셋·건물·캐릭터 워크 애니메이션 스프라이트시트 도입 → 렌더를 `drawImage` 기반으로 교체.
2. **백엔드(MVP)**: 사용자/인증/포인트 API. 사진 업로드+검수 큐, QR 1회성 토큰, 부정방지(중복 해시·시간간격·위치).
3. **멀티플레이**: WebSocket 기반 광장 실시간 위치·채팅.
4. **학과 랭킹 집계**: 활동 가중치 규칙 + 시즌/주간/일간 집계.
5. **프레임워크 이관**: 규모가 커지면 Phaser 또는 PixiJS로 이전 검토(현재는 의존성 0이 강점).

## 코딩 컨벤션
- 외부 의존성 추가는 신중히(현재 0). 단일 파일 실행 가능성을 가능한 유지.
- 좌표는 모두 그리드(gx,gy) 기준. 화면 픽셀 변환은 `toScr()`만 사용.
- 한국어 UI 텍스트 유지. 데이터(퀘스트/건물 등)는 상단 배열에서만 수정.
