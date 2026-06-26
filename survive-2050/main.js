/* ═══════════════════════════════════════════════════════════════
   2050 · 멸망 직전 지구에서 살아남기 — main.js
   게임 로직 + 사운드/돌발변수/업적/엔딩 매트릭스 + 저장 레이어.
   data.js(SDG / START / SCENARIOS) 다음에 로드됩니다.
   ═══════════════════════════════════════════════════════════════ */

/* ── 큐 구성: 그룹별 추출 개수 + 위기 tier. 합계 = 10단계 ── */
const QUEUE_PLAN = [
  { group:'early', pick:2, tier:1 },
  { group:'mid',   pick:3, tier:2 },
  { group:'late',  pick:3, tier:3 },
  { group:'final', pick:2, tier:4 },
];
const TOTAL_STAGES = QUEUE_PLAN.reduce((s,p)=>s+p.pick, 0); // 10

/* ── 게임 상태 ── */
let G = {
  currentStep: 0,
  gameQueue: [],
  stats: { temp: START.temp, sea: START.sea, eco: START.eco, score: START.score },
  history: [],
  modifier: null,
  renderingHalted: false,   // 조기 붕괴 시 비동기 렌더 차단 플래그
  rollTimers: [],           // 작동 중 애니메이션 프레임 추적
};
function freshStats(){ return { temp:START.temp, sea:START.sea, eco:START.eco, score:START.score }; }

/* ── 전역 사운드 상태(브라우저 자동재생 정책 대응: 사용자 클릭 후 가동) ── */
let audioCtx = null, bgmInterval = null, currentOscillators = [], soundEnabled = false;

