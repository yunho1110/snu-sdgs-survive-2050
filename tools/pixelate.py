#!/usr/bin/env python3
"""
마스코트 픽셀아트 변환
- 공식 일러스트 PNG(usong/cheri/chong)를 진짜 도트 느낌으로 재구성
- 가장자리 흰배경 flood-fill 투명화 → 타이트 크롭 → 저해상 다운스케일(NEAREST)
  → 팔레트 양자화 → 외곽 1px 다크라인 강조 → 작은 PNG 저장
- 게임은 image-rendering:pixelated 로 확대하므로 소스는 작게 유지(높이 ~48px)
요구: Pillow
실행:  python3 tools/pixelate.py
"""
import base64, json
from collections import deque
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "assets/mascots"
KEYS = ["usong", "cheri", "chong"]
TARGET_H = 52     # 도트 소스 높이(px)

# 씬과 통일된 따뜻·저채도 마스코트 팔레트(가장 가까운 색으로 매핑)
PALETTE = [
    (43, 34, 48),    # 외곽선 plum-black
    (244, 239, 230), # 화이트
    (122, 186, 150), # 우송이 청록 밝음
    (104, 168, 156), # 청록 중간
    (74, 134, 123),  # 청록
    (50, 100, 92),   # 청록 그림자
    (107, 157, 106), # 잎 그린 밝음
    (79, 129, 86),   # 그린 중간
    (232, 182, 194), # 체리니 핑크 밝음
    (217, 143, 166), # 핑크 중간
    (181, 103, 126), # 핑크 그림자
    (240, 216, 168), # 총장님 크림 밝음
    (224, 176, 106), # 크림/주황 중간
    (201, 138, 74),  # 주황 그림자
    (138, 90, 58),   # 갈색(다리/줄기)
    (102, 64, 42),   # 진갈색
    (95, 143, 191),  # 블루 액센트(배지/눈)
    (63, 106, 150),  # 진블루
    (232, 154, 134), # 볼 터치
]

def nearest(c):
    r, g, b = c
    best, bi = 1e9, 0
    for i, (pr, pg, pb) in enumerate(PALETTE):
        dd = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
        if dd < best:
            best, bi = dd, i
    return PALETTE[bi]

def remove_bg(im):
    """가장자리에서 연결된 흰색 영역만 투명화(내부 흰 하이라이트 보존)."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    def whiteish(p):
        r, g, b, a = p
        return a > 10 and r > 236 and g > 236 and b > 236
    seen = [[False]*w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h-1):
            q.append((x, y))
    for y in range(h):
        for x in (0, w-1):
            q.append((x, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y][x]:
            continue
        seen[y][x] = True
        if not whiteish(px[x, y]):
            continue
        px[x, y] = (255, 255, 255, 0)
        q.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    return im

def tight_crop(im):
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im

def add_outline(im):
    """알파가 있는 픽셀의 바깥 경계에 진한 외곽선 1px(도트 느낌)."""
    w, h = im.size
    px = im.load()
    line = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] < 40:
                # 이웃에 불투명 픽셀이 있으면 외곽선 후보
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 150:
                        line.append((x, y)); break
    for x, y in line:
        px[x, y] = (38, 52, 74, 255)
    return im

def process(src):
    im = remove_bg(Image.open(src))
    im = tight_crop(im)
    w, h = im.size
    nw = max(1, round(w * TARGET_H / h))
    small = im.resize((nw, TARGET_H), Image.NEAREST).convert("RGBA")
    # 고정 팔레트 nearest 매핑 + 알파 이진화
    px = small.load()
    for y in range(TARGET_H):
        for x in range(nw):
            r, g, b, al = px[x, y]
            if al < 110:
                px[x, y] = (255, 255, 255, 0)
            else:
                nr, ng, nb = nearest((r, g, b))
                px[x, y] = (nr, ng, nb, 255)
    small = add_outline(small)
    return small

def main():
    b64 = {}
    for key in KEYS:
        src = OUT / f"{key}.png"
        sprite = process(src)
        out = OUT / f"{key}_px.png"
        sprite.save(out, optimize=True)
        data = out.read_bytes()
        b64[key] = "data:image/png;base64," + base64.b64encode(data).decode()
        print(f"  {key}: {sprite.size}  {len(data)} bytes")
    (OUT / "sprites_px_b64.json").write_text(json.dumps(b64))
    print("저장: assets/mascots/*_px.png, sprites_px_b64.json")

if __name__ == "__main__":
    main()
