#!/usr/bin/env python3
"""
마스코트 스프라이트 빌드 파이프라인
- assets/mascots/source/*.ai (Adobe Illustrator = PDF 호환) 에서 히어로 포즈를 추출
- 흰 배경 투명화 → 게임용 높이로 리사이즈 → 64색 퀀타이즈
- PNG 저장 + base64 data URI(JSON) 생성
- game/index.html 의 __USONG__ / __CHERI__ / __CHONG__ 플레이스홀더(또는 기존 data URI)를 교체

요구: pdftoppm(poppler-utils), Pillow
  sudo apt-get install poppler-utils  /  pip install pillow
실행:  python tools/build_sprites.py
"""
import base64, json, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "assets/mascots/source"
OUT  = ROOT / "assets/mascots"
GAME = ROOT / "game/index.html"

# (소스파일 키워드, 출력키, 히어로영역 crop[150dpi 기준 x0,y0,x1,y1])
JOBS = {
    "usong": ("우송이", (90, 255, 790, 1130)),
    "cheri": ("체리니", (95, 250, 780, 1080)),
    "chong": ("총장님", (120, 250, 800, 1135)),
}
TARGET_H = 240   # 게임 스프라이트 높이(px)
QUANT    = 64    # 퀀타이즈 색상 수

def find_ai(keyword):
    for p in SRC.glob("*.ai"):
        if keyword in p.name:
            return p
    raise FileNotFoundError(f"{keyword} .ai 파일을 찾지 못했습니다 ({SRC})")

def render(ai_path, dpi=150):
    stem = OUT / ("_tmp_" + ai_path.stem)
    subprocess.run(["pdftoppm","-png","-r",str(dpi),"-f","1","-l","1",str(ai_path),str(stem)],
                   check=True)
    return Path(str(stem) + "-1.png")

def process(png, region, target_h=TARGET_H):
    x0,y0,x1,y1 = region
    im = Image.open(png).crop((x0,y0,x1,y1)).convert("RGBA")
    px = im.load(); w,h = im.size
    # 비흰색 타이트 bbox
    minx,miny,maxx,maxy = w,h,0,0
    for y in range(h):
        for x in range(w):
            r,g,b,a = px[x,y]
            if not (r>240 and g>240 and b>240):
                minx=min(minx,x);maxx=max(maxx,x);miny=min(miny,y);maxy=max(maxy,y)
    im = im.crop((max(0,minx-6),max(0,miny-6),min(w,maxx+6),min(h,maxy+6)))
    # 흰 배경 투명화
    px = im.load(); w,h = im.size
    for y in range(h):
        for x in range(w):
            r,g,b,a = px[x,y]
            if r>242 and g>242 and b>242: px[x,y]=(r,g,b,0)
    nw = int(w*target_h/h)
    im = im.resize((nw,target_h), Image.LANCZOS)
    return im.quantize(colors=QUANT, method=Image.FASTOCTREE).convert("RGBA")

def main():
    b64 = {}
    for key,(kw,region) in JOBS.items():
        ai = find_ai(kw)
        png = render(ai)
        sprite = process(png, region)
        out_png = OUT / f"{key}.png"
        sprite.save(out_png, optimize=True)
        data = out_png.read_bytes()
        b64[key] = "data:image/png;base64," + base64.b64encode(data).decode()
        try: png.unlink()
        except OSError: pass
        print(f"  {key}: {sprite.size}  {len(data)} bytes")
    (OUT/"sprites_b64.json").write_text(json.dumps(b64))
    # index.html 주입: 플레이스홀더(__USONG__ 등) 또는 기존 data URI를 교체
    import re
    html = GAME.read_text(encoding="utf-8")
    for key in JOBS:
        ph = "__" + key.upper() + "__"
        if ph in html:
            html = html.replace(ph, b64[key])
        else:
            # 예: usong:"data:image/png;base64,...."  ->  새 data URI
            html = re.sub(rf'({key}:")data:image/png;base64,[^"]*(")',
                          lambda m, k=key: m.group(1) + b64[k] + m.group(2), html)
    GAME.write_text(html, encoding="utf-8")
    print("game/index.html 스프라이트 주입 완료")

if __name__ == "__main__":
    main()
