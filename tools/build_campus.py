#!/usr/bin/env python3
"""
순천대 실제 캠퍼스맵 → 아이소메트릭 그리드 생성 + index.html 주입
- 제공된 캠퍼스맵의 라벨 화면좌표(px,py)를 아이소 그리드(gx,gy)로 변환
- A1~F4 전체 건물 + 운동장/체육관/정문·남문·북문/도로/연못/정원 배치
- 마스코트 픽셀 스프라이트(base64) 주입
- game/index.html 의 마커 블록을 치환
실행:  python3 tools/build_campus.py
"""
import json, re, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "game/index.html"
PX   = json.loads((ROOT / "assets/mascots/sprites_px_b64.json").read_text())

# (code, name, px, py, w, d, h, cat, icon, kind)
# kind: build | gate | court(평면)
B = [   # px,py = 실제 캠퍼스맵 핀 좌표(2026-06 정밀 지도 기준)
 ("A1","대학본부",940,740,4,3,108,"G","🏛️","build"),
 ("A2","약학대학",965,605,3,3,92,"E","💊","build"),
 ("A3","천연물신약연구소",900,610,3,2,78,"E","🧪","build"),
 ("A4","학생생활관 부속동",855,855,2,2,66,"S","🏠","build"),
 ("A5","학생생활관 진리관",1010,865,2,3,92,"S","🏠","build"),
 ("A6","학생생활관 창조관",720,970,2,3,92,"S","🏠","build"),
 ("A7","학생생활관 관리동",855,940,2,2,66,"S","🏠","build"),
 ("A8","학생생활관 향림관",1000,1015,2,3,92,"S","🏠","build"),
 ("A9","학생생활관 청운관",855,1100,2,3,92,"S","🏠","build"),
 ("A10","인재관",740,1080,2,2,78,"S","🎓","build"),
 ("A11","제2중앙공급실",690,1075,2,2,56,"G","🔧","build"),
 ("A12","우정원",715,1130,2,2,66,"S","🏡","build"),
 ("A13","웅지관",1160,1040,3,3,98,"S","🏫","build"),
 ("A14","남문",1110,1085,2,2,38,"S","🚪","gate"),
 ("A16","교직원테니스장",1370,985,3,2,14,"S","🎾","court"),
 ("A17","체육관",1465,870,3,3,68,"S","🏟️","build"),
 ("A18","체육관 증축동",1465,950,2,2,52,"S","🏟️","build"),
 ("A19","정문",1460,685,3,2,40,"S","🚪","gate"),
 ("B1","박물관",1340,485,3,3,78,"S","🏺","build"),
 ("B2","70주년기념관",1180,480,3,3,88,"S","🏛️","build"),
 ("B3","생명산업과학대학1호관",1190,330,4,3,98,"E","🌾","build"),
 ("B4","생명산업과학대학2호관",1000,380,3,3,92,"E","🌾","build"),
 ("B5","생명과학 온실",1040,320,3,2,38,"E","🪴","build"),
 ("B6","제1중앙공급실",940,290,2,2,56,"G","🔧","build"),
 ("B7","산학협력관",1340,205,4,3,88,"G","🤝","build"),
 ("C1","중앙도서관",685,425,4,3,118,"E","📚","build"),
 ("C2","친환경농업센터",795,240,3,2,72,"E","🌱","build"),
 ("C3","공동실험실습관",685,215,3,2,78,"E","🔬","build"),
 ("C4","환경친화형물질공장기술혁신센터",740,185,3,2,72,"E","🏭","build"),
 ("C5","어린이집",685,120,2,2,52,"S","🧸","build"),
 ("C6","북문",610,100,2,2,38,"S","🚪","gate"),
 ("D1","창업보육센터",570,175,3,2,80,"G","🚀","build"),
 ("D2","공과대학1호관",425,170,3,3,108,"G","⚙️","build"),
 ("D3","공과대학2호관",310,390,3,3,108,"G","⚙️","build"),
 ("D4","공과대학3호관",140,345,4,3,118,"G","⚙️","build"),
 ("D5","학군단",280,220,2,2,58,"G","🎖️","build"),
 ("E1","학생회관",730,565,3,3,92,"S","🏫","build"),
 ("E2","기초교육관",645,785,3,3,98,"S","📖","build"),
 ("E3","사범대학1호관",505,525,3,3,98,"S","🎒","build"),
 ("E4","사범대학2호관",525,460,3,3,98,"S","🎒","build"),
 ("E5","사범대학3호관",470,730,3,3,98,"S","🎒","build"),
 ("E6","미래창조관",560,990,3,3,104,"G","💡","build"),
 ("E7","사회과학대학",375,940,4,3,108,"S","⚖️","build"),
 ("E8","인문예술대학",280,660,4,3,108,"S","🎨","build"),
 ("F1","국제문화컨벤션관",1540,1140,4,3,90,"S","🎪","build"),
 ("F2","평생교육원",1450,1130,3,3,88,"S","📚","build"),
 ("F3","학생테니스장",1390,1220,3,2,14,"S","🎾","court"),
 ("F4","연립관사",1400,1340,3,2,68,"S","🏘️","build"),
]
# 운동장(트랙) 중심 — A15
FIELD = (1215,845)
FIELD_W, FIELD_D = 12, 9   # 운동장 타일 크기(가로/세로)