/* ═══════════════ 1. Web Audio 생성형 앰비언트 BGM ═══════════════ */
function initAudio(){
  if(!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if(audioCtx.state === 'suspended') audioCtx.resume();
}
function startAmbientBGM(){
  if(!soundEnabled) return;
  initAudio();
  if(bgmInterval) clearInterval(bgmInterval);
  // 생태계(eco) 상태를 주기적으로 스캔해 화음·파형을 동적으로 모핑
  bgmInterval = setInterval(()=>{
    if(!soundEnabled || G.renderingHalted) return;
    const eco = G.stats.eco;
    let freqs=[130.81,164.81,196.00], type='sine', duration=2.8, gainVal=0.04; // C Major(평화)
    if(eco < 30){ freqs=[116.54,138.59,155.56,207.65]; type='sawtooth'; gainVal=0.015; duration=1.2; }   // 멸망: 불협화 톱니파
    else if(eco < 60){ freqs=[110.00,130.81,164.81,220.00]; type='triangle'; duration=2.0; }              // 경고: 어두운 마이너
    playChordSynth(freqs, type, duration, gainVal);
  }, 2500);
}
function playChordSynth(freqs, type, duration, maxGain){
  if(!audioCtx || audioCtx.state === 'suspended') return;
  const now = audioCtx.currentTime;
  freqs.forEach(f=>{
    const osc = audioCtx.createOscillator(), gainNode = audioCtx.createGain();
    osc.type = type; osc.frequency.setValueAtTime(f, now);
    gainNode.gain.setValueAtTime(0, now);                                   // 클릭 노이즈 방지 페이드
    gainNode.gain.linearRampToValueAtTime(maxGain, now + 0.4);
    gainNode.gain.setValueAtTime(maxGain, now + duration - 0.5);
    gainNode.gain.linearRampToValueAtTime(0, now + duration);
    osc.connect(gainNode); gainNode.connect(audioCtx.destination);
    osc.start(now); osc.stop(now + duration);
    currentOscillators.push(osc);
  });
  if(currentOscillators.length > 20) currentOscillators.splice(0, 5);
}
function toggleSound(){
  soundEnabled = !soundEnabled;
  const btn = document.getElementById('soundBtn');
  if(soundEnabled){
    btn.innerText = '🔊 소리 켜짐';
    btn.className = 'px-2.5 py-1 text-xs font-bold rounded-lg bg-emerald-500 text-slate-950 active:scale-95 transition shadow-lg';
    initAudio(); startAmbientBGM();
    playChordSynth([523.25,659.25],'sine',0.3,0.05);
  } else {
    btn.innerText = '🔇 소리 꺼짐';
    btn.className = 'px-2.5 py-1 text-xs font-bold rounded-lg glass-soft border border-white/10 text-slate-300 active:scale-95 transition';
    if(bgmInterval) clearInterval(bgmInterval);
    currentOscillators.forEach(o=>{ try{ o.stop(); }catch(e){} });
  }
}

/* ═══════════════ 2. 돌발 기후 변수(Random Modifiers) ═══════════════ */
const MODIFIERS_POOL = [
  { name:'🔥 초대형 아마존 대화재 촉발',     desc:'이번 턴 생태계 타격이 1.6배 가속화됩니다.', target:'eco',  multiply:1.6, type:'bad' },
  { name:'🌊 슈퍼 엘니뇨 현상 동시 발생',    desc:'이번 턴 기온 상승 타격이 1.8배 증폭됩니다.', target:'temp', multiply:1.8, type:'bad' },
  { name:'🧊 북극 메탄 하이드레이트 대분출', desc:'이번 턴 모든 악영향 가중치가 1.5배 폭주합니다.', target:'all', multiply:1.5, type:'bad' },
  { name:'🌱 글로벌 녹색 보조금 전격 타결',  desc:'이번 턴 생태 복원 정책 효율이 1.4배 향상됩니다.', target:'eco', multiply:1.4, type:'good' },
];
function triggerRandomEvent(){
  const warn = document.getElementById('warn');
  if(Math.random() < 0.28 && G.currentStep > 0 && G.currentStep < TOTAL_STAGES - 1){
    const rand = MODIFIERS_POOL[Math.floor(Math.random()*MODIFIERS_POOL.length)];
    G.modifier = rand;
    warn.className = rand.type === 'bad'
      ? 'block rounded-xl mb-3 text-center text-xs font-bold p-2.5 bg-red-950/80 border border-red-700 text-red-300 animate-pulse'
      : 'block rounded-xl mb-3 text-center text-xs font-bold p-2.5 bg-emerald-950/80 border border-emerald-700 text-emerald-300';
    warn.innerHTML = `🚨 [돌발 속보] ${rand.name}<br/><span class="font-normal text-[11px]">${rand.desc}</span>`;
  } else {
    G.modifier = null;
    warn.className = 'hidden';
  }
}

/* ═══════════════ 3. 라이프타임 영구 업적(Achievement) ═══════════════ */
const ACH_META = {
  PARIS: { name:'🕊️ 파리 협정의 전설', desc:'평균 기온 상승을 +1.5°C 이하로 완벽히 방어했습니다.' },
  BOIL:  { name:'🌋 끓어버린 지구',     desc:'기온 폭주(+4.5°C)로 인류가 강제 조기 종료되었습니다.' },
  EMPTY: { name:'🍂 침묵의 봄',         desc:'생태계 건강도 0% 도달로 먹이사슬이 전멸했습니다.' },
  CYBER: { name:'🤖 프랑켄슈타인 테크',  desc:'위험한 지구공학 카드를 남발하여 생존했습니다.' },
  COLD:  { name:'🥶 냉혈한 최고사령관',  desc:'생태 지표를 20% 미만으로 버려둔 채 문명만 보존했습니다.' },
};
function getBadges(){ try{ return JSON.parse(localStorage.getItem('survive2050_achievements')||'[]'); }catch(e){ return []; } }
function unlockBadge(id){
  const earned = getBadges();
  if(earned.includes(id)) return;
  earned.push(id);
  try{ localStorage.setItem('survive2050_achievements', JSON.stringify(earned)); }catch(e){}
  const toast = document.createElement('div');
  toast.className = 'fixed bottom-6 right-6 z-50 glass-main ring-2 ring-amber-400 p-4 rounded-xl shadow-2xl text-white max-w-xs text-left animate-fade-in';
  toast.innerHTML = `
    <div class="text-xs font-black text-amber-400">🏆 영구 업적 해금!</div>
    <div class="font-bold text-sm mt-0.5">${ACH_META[id].name}</div>
    <div class="text-[11px] text-slate-400 mt-0.5">${ACH_META[id].desc}</div>`;
  document.body.appendChild(toast);
  if(soundEnabled) playChordSynth([440,554.37,659.25,880],'sine',0.6,0.06);
  setTimeout(()=>toast.remove(), 4500);
}

/* ═══════════════ 4. 계기판 롤링 + 비동기 안전 차단(Interrupt) ═══════════════ */
function clamp(v,a,b){ return Math.max(a, Math.min(b, v)); }
function rollNum(elId, start, end, duration=600, isFloat=false){
  if(G.renderingHalted) return;
  const el = document.getElementById(elId); if(!el) return;
  const startTime = performance.now();
  (function update(now){
    if(G.renderingHalted) return;
    const p = Math.min((now-startTime)/duration, 1), ease = 1 - Math.pow(1-p, 3);
    const cur = start + (end-start)*ease;
    el.innerText = isFloat ? cur.toFixed(2) : Math.round(cur);
    if(p < 1){ G.rollTimers.push(requestAnimationFrame(update)); }
  })(startTime);
}
function clearAllRollTimers(){ G.rollTimers.forEach(id=>cancelAnimationFrame(id)); G.rollTimers = []; }
function updateBars(){
  const s = G.stats;
  const bT=document.getElementById('bTemp'), bS=document.getElementById('bSea'), bE=document.getElementById('bEco');
  if(bT) bT.style.width = clamp((s.temp/4)*100, 4, 100)+'%';
  if(bS) bS.style.width = clamp((s.sea/120)*100, 2, 100)+'%';
  if(bE) bE.style.width = clamp(s.eco, 2, 100)+'%';
}

/* ── 분위기 연출: 배경 입자 + 생태계 반영 하늘색 ── */
function spawnParticles(mode){
  const wrap = document.getElementById('particles'); if(!wrap) return;
  wrap.innerHTML='';
  for(let k=0;k<16;k++){
    const s = 4 + Math.random()*10, p = document.createElement('span');
    p.className = 'particle';
    p.style.left = (Math.random()*100)+'%';
    p.style.width = s+'px'; p.style.height = s+'px';
    p.style.animationDuration = (6+Math.random()*8)+'s';
    p.style.animationDelay = (-Math.random()*8)+'s';
    p.style.background = mode==='smog' ? 'rgba(140,130,120,.30)'
                       : mode==='eco'  ? 'rgba(160,230,200,.30)'
                                       : 'rgba(120,170,220,.28)';
    wrap.appendChild(p);
  }
}
function setSky(top, mid, bot){
  const r = document.documentElement.style;
  r.setProperty('--sky-top', top); r.setProperty('--sky-mid', mid); r.setProperty('--sky-bot', bot);
}
function updateSky(){
  const e = G ? G.stats.eco : START.eco;
  if(e >= 66){ setSky('#0e7490','#0f766e','#14532d'); spawnParticles('eco'); }
  else if(e >= 33){ setSky('#0b2545','#13315c','#1d3461'); spawnParticles('cool'); }
  else { setSky('#3b2f2f','#4a3b2a','#5b3a29'); spawnParticles('smog'); }
}

/* ═══════════════ 5. 큐 생성 + 선택 처리 ═══════════════ */
function sample(arr, n){
  const pool = arr.slice();
  for(let i=pool.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [pool[i],pool[j]]=[pool[j],pool[i]]; }
  return pool.slice(0, Math.min(n, pool.length));
}
function buildQueue(){
  const q = [];
  QUEUE_PLAN.forEach(({group,pick,tier})=>{
    const pool = SCENARIOS[group] || [];
    sample(pool, pick).forEach(scene=> q.push({ group, tier, scene }));
  });
  G.gameQueue = q; // early→mid→late→final 순(점진적 난이도)
}
function weightFor(step){ return 1 + step * 0.1; }   // 1단계 ×1.0 → 10단계 ×1.9

let locking = false;
function choose(choiceIdx){
  if(G.renderingHalted || locking) return; locking = true;
  const item = G.gameQueue[G.currentStep];
  const scene = item.scene;
  const c = scene.choices[choiceIdx];

  const old = { ...G.stats };
  const stepWeight = weightFor(G.currentStep);
  let modWeight = 1.0;
  if(G.modifier){
    if(G.modifier.target === 'all') modWeight = G.modifier.multiply;
    else if(G.modifier.target === 'temp' && c.fx.temp > 0) modWeight = G.modifier.multiply;
    else if(G.modifier.target === 'eco'){
      // 악재(eco<0)는 피해 증폭, 호재(eco>0)는 복원 증폭
      if((G.modifier.type==='bad' && c.fx.eco < 0) || (G.modifier.type==='good' && c.fx.eco > 0)) modWeight = G.modifier.multiply;
    }
  }

  let nextTemp = G.stats.temp + (c.fx.temp * stepWeight * modWeight);
  if(nextTemp < 0.80) nextTemp = 0.80;   // 최선 플레이라도 영하로 내려가지 않도록 하한 지지선
  G.stats.temp = nextTemp;
  G.stats.sea  = G.stats.sea + (c.fx.sea * stepWeight);
  G.stats.eco  = clamp(G.stats.eco + (c.fx.eco * stepWeight * modWeight), 0, 100);
  G.stats.score += c.fx.score;

  G.history.push({
    step:G.currentStep, tier:item.tier, title:scene.title, choice:c.label, tag:c.tag,
    sdg:c.fx.sdg, baseScore:c.fx.score, feedback:c.feedback, fact:c.fact,
  });

  // 계기판 반영
  rollNum('vTemp', old.temp, G.stats.temp, 500, true);
  rollNum('vSea',  old.sea,  G.stats.sea,  500, false);
  rollNum('vEco',  old.eco,  G.stats.eco,  500, false);
  updateBars();
  if(Math.floor(old.eco/33) !== Math.floor(G.stats.eco/33)) updateSky();   // 생태 구간 바뀔 때만 하늘 갱신

  // 임계점 도달 시 화면 붕괴 연출
  const root = document.getElementById('app-root');
  if(G.stats.eco < 35 || G.stats.temp >= 3.60) root.classList.add('earthquake','glitch-red');
  else root.classList.remove('earthquake','glitch-red');

  // 효과음
  if(soundEnabled){
    if(c.fx.score >= 20) playChordSynth([659.25,783.99,987.77],'sine',0.25,0.05);
    else if(c.fx.score <= 0) playChordSynth([220,174.61],'sawtooth',0.3,0.04);
    else playChordSynth([523.25],'triangle',0.18,0.04);
  }

  // 조기 강제 붕괴 검증
  if(G.stats.eco <= 0 || G.stats.temp >= 4.50){
    if(G.stats.eco <= 0) executeSuddenDeath('EMPTY');
    else executeSuddenDeath('BOIL');
    locking = false;
    return;
  }

  G.currentStep++;
  saveGame();

  if(G.currentStep >= TOTAL_STAGES){
    const result = getMatrixEnding(G.stats.score / MAX_SCORE);
    clearSave();
    renderMatrixCanvas('PEACE');
    renderFinalEndingPage(result.title, result.desc, result.color);
  } else {
    renderFeedbackPage(c);
  }
  locking = false;
}
const MAX_SCORE = TOTAL_STAGES * 20; // 200

/* ═══════════════ 6. 엔딩 매트릭스 + 조기 강제 붕괴 ═══════════════ */
function executeSuddenDeath(reasonType){
  G.renderingHalted = true;
  clearAllRollTimers();
  clearSave();
  unlockBadge(reasonType);
  if(soundEnabled) playChordSynth([146.83,110,82.41],'sawtooth',1.2,0.05);

  let title, desc;
  if(reasonType === 'EMPTY'){
    title = '🍂 배드 엔딩: 텅 빈 세계';
    desc  = '생태계 건강 지표가 결국 0%를 뚫고 파산했습니다. 벌과 미생물이 사라져 수정이 불가능해졌고 모든 식생이 고사했습니다. 인류는 지하 벙커에서 영양 배양액으로 연명하는 혹독한 디스토피아를 마주합니다.';
  } else {
    title = '🌋 배드 엔딩: 끓어버린 지구';
    desc  = '평균 기온 상승이 마지노선인 +4.5°C를 넘어서며 시베리아 영구동토층이 완전히 뒤집혔습니다. 기후 제어 능력을 상실한 지구는 방호복 없이 한 걸음도 걸을 수 없는 거대한 용광로가 되었습니다.';
  }
  renderMatrixCanvas(reasonType);
  renderFinalEndingPage(title, desc, '#ef4444');
}

function getMatrixEnding(ratio){
  const s = G.stats;
  const geoCount = G.history.filter(h=> h.tag && h.tag.includes('지구공학')).length;

  /* ── S 등급(매우 우수) ── */
  if(ratio >= 0.85){
    if(s.temp <= 1.50){ unlockBadge('PARIS'); return {
      title:'🌱 파리의 유토피아', color:'#10b981',
      desc:'기적적으로 온실가스를 포집하고 문명을 보존하여 기온 상승을 1.5°C 미만으로 묶었습니다. 자연과 인류가 진정으로 공존하는 완전한 탄소 중립 낙원이 펼쳐집니다.' }; }
    if(geoCount >= 2){ unlockBadge('CYBER'); return {
      title:'🤖 사이버 가이아 테크노크라시', color:'#3b82f6',
      desc:'탄소는 충분히 줄이지 못했으나 성층권 차단막과 인공 장치를 상시 가동해 연명하는 통제형 인공 에덴입니다. 제어 장치가 단 1분만 멈춰도 종말이 찾아올 것입니다.' }; }
    return {
      title:'✨ 균형 잡힌 탄소중립 도시', color:'#34d399',
      desc:'경제 성장을 훼손하지 않으면서 순환경제 100%에 가깝게 도달한, 균형 잡힌 지속가능 미래입니다.' };
  }

  /* ── A 등급(우수) ── */
  if(ratio >= 0.68) return {
    title:'🌿 녹색 성장의 표준 도시', color:'#22d3ee',
    desc:'대부분의 위기에서 지구를 먼저 생각했습니다. 완전한 회복까지는 아니지만, 도시는 안정적인 궤도 위에서 천천히 더 푸르러지고 있습니다.' };

  /* ── B+ 등급(회복 우세) ── */
  if(ratio >= 0.55) return {
    title:'🌤️ 회복의 궤도 위에서', color:'#2dd4bf',
    desc:'좋은 선택과 미흡한 선택이 섞였지만 전체적으로 회복 쪽으로 기울었습니다. 도시는 여전히 흔들리지만 방향만큼은 옳은 쪽을 향합니다.' };

  /* ── B 등급(생존) — 최종 지표로 분기 ── */
  if(ratio >= 0.40){
    if(s.sea >= 60) return {
      title:'🌊 워터월드: 부유식 아크 문명', color:'#06b6d4',
      desc:'기온은 어느 정도 방어했으나 빙하 해빙 가속으로 해안 대도시가 전면 수몰됐습니다. 인류는 거대한 해상 메가 플로팅 아크를 세워 바다 위 문명을 이어갑니다.' };
    if(s.eco < 25){ unlockBadge('COLD'); return {
      title:'🏙️ 회색 강철 돔의 문명', color:'#64748b',
      desc:'자연 생태계는 사실상 포기하고 모든 녹지를 인공 콘크리트와 기계 숲으로 대체한 채 살아가는, 쓸쓸하고 차가운 인공 도시입니다.' }; }
    return {
      title:'⚖️ 아슬아슬한 평형의 평화', color:'#f59e0b',
      desc:'인류는 멸망하지 않았으나 매년 강타하는 슈퍼 태풍과 초대형 가뭄을 일상으로 견뎌야 하는 끈질긴 생존의 궤도에 들어섰습니다.' };
  }

  /* ── C 등급(위태) ── */
  if(ratio >= 0.25) return {
    title:'🌫️ 흔들리는 잿빛 미래', color:'#a16207',
    desc:'당장의 편리함에 끌린 선택이 더 많았습니다. 도시는 아직 형태를 유지하지만 기온과 생태계 모두 위태로운 경계선 위에 서 있습니다.' };

  /* ── D 등급(붕괴) ── */
  return {
    title:'🌪️ 각자도생의 뉴 다크에이지', color:'#78350f',
    desc:'국제 공조가 파탄 나고 식량 부족으로 인한 기후 난민이 수억 명에 달합니다. 자원 부국들은 장벽을 높이고 자원 민족주의 전쟁에 돌입하는 암흑기입니다.' };
}

/* ═══════════════ 7. 엔딩 Canvas 매트릭스 스트림(모바일 최적화) ═══════════════ */
let matrixRAF = null;
function renderMatrixCanvas(type){
  const canvas = document.getElementById('endingCanvas');
  canvas.classList.remove('hidden');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth; canvas.height = window.innerHeight;

  const isMobile = window.innerWidth < 640;
  const cell = isMobile ? 18 : 14;
  const step = isMobile ? 24 : 14;
  const columns = Math.floor(canvas.width / step);
  const drops = Array(columns).fill(1);

  let chars, fillStyleColor, textColor;
  if(type === 'BOIL'){ chars='🌋🔥4.5°C'; fillStyleColor='rgba(239,68,68,0.06)'; textColor='#f87171'; }
  else if(type === 'EMPTY'){ chars='🍂☠️0%';  fillStyleColor='rgba(16,185,129,0.06)'; textColor='#34d399'; }
  else { chars='🌍🌱✓2050'; fillStyleColor='rgba(13,148,136,0.05)'; textColor='#5eead4'; }

  const interval = isMobile ? 1000/38 : 1000/60;
  let lastTime = 0;
  if(matrixRAF) cancelAnimationFrame(matrixRAF);
  function draw(ts){
    if(!lastTime) lastTime = ts;
    if(ts - lastTime > interval){
      ctx.fillStyle = fillStyleColor; ctx.fillRect(0,0,canvas.width,canvas.height);
      ctx.fillStyle = textColor; ctx.font = (isMobile?'11px':'14px')+' monospace';
      for(let i=0;i<drops.length;i++){
        const text = chars[Math.floor(Math.random()*chars.length)];
        ctx.fillText(text, i*step, drops[i]*cell);
        if(drops[i]*cell > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
      lastTime = ts;
    }
    matrixRAF = requestAnimationFrame(draw);
  }
  matrixRAF = requestAnimationFrame(draw);
}

/* ═══════════════ 8. 화면 렌더 ═══════════════ */
function renderCurrentScenario(){
  if(G.renderingHalted) return;
  const stage = document.getElementById('stage');
  const item = G.gameQueue[G.currentStep];
  const scene = item.scene;

  const choicesHTML = scene.choices.map((c, idx)=>{
    const meta = SDG[c.fx.sdg] || { name:'SDGs', color:'#64748b' };
    return `
      <button onclick="choose(${idx})" class="w-full text-left p-3.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-emerald-400/40 text-sm font-medium transition active:scale-[0.99] text-slate-200">
        <div class="flex items-center justify-between gap-2 mb-0.5">
          <div class="font-bold text-emerald-400 text-xs">[선택 ${String.fromCharCode(65+idx)}] ${c.tag}</div>
          <span class="text-[10px] rounded-full px-1.5 py-0.5 font-bold shrink-0" style="background:${meta.color}22;color:${meta.color};border:1px solid ${meta.color}55">SDG ${c.fx.sdg}</span>
        </div>
        ${c.label}
      </button>`;
  }).join('');

  // 진행 세그먼트
  let seg = '';
  for(let k=0;k<TOTAL_STAGES;k++) seg += `<span class="h-1.5 rounded-full ${k<G.currentStep?'bg-emerald-400':(k===G.currentStep?'bg-white/60':'bg-white/15')}" style="width:${100/TOTAL_STAGES-1.5}%"></span>`;

  stage.innerHTML = `
    <div class="glass-main p-5 rounded-2xl shadow-xl animate-fade-in">
      <div class="flex items-center gap-1 mb-3">${seg}</div>
      <div class="flex justify-between text-xs text-slate-400 font-bold mb-2">
        <span>📋 통제 단계: ${G.currentStep+1} / ${TOTAL_STAGES}</span>
        <span class="text-red-400">위기 등급: TIER ${item.tier}</span>
      </div>
      <h2 class="text-lg font-black text-white mb-2">${scene.title}</h2>
      <p class="text-xs text-slate-300 leading-relaxed bg-black/20 p-3 rounded-xl border border-white/5 mb-4">${scene.text}</p>
      <div class="space-y-2">${choicesHTML}</div>
    </div>`;
}

function renderFeedbackPage(choice){
  const stage = document.getElementById('stage');
  const meta = SDG[choice.fx.sdg] || { name:'지속가능개발목표', color:'#64748b' };
  stage.innerHTML = `
    <div class="glass-main p-6 rounded-2xl text-center shadow-xl animate-fade-in">
      <div class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-1">정책 시행 결과</div>
      <h3 class="text-xl font-black text-white mb-4">"${choice.tag}"</h3>
      <p class="text-sm text-slate-300 leading-relaxed mb-5">${choice.feedback}</p>
      <a href="${meta.url||'#'}" target="_blank" rel="noopener" class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold text-white mb-4" style="background:${meta.color}">
        🌐 SDG ${choice.fx.sdg}: ${meta.name} ↗
      </a>
      <div class="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 text-left mb-6 text-slate-300 text-[11px] leading-relaxed">
        <strong class="text-amber-400 block mb-0.5">💡 과학적 팩트 체크</strong>
        ${choice.fact}
      </div>
      <button id="nextBtn" class="w-full rounded-full bg-white text-slate-950 font-black py-3 active:scale-95 transition shadow-lg text-sm">
        다음 위기 보고서 접수 ➡️
      </button>
    </div>`;
  document.getElementById('nextBtn').onclick = ()=>{
    if(soundEnabled) playChordSynth([587.33,783.99],'sine',0.15,0.04);
    triggerRandomEvent();
    renderCurrentScenario();
  };
}

function renderFinalEndingPage(title, desc, color){
  const stage = document.getElementById('stage');
  document.getElementById('warn').className = 'hidden';
  document.getElementById('app-root').classList.remove('earthquake','glitch-red');
  setSky(color, color+'88', '#0b1220'); spawnParticles(G.stats.eco<33?'smog':'eco');  // 엔딩 색에 맞춘 하늘

  // SDGs 성적표
  let report = '';
  G.history.forEach((l,k)=>{
    const m = SDG[l.sdg] || { name:'SDGs', color:'#64748b', url:'#' };
    const good = l.baseScore>=20, mid = l.baseScore>=10;
    const mark = good?'🟢 탁월':(mid?'🟡 무난':'🔴 아쉬움');
    report += `
      <div class="flex items-start gap-2.5 p-2.5 rounded-lg bg-white/5 border border-white/5 text-left">
        <div class="shrink-0 grid h-9 w-9 place-items-center rounded-lg font-black text-white text-[10px] text-center leading-tight" style="background:${m.color}">SDG<br>${l.sdg}</div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-2"><span class="text-[10px] text-slate-400">${l.step+1}단계</span><span class="text-[10px] font-bold">${mark}</span></div>
          <div class="text-xs font-bold leading-snug truncate">${l.choice}</div>
          <a href="${m.url}" target="_blank" rel="noopener" class="text-[10px] underline decoration-dotted hover:text-emerald-300" style="color:${m.color}">${m.name} ↗</a>
        </div>
      </div>`;
  });

  const scorePct = Math.round(G.stats.score / MAX_SCORE * 100);
  stage.innerHTML = `
    <div class="glass-main p-6 rounded-2xl text-center shadow-2xl border relative z-50 animate-fade-in" style="border-color:${color}50">
      <div class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">2050 기후 시뮬레이션 최종 보고서</div>
      <h2 class="text-xl font-black mb-4" style="color:${color}">${title}</h2>
      <p class="text-xs text-slate-300 leading-relaxed bg-black/40 p-3.5 rounded-xl border border-white/5 text-left mb-5">${desc}</p>

      <div class="bg-slate-900/80 p-3.5 rounded-xl border border-white/5 text-xs text-left space-y-1.5 mb-5">
        <div class="font-bold text-center text-slate-400 border-b border-white/10 pb-1.5 mb-1.5">📊 최종 지구 환경 지표</div>
        <div class="flex justify-between"><span>🌡️ 평균 기온 변동</span><span class="font-bold text-red-400">+${G.stats.temp.toFixed(2)}°C</span></div>
        <div class="flex justify-between"><span>🌊 글로벌 해수면</span><span class="font-bold text-cyan-400">+${G.stats.sea.toFixed(0)}cm</span></div>
        <div class="flex justify-between"><span>🌱 대자연 생태 지표</span><span class="font-bold text-emerald-400">${G.stats.eco.toFixed(0)}%</span></div>
        <div class="flex justify-between border-t border-white/10 pt-1.5 mt-1 font-bold"><span>지속가능성 점수</span><span class="text-amber-400">${scorePct}% (${G.stats.score}점)</span></div>
      </div>

      <div class="mb-5">
        <div class="text-xs font-bold text-slate-300 text-left mb-2">🎓 나의 SDGs 성적표</div>
        <div class="space-y-1.5 max-h-60 overflow-y-auto pr-1">${report}</div>
      </div>

      <button onclick="restartGame()" class="w-full rounded-full py-3 text-slate-950 font-black text-sm active:scale-95 transition shadow-lg" style="background:${color}">
        🔄 타임 패러독스: 지구 다시 구하기
      </button>
    </div>`;
}

/* ═══════════════ 9. 인트로 + 업적 진열장 ═══════════════ */
function screenIntro(){
  const stage = document.getElementById('stage');
  document.getElementById('app-root').classList.remove('earthquake','glitch-red');
  const canvas = document.getElementById('endingCanvas'); if(canvas) canvas.classList.add('hidden');
  if(matrixRAF) cancelAnimationFrame(matrixRAF);

  const earned = getBadges();
  const badgeHTML = Object.keys(ACH_META).map(key=>{
    const ok = earned.includes(key);
    const ic = ACH_META[key].name.split(' ')[0];
    const nm = ACH_META[key].name.split(' ').slice(1).join(' ');
    return `<div class="p-2 rounded-lg text-center ${ok?'bg-amber-500/10 border border-amber-500/30 text-amber-300':'bg-white/5 opacity-30 text-slate-500'} text-[10px]">
        <div class="text-base mb-0.5">${ic}</div><div class="font-bold truncate">${nm}</div></div>`;
  }).join('');

  G = null; updateSky();   // 인트로는 시원한 기본 하늘 + 입자
  // 상단 지표를 시작값으로 리셋(직전 게임 잔상 제거)
  document.getElementById('vTemp').innerText = START.temp.toFixed(2);
  document.getElementById('vSea').innerText  = START.sea;
  document.getElementById('vEco').innerText  = START.eco;
  document.getElementById('bTemp').style.width = clamp((START.temp/4)*100,4,100)+'%';
  document.getElementById('bSea').style.width  = clamp((START.sea/120)*100,2,100)+'%';
  document.getElementById('bEco').style.width  = clamp(START.eco,2,100)+'%';
  const hasSave = !!readSave();
  stage.innerHTML = `
    <div class="glass-main p-6 rounded-2xl text-center shadow-xl animate-fade-in">
      <div class="text-6xl floaty mb-2 drop-shadow-[0_10px_30px_rgba(16,185,129,.35)]">🌏</div>
      <h2 class="font-display text-3xl text-white mb-1">살려야 한다, 지구</h2>
      <p class="text-xs text-slate-400 mb-6">UN SDGs 기반 기후 통제 시뮬레이션 · 총 ${TOTAL_STAGES}단계</p>
      <button id="startBtn" class="glow-pulse w-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 text-slate-950 font-black py-3.5 text-sm active:scale-95 transition shadow-xl mb-2.5">
        ▶ 통제실 입장 (새 게임)
      </button>
      ${hasSave?`<button id="resumeBtn" class="w-full rounded-full glass-soft border border-white/10 text-slate-200 font-bold py-3 text-sm active:scale-95 transition mb-6">💾 이어하기</button>`:'<div class="mb-6"></div>'}
      <div class="border-t border-white/5 pt-4">
        <div class="text-xs font-bold text-slate-400 text-left mb-2">🏆 영구 업적 진열장 (${earned.length}/${Object.keys(ACH_META).length})</div>
        <div class="grid grid-cols-5 gap-1.5">${badgeHTML}</div>
      </div>
    </div>`;

  // 사용자 클릭 시점에 오디오 가동(자동재생 정책 대응)
  document.getElementById('startBtn').onclick = ()=>{ if(!soundEnabled) toggleSound(); startGame(); };
  const rb = document.getElementById('resumeBtn');
  if(rb) rb.onclick = ()=>{ if(!soundEnabled) toggleSound(); loadGame(); };
}

function startGame(){
  G = { stats: freshStats(), history: [], currentStep: 0, gameQueue: [], modifier: null, renderingHalted: false, rollTimers: [] };
  buildQueue();
  document.getElementById('warn').className = 'hidden';
  syncHUD(); saveGame();
  renderCurrentScenario();
}
function restartGame(){
  G.renderingHalted = false;
  if(matrixRAF) cancelAnimationFrame(matrixRAF);
  document.getElementById('endingCanvas').classList.add('hidden');
  clearSave();
  screenIntro();
}

/* ═══════════════ 10. 저장 / 복구 ═══════════════ */
const STORAGE_KEY = 'survive2050_save';
function saveGame(){
  try{
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      currentStep:G.currentStep, gameQueue:G.gameQueue, stats:G.stats, history:G.history, savedAt:Date.now(),
    }));
  }catch(e){}
}
function readSave(){
  try{
    const raw = localStorage.getItem(STORAGE_KEY); if(!raw) return null;
    const d = JSON.parse(raw);
    const ok = d && typeof d.currentStep==='number' && Array.isArray(d.gameQueue) &&
      d.gameQueue.length===TOTAL_STAGES && d.stats && typeof d.stats.temp==='number' &&
      Array.isArray(d.history) && d.currentStep>=1 && d.currentStep<TOTAL_STAGES;
    if(!ok) return null;
    if(d.gameQueue.some(q=> !q || !q.scene || !Array.isArray(q.scene.choices))) return null;
    return d;
  }catch(e){ return null; }
}
function clearSave(){ try{ localStorage.removeItem(STORAGE_KEY); }catch(e){} }
function loadGame(){
  const saved = readSave(); if(!saved){ startGame(); return; }
  G = { currentStep: saved.currentStep, gameQueue: saved.gameQueue, stats: saved.stats,
        history: saved.history, modifier: null, renderingHalted: false, rollTimers: [] };
  syncHUD();
  renderCurrentScenario();
}
function syncHUD(){
  document.getElementById('vTemp').innerText = (+G.stats.temp).toFixed(2);
  document.getElementById('vSea').innerText  = Math.round(G.stats.sea);
  document.getElementById('vEco').innerText  = Math.round(G.stats.eco);
  updateBars();
  updateSky();
}

/* ═══════════════ 부팅 ═══════════════ */
function boot(){
  document.getElementById('soundBtn').onclick = toggleSound;
  syncHUD();
  screenIntro();
}
window.onload = boot;
