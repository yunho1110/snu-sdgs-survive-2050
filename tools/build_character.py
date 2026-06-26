#!/usr/bin/env python3
"""
전용 플레이어 캐릭터 스프라이트시트 생성기
- 32x32 타일, 3행(정면 down / 측면 side(우향) / 뒷면 up) x 4열(걷기 프레임)
- 씬 통일 팔레트의 '에코 학생' 캐릭터를 픽셀 단위로 작도 + 외곽선 자동 래핑
- assets/character/hero.png 저장 + base64를 index.html 의 HERO_SRC 에 주입
실행:  python3 tools/build_character.py
"""
import base64, re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "assets/character"; OUTDIR.mkdir(parents=True, exist_ok=True)
GAME = ROOT / "game/index.html"

T = 32           # 타일 크기
COLS, ROWS = 4, 3
SCALE_PREVIEW = 6

# 팔레트
CLR = dict(
  OUT=(43,34,48,255), NONE=(0,0,0,0),
  SKIN=(242,206,160,255), SKINSH=(216,176,132,255), BLUSH=(232,154,134,255),
  HAIR=(120,80,50,255), HAIRSH=(92,58,34,255), HAIRHI=(150,108,72,255),
  TOP=(79,158,146,255), TOPSH=(56,116,107,255), TOPHI=(150,202,190,255),
  PANTS=(78,94,124,255), PANTSSH=(56,68,94,255),
  SHOE=(60,54,66,255), LEAF=(124,200,120,255), WHITE=(245,240,232,255), EYE=(43,34,48,255),
)