# ── 화면좌표 → 아이소 그리드 변환 (값↓ = 맵 더 넓게) ──────────
SX, PX0 = 13.5, 820.0     # u = (px-PX0)/SX  (= gx-gy)
SY, PY0 = 9.0, 100.0      # v = (py-PY0)/SY  (= gx+gy)
def to_grid(px, py):
    u = (px-PX0)/SX
    v = (py-PY0)/SY
    return (v+u)/2.0, (v-u)/2.0   # gx, gy

raw = []
for code,name,px,py,w,d,h,cat,icon,kind in B:
    gx,gy = to_grid(px,py)
    raw.append([code,name,gx,gy,w,d,h,cat,icon,kind])
fgx,fgy = to_grid(*FIELD)

# 정규화(여백 MARGIN)
MARGIN = 8
minx = min(r[2] for r in raw); miny = min(r[3] for r in raw)
minx = min(minx, fgx-4); miny = min(miny, fgy-3)
def nx(gx): return int(round(gx-minx))+MARGIN
def ny(gy): return int(round(gy-miny))+MARGIN

builds = []
by_code = {}
for code,name,gx,gy,w,d,h,cat,icon,kind in raw:
    x,y = nx(gx), ny(gy)
    rec = dict(id=code.lower(),code=code,name=name,gx=x,gy=y,w=w,d=d,h=h,
               cat=cat,icon=icon,kind=kind)
    builds.append(rec); by_code[code]=rec
FX, FY = nx(fgx), ny(fgy)

GW = max(b["gx"]+b["w"] for b in builds) + MARGIN + 2
GH = max(b["gy"]+b["d"] for b in builds) + MARGIN + 2
GW = max(GW, FX+FIELD_W); GH = max(GH, FY+FIELD_D)

# ── 색상(카테고리별 팔레트, 도트친화) ──────────────────────
PAL = {
 "E": dict(top="#cfeae0",l="#7fb8a8",r="#a6d2c4",roof="#3f7d6e"),
 "S": dict(top="#f7d9e2",l="#d68fa6",r="#e8b4c4",roof="#a8506a"),
 "G": dict(top="#d8def0",l="#8f9ed0",r="#b3bfe4",roof="#566190"),
}
GATE = dict(top="#e6ddc8",l="#b6a886",r="#cebfa0",roof="#7d6a48")
COURT= dict(top="#7fae5e",l="#5f8a46",r="#6fa052",roof="#4d7038")

for b in builds:
    p = GATE if b["kind"]=="gate" else COURT if b["kind"]=="court" else PAL[b["cat"]]
    b.update(p)
    b["solar"] = b["cat"]=="E" and b["kind"]=="build" and b["h"]>70
    b["poi"] = f'{b["name"]} · {{"E":"환경(E)","S":"사회(S)","G":"지배구조(G)"}} 미션 거점.'

