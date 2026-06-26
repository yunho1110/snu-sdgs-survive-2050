#!/usr/bin/env python3
"""
마스코트 전용 워크 스프라이트시트 생성기 (우송이/체리니/총장님)
- 32x40 타일, 3행(down/side(우향)/up) x 4열(걷기 프레임)
- 각 마스코트의 시그니처 실루엣을 도트로 작도 + 외곽선 자동 + 걷기(다리 셔플·반동)
- assets/mascots/<key>_sheet.png 저장 + base64를 index.html MASCOT_SHEETS 에 주입
실행:  python3 tools/build_mascots.py
"""
import base64, json, re
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"assets/mascots"; GAME=ROOT/"game/index.html"
TW,TH=32,40; COLS,ROWS=4,3; PREV=6
OUTLINE=(43,34,48,255); EYE=(43,34,48,255); BLUSH=(232,154,134,255); WHITE=(245,240,232,255); NONE=(0,0,0,0)

PAL=dict(
 usong=dict(body=(104,168,156,255),sh=(74,134,123,255),hi=(150,196,150,255),leg=(150,110,80,255),legsh=(120,84,58,255)),
 cheri=dict(body=(232,160,182,255),sh=(205,120,150,255),hi=(246,202,214,255),leg=(214,150,92,255),legsh=(176,116,70,255)),
 chong=dict(body=(242,216,168,255),sh=(216,180,130,255),hi=(250,236,202,255),leg=(226,196,150,255),legsh=(196,164,120,255)),
)

class Tile:
    def __init__(s): s.px=[[NONE]*TW for _ in range(TH)]
    def set(s,x,y,c):
        if 0<=x<TW and 0<=y<TH and c[3]>0: s.px[int(y)][int(x)]=c
    def rect(s,x0,y0,x1,y1,c):
        for y in range(int(y0),int(y1)+1):
            for x in range(int(x0),int(x1)+1): s.set(x,y,c)
    def op(s,x,y): return 0<=x<TW and 0<=y<TH and s.px[y][x][3]>0
    def outline(s):
        add=[]
        for y in range(TH):
            for x in range(TW):
                if s.px[y][x][3]==0 and any(s.op(x+dx,y+dy) and s.px[y+dy][x+dx]!=OUTLINE for dx,dy in((1,0),(-1,0),(0,1),(0,-1))):
                    add.append((x,y))
        for x,y in add: s.px[y][x]=OUTLINE
    def img(s):
        im=Image.new("RGBA",(TW,TH))
        for y in range(TH):
            for x in range(TW): im.putpixel((x,y),s.px[y][x])
        return im

def gait(f): return [0,-1,0,-1][f], [0,-2,0,0][f], [0,0,0,-2][f]   # bob, legL, legR

def legs(t,p,cx,base,lL,lR,side=False,split=0):
    if side:
        bx=cx-2; fx=cx+1
        t.rect(bx-1,base,bx,base+4,p['legsh']); t.rect(bx-1,base+5,bx+1,base+6,p['legsh'])
        t.rect(fx,base,fx+1,base+4,p['leg']);   t.rect(fx,base+5,fx+2,base+6,p['leg'])
    else:
        t.rect(cx-3,base,cx-1,base+4+lL,p['legsh']); t.rect(cx-3,base+5+lL,cx-1,base+6+lL,p['legsh'])
        t.rect(cx+1,base,cx+3,base+4+lR,p['leg']);   t.rect(cx+1,base+5+lR,cx+3,base+6+lR,p['leg'])

def shade_col(t,p,x0,y0,x1,y1,back=False):
    t.rect(x0,y0,x1,y1,p['body']); t.rect(x1-1,y0,x1,y1,p['sh']); t.set(x0,y0,p['hi'])

def usong(view,f,p):
    t=Tile(); cx=16; bob,lL,lR=gait(f); top=4+bob
    # 원뿔(낙우송): 위로 갈수록 좁아짐
    rows=[(cx-1,cx+1,top),(cx-3,cx+2,top+3),(cx-5,cx+4,top+7),(cx-7,cx+6,top+12),(cx-8,cx+7,top+17),(cx-9,cx+8,top+22)]
    yprev=top
    for (x0,x1,yy) in rows:
        t.rect(x0,yprev,x1,yy+2,p['body']); yprev=yy
    t.rect(cx-9,top+20,cx+8,top+24,p['body'])
    # 음영/하이라이트
    for (x0,x1,yy) in rows: t.rect(x1-1,yy,x1,yy+3,p['sh'])
    t.rect(cx-9,top+18,cx-7,top+24,p['hi'])
    legs(t,p,cx,top+24,lL,lR,side=(view=='side'))
    # 팔(잔가지)
    t.rect(cx-11,top+15,cx-9,top+17,p['body']); t.rect(cx+9,top+15,cx+11,top+17,p['body'])
    t.outline()
    if view!='up':
        ex=2 if view=='side' else 0
        t.rect(cx-3+ex,top+13,cx-2+ex,top+14,EYE);
        if view!='side': t.rect(cx+2,top+13,cx+3,top+14,EYE)
        t.set(cx-4+ex,top+15,BLUSH);
        if view!='side': t.set(cx+4,top+15,BLUSH)
    return t.img()