class Tile:
    def __init__(s): s.px=[[(0,0,0,0)]*T for _ in range(T)]
    def set(s,x,y,c):
        if 0<=x<T and 0<=y<T and c[3]>0: s.px[y][x]=c
    def rect(s,x0,y0,x1,y1,c):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1): s.set(x,y,c)
    def opaque(s,x,y):
        return 0<=x<T and 0<=y<T and s.px[y][x][3]>0
    def outline(s,col):
        add=[]
        for y in range(T):
            for x in range(T):
                if s.px[y][x][3]==0:
                    if any(s.opaque(x+dx,y+dy) and s.px[y+dy][x+dx]!=col
                           for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                        add.append((x,y))
        for x,y in add: s.px[y][x]=col
    def img(s):
        im=Image.new("RGBA",(T,T))
        for y in range(T):
            for x in range(T): im.putpixel((x,y),s.px[y][x])
        return im

C=lambda k:CLR[k]

# ── 다리/팔 위상 (프레임별 오프셋) ──
def gait(frame):
    bob=[0,-1,0,-1][frame]
    legL=[0,-2,0,0][frame]   # 왼발 들림(정면)
    legR=[0,0,0,-2][frame]   # 오른발 들림
    armF=[0,1,0,-1][frame]   # 팔 스윙
    return bob,legL,legR,armF

def head_front(t,cx,top,back=False):
    # 머리(스킨) + 머리카락
    t.rect(cx-4,top+2,cx+3,top+8,C('SKIN'))
    t.rect(cx+3,top+3,cx+3,top+7,C('SKINSH'))          # 우측 음영
    # 머리카락
    t.rect(cx-4,top,cx+3,top+3,C('HAIR'))
    t.rect(cx-4,top+3,cx-3,top+5,C('HAIR'))            # 옆머리 좌
    t.rect(cx+2,top+3,cx+3,top+5,C('HAIR'))            # 옆머리 우
    t.set(cx-4,top, C('HAIRHI')); t.set(cx-3,top,C('HAIRHI'))
    if back:
        # 뒤통수: 머리 전체 덮음
        t.rect(cx-4,top,cx+3,top+8,C('HAIR'))
        t.rect(cx-4,top+1,cx-2,top+2,C('HAIRHI'))
        t.rect(cx-4,top+8,cx+3,top+9,C('SKIN'))        # 목덜미 살짝

def face_front(t,cx,top):
    t.set(cx-2,top+5,C('EYE')); t.set(cx-2,top+6,C('EYE'))
    t.set(cx+1,top+5,C('EYE')); t.set(cx+1,top+6,C('EYE'))
    t.set(cx-3,top+7,C('BLUSH')); t.set(cx+2,top+7,C('BLUSH'))
    t.set(cx-1,top+8,C('SKINSH')); t.set(cx,top+8,C('SKINSH'))  # 입

def body_front(t,cx,bob,armF):
    yt=15+bob
    # 몸통(후디)
    t.rect(cx-4,yt,cx+3,yt+8,C('TOP'))
    t.rect(cx+2,yt,cx+3,yt+8,C('TOPSH'))      # 우측 음영
    t.rect(cx-4,yt,cx-4,yt+8,C('TOPHI'))      # 좌측 하이라이트
    t.rect(cx-1,yt,cx,yt+1,C('TOPSH'))        # 후드 끈 자리
    # 잎 엠블럼
    t.set(cx,yt+4,C('LEAF')); t.set(cx-1,yt+4,C('LEAF')); t.set(cx,yt+5,C('LEAF'))
    # 팔
    t.rect(cx-6,yt+1+armF,cx-5,yt+6+armF,C('TOP')); t.set(cx-6,yt+7+armF,C('SKIN'))
    t.rect(cx+4,yt+1-armF,cx+5,yt+6-armF,C('TOP')); t.set(cx+5,yt+7-armF,C('SKIN'))

def legs_front(t,cx,bob,legL,legR):
    yt=23+bob
    # 왼다리
    t.rect(cx-3,yt,cx-1,yt+4+legL,C('PANTS')); t.rect(cx-3,yt+5+legL,cx-1,yt+6+legL,C('SHOE'))
    # 오른다리
    t.rect(cx+1,yt,cx+3,yt+4+legR,C('PANTSSH')); t.rect(cx+1,yt+5+legR,cx+3,yt+6+legR,C('SHOE'))

def build_down(frame,back=False):
    t=Tile(); cx=16; bob,legL,legR,armF=gait(frame)
    legs_front(t,cx,bob,legL,legR)
    body_front(t,cx,bob,armF)
    head_front(t,cx,5+bob,back=back)
    t.outline(C('OUT'))
    if not back: face_front(t,cx,5+bob)
    return t.img()

def build_side(frame):
    t=Tile(); cx=16; bob,legL,legR,armF=gait(frame)
    # 측면 스텝: 앞다리/뒷다리 교차
    split=[0,2,0,2][frame]; lead=[1,1,1,-1][frame]   # lead 방향 토글
    yt=23+bob
    # 뒷다리
    bx=cx-2-split*lead
    t.rect(bx-1,yt,bx+1,yt+4,C('PANTSSH')); t.rect(bx-1,yt+5,bx+2,yt+6,C('SHOE'))
    # 앞다리
    fx=cx+1+split*lead
    t.rect(fx-1,yt,fx+1,yt+4,C('PANTS')); t.rect(fx-1,yt+5,fx+2,yt+6,C('SHOE'))
    # 몸통(측면)
    bt=15+bob
    t.rect(cx-3,bt,cx+3,bt+8,C('TOP'))
    t.rect(cx-3,bt,cx-2,bt+8,C('TOPSH'))      # 등쪽 음영
    t.rect(cx+3,bt,cx+3,bt+8,C('TOPHI'))      # 앞쪽 하이라이트
    t.set(cx+1,bt+4,C('LEAF'))
    # 가까운 팔(스윙)
    ax=cx; t.rect(ax,bt+2+armF,ax+1,bt+6+armF,C('TOPSH')); t.set(ax,bt+7+armF,C('SKIN'))
    # 머리(측면, 우향)
    ht=6+bob
    t.rect(cx-3,ht+2,cx+3,ht+8,C('SKIN'))
    t.rect(cx+3,ht+3,cx+3,ht+7,C('SKINSH'))
    t.rect(cx-4,ht,cx+2,ht+4,C('HAIR'))       # 머리카락(위~뒤)
    t.rect(cx-4,ht+4,cx-3,ht+8,C('HAIR'))     # 뒷머리
    t.set(cx-4,ht,C('HAIRHI'))
    t.set(cx+4,ht+5,C('SKIN'))                # 코
    t.outline(C('OUT'))
    # 눈 1개(앞쪽)
    t.set(cx+2,ht+5,C('EYE')); t.set(cx+2,ht+6,C('EYE'))
    t.set(cx+1,ht+7,C('BLUSH'))
    return t.img()

def main():
    sheet=Image.new("RGBA",(COLS*T,ROWS*T))
    for f in range(COLS):
        sheet.paste(build_down(f),       (f*T,0*T))
        sheet.paste(build_side(f),       (f*T,1*T))
        sheet.paste(build_down(f,back=True),(f*T,2*T))
    out=OUTDIR/"hero.png"; sheet.save(out)
    # 미리보기(확대)
    sheet.resize((COLS*T*SCALE_PREVIEW,ROWS*T*SCALE_PREVIEW),Image.NEAREST).save(OUTDIR/"hero_preview.png")
    data=out.read_bytes()
    b64="data:image/png;base64,"+base64.b64encode(data).decode()
    html=GAME.read_text(encoding="utf-8")
    if 'const HERO_SRC=' in html:
        html=re.sub(r'const HERO_SRC="[^"]*";', 'const HERO_SRC="'+b64+'";', html, count=1)
        GAME.write_text(html,encoding="utf-8")
        print("index.html HERO_SRC 주입 완료")
    else:
        print("!! HERO_SRC 자리표시자가 없습니다. index.html에 먼저 추가하세요.")
    print(f"hero.png {sheet.size}  {len(data)} bytes")

if __name__=="__main__":
    main()