# poi 텍스트(카테고리 한글)
catko = {"E":"환경(E)","S":"사회(S)","G":"지배구조(G)"}
for b in builds:
    b["poi"] = f'{b["code"]} {b["name"]} — {catko[b["cat"]]} 실천 거점입니다.'

# ── 지면(ground) 연산 리스트 [x0,y0,x1,y1,type] ───────────
# type: 0잔디 1광장 2길 3물 4정원 5운동장
ops = []
def rect(x0,y0,x1,y1,t): ops.append([int(x0),int(y0),int(x1),int(y1),t])

# 운동장(트랙) 영역
HFW, HFD = FIELD_W//2, FIELD_D//2
rect(FX-HFW,FY-HFD,FX+HFW,FY+HFD,5)

# 중앙 광장: A1·E1·C1 무게중심 부근
cx = round((by_code["A1"]["gx"]+by_code["E1"]["gx"]+by_code["C1"]["gx"])/3)
cy = round((by_code["A1"]["gy"]+by_code["E1"]["gy"]+by_code["C1"]["gy"])/3)
rect(cx-3,cy-2,cx+3,cy+2,1)
# 연못
rect(cx+1,cy-1,cx+2,cy+0,3)
# 정원(도서관~농업센터 사이)
gx0=min(by_code["C1"]["gx"],by_code["C2"]["gx"]);
rect(by_code["C2"]["gx"]-1,by_code["C2"]["gy"]+2,by_code["C2"]["gx"]+1,by_code["C2"]["gy"]+3,4)

# 도로: L자 코리도(폭2)로 주요 노드 연결
def road(a,b,wd=1):
    ax,ay=a; bx,by=b
    rect(min(ax,bx),ay,max(ax,bx),ay+wd,2)   # 수평
    rect(bx,min(ay,by),bx+wd,max(ay,by),2)   # 수직
gate=(by_code["A19"]["gx"],by_code["A19"]["gy"])
nm  =(by_code["A14"]["gx"],by_code["A14"]["gy"])
bm  =(by_code["C6"]["gx"], by_code["C6"]["gy"])
ctr=(cx,cy)
road(gate,ctr); road(ctr,nm); road(ctr,bm)
road(ctr,(by_code["E5"]["gx"],by_code["E5"]["gy"]))
road(ctr,(by_code["D4"]["gx"],by_code["D4"]["gy"]))
road(ctr,(by_code["B3"]["gx"],by_code["B3"]["gy"]))
road((by_code["A13"]["gx"],by_code["A13"]["gy"]),(by_code["A17"]["gx"],by_code["A17"]["gy"]))
road(nm,(by_code["F2"]["gx"],by_code["F2"]["gy"]))
# 둘레 산책로(맵 전체를 도는 루프) — 넓은 이동 공간
BR=4
rect(BR,BR,GW-1-BR,BR+1,2); rect(BR,GH-2-BR,GW-1-BR,GH-1-BR,2)   # 상/하
rect(BR,BR,BR+1,GH-1-BR,2); rect(GW-2-BR,BR,GW-1-BR,GH-1-BR,2)   # 좌/우

# ── NPC(마스코트) ─────────────────────────────────────────
def near(code,dx,dy):
    b=by_code[code]; return b["gx"]+dx, b["gy"]+dy
npcs=[
 dict(id="chong",name="총장님",kind="G",img="chong",gx=by_code["A1"]["gx"]-1,gy=by_code["A1"]["gy"]+by_code["A1"]["d"]+1,sc=0.92),
 dict(id="cheri",name="체리니",kind="S",img="cheri",gx=cx-2,gy=cy+1,sc=0.86),
 dict(id="usong",name="우송이",kind="E",img="usong",gx=by_code["C1"]["gx"]-1,gy=by_code["C1"]["gy"]+by_code["C1"]["d"]+1,sc=0.88),
]
# 광장 중심 좌표(플레이어/상호작용)
PLAZA=(cx, cy)
player=dict(gx=gate[0]+1, gy=gate[1]-1)