def cheri(view,f,p):
    t=Tile(); cx=16; bob,lL,lR=gait(f); top=6+bob
    # 둥근 블롭
    t.rect(cx-7,top+3,cx+6,top+20,p['body'])
    t.rect(cx-5,top,cx+4,top+3,p['body'])
    t.rect(cx-8,top+7,cx-7,top+16,p['body']); t.rect(cx+6,top+7,cx+7,top+16,p['body'])
    t.rect(cx+4,top+3,cx+6,top+20,p['sh']); t.rect(cx-7,top+3,cx-6,top+8,p['hi'])
    # 머리 위 새싹
    t.rect(cx-1,top-3,cx,top,(86,170,90,255)); t.rect(cx+1,top-2,cx+2,top-1,(86,170,90,255))
    legs(t,p,cx,top+20,lL,lR,side=(view=='side'))
    t.rect(cx-9,top+9,cx-7,top+12,p['body']); t.rect(cx+7,top+9,cx+9,top+12,p['body'])  # 팔
    t.outline()
    if view!='up':
        ex=2 if view=='side' else 0
        t.rect(cx-3+ex,top+9,cx-2+ex,top+10,EYE)
        if view!='side': t.rect(cx+2,top+9,cx+3,top+10,EYE)
        t.set(cx-4+ex,top+12,BLUSH)
        if view!='side': t.set(cx+4,top+12,BLUSH)
    return t.img()

def chong(view,f,p):
    t=Tile(); cx=16; bob,lL,lR=gait(f); top=4+bob
    # 귀
    t.rect(cx-6,top,cx-4,top+3,p['body']); t.rect(cx+4,top,cx+6,top+3,p['body'])
    t.set(cx-5,top+1,(232,150,160,255)); t.set(cx+5,top+1,(232,150,160,255))
    # 머리
    t.rect(cx-6,top+2,cx+5,top+11,p['body']); t.rect(cx+4,top+2,cx+5,top+11,p['sh'])
    # 몸통
    t.rect(cx-5,top+11,cx+4,top+22,p['body']); t.rect(cx+3,top+11,cx+4,top+22,p['sh'])
    t.rect(cx-4,top+12,cx-2,top+18,WHITE)  # 배 무늬
    # 꼬리
    if view=='side': t.rect(cx-9,top+16,cx-6,top+18,p['body']); t.rect(cx-11,top+13,cx-9,top+17,p['body'])
    else: t.rect(cx+5,top+16,cx+8,top+18,p['body'])
    legs(t,p,cx,top+22,lL,lR,side=(view=='side'))
    t.rect(cx-8,top+12,cx-6,top+16,p['body']); t.rect(cx+5,top+12,cx+7,top+16,p['body'])  # 앞발
    t.outline()
    if view!='up':
        ex=2 if view=='side' else 0
        t.rect(cx-3+ex,top+6,cx-2+ex,top+7,EYE)
        if view!='side': t.rect(cx+2,top+6,cx+3,top+7,EYE)
        t.set(cx-1,top+8,(232,150,160,255))  # 코
        t.set(cx-4+ex,top+8,BLUSH)
        if view!='side': t.set(cx+4,top+8,BLUSH)
    return t.img()

BUILD=dict(usong=usong,cheri=cheri,chong=chong)
VIEWS=['down','side','up']

def main():
    b64={}
    for key,fn in BUILD.items():
        p=PAL[key]; sheet=Image.new("RGBA",(COLS*TW,ROWS*TH))
        for ri,view in enumerate(VIEWS):
            for f in range(COLS):
                sheet.paste(fn(view,f,p),(f*TW,ri*TH))
        out=OUT/f"{key}_sheet.png"; sheet.save(out)
        sheet.resize((COLS*TW*PREV,ROWS*TH*PREV),Image.NEAREST).save(OUT/f"{key}_sheet_preview.png")
        b64[key]="data:image/png;base64,"+base64.b64encode(out.read_bytes()).decode()
        print(f"  {key}: {sheet.size}")
    html=GAME.read_text(encoding="utf-8")
    js="const MASCOT_SHEETS="+json.dumps(b64)+";"
    if re.search(r'const MASCOT_SHEETS=.*?;',html):
        html=re.sub(r'const MASCOT_SHEETS=.*?;',js,html,count=1,flags=re.S)
    else:
        html=html.replace('const HERO_SRC=', js+'\nconst HERO_SRC=',1)
    GAME.write_text(html,encoding="utf-8")
    print("MASCOT_SHEETS 주입 완료")

if __name__=="__main__": main()