# ── SDG 간판 ──────────────────────────────────────────────
sdg=[
 dict(gx=by_code["C1"]["gx"]+by_code["C1"]["w"],gy=by_code["C1"]["gy"]+1,n=4,c="#C5192D",label="양질의 교육"),
 dict(gx=by_code["C2"]["gx"],gy=by_code["C2"]["gy"]+3,n=15,c="#56C02B",label="육상 생태"),
 dict(gx=by_code["B4"]["gx"]+1,gy=by_code["B4"]["gy"]+3,n=2,c="#DDA63A",label="기아 종식"),
 dict(gx=by_code["D2"]["gx"]-1,gy=by_code["D2"]["gy"]+3,n=9,c="#FD6925",label="산업·혁신"),
 dict(gx=cx,gy=cy-2,n=11,c="#FD9D24",label="지속가능 도시"),
 dict(gx=by_code["A1"]["gx"]+by_code["A1"]["w"],gy=by_code["A1"]["gy"],n=16,c="#00689D",label="제도·정의"),
]

# ── 데코 ──────────────────────────────────────────────────
rng=random.Random(7)
footprint=set()
for b in builds:
    for yy in range(b["gy"]-1,b["gy"]+b["d"]+1):
        for xx in range(b["gx"]-1,b["gx"]+b["w"]+1):
            footprint.add((xx,yy))
roadset=set()
for x0,y0,x1,y1,t in ops:
    if t in (1,2,3,5):
        for yy in range(y0,y1+1):
            for xx in range(x0,x1+1):
                roadset.add((xx,yy))
decor=[]
# 가로수: 도로 가장자리
for x0,y0,x1,y1,t in ops:
    if t!=2: continue
    for (xx,yy) in [(x0-1,y0),(x1+1,y1),(x0,y0-1),(x1,y1+1)]:
        if (xx,yy) not in footprint and 1<xx<GW-1 and 1<yy<GH-1 and rng.random()<0.5:
            decor.append(dict(t="tree",gx=xx,gy=yy,r=rng.random()))
# 빈 잔디 가로수
placed={(d["gx"],d["gy"]) for d in decor}
tries=0
while sum(1 for d in decor if d["t"]=="tree")<420 and tries<20000:
    tries+=1
    xx=rng.randint(2,GW-3); yy=rng.randint(2,GH-3)
    if (xx,yy) in footprint or (xx,yy) in roadset or (xx,yy) in placed: continue
    placed.add((xx,yy)); decor.append(dict(t="tree",gx=xx,gy=yy,r=rng.random()))
# 광장 편의시설
decor.append(dict(t="fountainGarden",gx=cx,gy=cy))
for dxy in [(-2,-1),(2,1),(-2,1),(2,-1)]:
    decor.append(dict(t="bench",gx=cx+dxy[0],gy=cy+dxy[1]))
for dxy in [(-3,0),(3,0),(0,-2),(0,2)]:
    decor.append(dict(t="lamp",gx=cx+dxy[0],gy=cy+dxy[1]))
decor.append(dict(t="bins",gx=cx-1,gy=cy+2))
decor.append(dict(t="sign",gx=cx,gy=cy+2,txt="분리수거"))
for i in range(6):
    decor.append(dict(t="flower",gx=by_code["C2"]["gx"]-1+i%3,gy=by_code["C2"]["gy"]+2+i//3))
# 운동장 트랙(스타디움)
decor.append(dict(t="stadium",gx=FX,gy=FY,fw=FIELD_W,fd=FIELD_D))

# ── JS 직렬화 ────────────────────────────────────────────
def js(o): return json.dumps(o, ensure_ascii=False)

data_js = f"""// ===== AUTO-GENERATED CAMPUS (build_campus.py) =====
const GW={GW}, GH={GH};
const PLAZA={{gx:{PLAZA[0]}, gy:{PLAZA[1]}}};
const GROUND_OPS={js(ops)};
const buildings={js([{k:b[k] for k in ['id','name','code','cat','icon','gx','gy','w','d','h','solar','top','l','r','roof','poi','kind']} for b in builds])};
const npcs={js(npcs)};
const sdg={js(sdg)};
const DECOR={js(decor)};
const PLAYER_SPAWN={js(player)};
// ===== END AUTO-GENERATED =====
"""

html = GAME.read_text(encoding="utf-8")

# 0) 구조 스캐폴딩(최초 1회): 기존 정적 데이터 영역 → 자동생성 마커 블록
if "/*CAMPUS_DATA_START*/" not in html:
    # GW/GH 는 자동생성 블록으로 이동
    html = html.replace(
        "const TW=64, TH=32, HW=32, HH=16, GW=30, GH=30;",
        "const TW=64, TH=32, HW=32, HH=16;")
    scaffold = """/*CAMPUS_DATA_START*/
/*CAMPUS_DATA_END*/
function setRect(arr,x0,y0,x1,y1,v){for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++) if(arr[y]&&x>=0&&x<GW)arr[y][x]=v;}
const ground=[]; for(let y=0;y<GH;y++){ground.push(new Array(GW).fill(0));}
GROUND_OPS.forEach(o=>setRect(ground,o[0],o[1],o[2],o[3],o[4]));
const decor=DECOR;
const crowd=[]; (function(){ let s=99; const R=()=>{s=(s*1103515245+12345)&0x7fffffff;return s/0x7fffffff;};
 const cols=['#c45a6a','#5a8fd6','#6aae6a','#b08fd0','#d0a85a','#5ab0a8','#d07a9a','#7a8fd0'];
 for(let i=0;i<10;i++){ const gx=PLAZA.gx-3+R()*6, gy=PLAZA.gy-2+R()*4; crowd.push({gx,gy,tx:gx,ty:gy,c:cols[i%cols.length],hair:['#3a2a1a','#5a3a20','#222'][i%3],t:R()*100,dir:'down'}); }})();
const blockedTiles=new Set();
buildings.forEach(b=>{ if(b.kind==='court')return; for(let y=b.gy;y<b.gy+b.d;y++)for(let x=b.gx;x<b.gx+b.w;x++)blockedTiles.add(x+','+y);});
for(let y=0;y<GH;y++)for(let x=0;x<GW;x++) if(ground[y][x]===3) blockedTiles.add(x+','+y);
function blocked(gx,gy){ return blockedTiles.has(Math.floor(gx)+','+Math.floor(gy)); }
const player={gx:PLAYER_SPAWN.gx,gy:PLAYER_SPAWN.gy, spd:0.11, dir:'S', moving:false, t:0};"""
    # 기존 정적 데이터 영역(앵커 사이) 통째 치환
    pat = re.compile(
        r"const ground=\[\]; for\(let y=0;y<GH;y\+\+\)\{ground\.push\(new Array\(GW\)\.fill\(0\)\);\}.*?"
        r"const player=\{gx:15,gy:23, spd:0\.08, dir:'down', moving:false, t:0\};",
        re.S)
    if not pat.search(html):
        raise SystemExit("!! 정적 데이터 영역 앵커를 찾지 못했습니다.")
    html = pat.sub(lambda m: scaffold, html)

# 1) 마스코트 스프라이트 주입
for key in ("usong","cheri","chong"):
    html = re.sub(rf'({key}:")data:image/png;base64,[^"]*(")',
                  lambda m,k=key: m.group(1)+PX[k]+m.group(2), html, count=1)

# 2) 데이터 블록 치환 (마커 사이)
if "/*CAMPUS_DATA_START*/" in html:
    html = re.sub(r"/\*CAMPUS_DATA_START\*/.*?/\*CAMPUS_DATA_END\*/",
                  "/*CAMPUS_DATA_START*/\n"+data_js+"/*CAMPUS_DATA_END*/",
                  html, flags=re.S)
else:
    print("!! 마커(/*CAMPUS_DATA_START*/)가 없습니다. index.html에 먼저 추가하세요.")

GAME.write_text(html, encoding="utf-8")
print(f"GW={GW} GH={GH}  buildings={len(builds)}  npcs={len(npcs)}  decor={len(decor)}")
print(f"plaza=({cx},{cy})  field=({FX},{FY})  spawn={player}")
print("index.html 주입 완료")
