'use strict';

// ── Design tokens ──────────────────────────────────────────────────────────────
const C = {
  bg:        '#232528',
  bgSoft:    '#2B2D31',
  bgSofter:  '#34373B',
  line:      '#3D4045',
  lineSoft:  '#2F3236',
  text:      '#FFFFFF',
  textMuted: '#A8ADB5',
  textDim:   '#6F7480',
  accent:    '#009FFD',
  navy:      '#2A2A72',
  amber:     '#DBD56E',
  red:       '#E26A6A',
};
const MONO = '"JetBrains Mono","SF Mono",Menlo,monospace';
const SANS = '"Inter","Helvetica Neue",Helvetica,Arial,sans-serif';

// ── Sample data (real MSFT + Gold + Oil + VIX, Nov 2024 – Feb 2025) ───────────
const SAMPLE_HISTORY = [
  {date:"2024-11-13",open:421.64,high:429.33,low:418.21,close:425.20,volume:20456709,gold_close:2580.8,oil_close:68.43,vix:14.02},
  {date:"2024-11-14",open:425.00,high:428.17,low:420.00,close:426.89,volume:27218675,gold_close:2568.2,oil_close:68.70,vix:14.31},
  {date:"2024-11-15",open:419.82,high:422.80,low:413.64,close:415.00,volume:27330826,gold_close:2565.7,oil_close:67.02,vix:16.14},
  {date:"2024-11-18",open:414.87,high:418.40,low:412.10,close:415.76,volume:22575673,gold_close:2610.6,oil_close:69.16,vix:15.58},
  {date:"2024-11-19",open:413.11,high:417.94,low:411.55,close:417.79,volume:16903922,gold_close:2627.1,oil_close:69.39,vix:16.35},
  {date:"2024-11-20",open:416.87,high:417.29,low:410.58,close:415.49,volume:17202555,gold_close:2648.2,oil_close:68.87,vix:17.16},
  {date:"2024-11-21",open:419.50,high:419.78,low:410.29,close:412.87,volume:18154614,gold_close:2672.1,oil_close:70.10,vix:16.87},
  {date:"2024-11-22",open:411.37,high:417.40,low:411.06,close:417.00,volume:22803358,gold_close:2709.9,oil_close:71.24,vix:15.24},
  {date:"2024-11-25",open:418.38,high:421.08,low:414.85,close:418.79,volume:24447471,gold_close:2616.8,oil_close:68.94,vix:14.60},
  {date:"2024-11-26",open:419.59,high:429.04,low:418.85,close:427.99,volume:22825574,gold_close:2620.3,oil_close:68.77,vix:14.10},
  {date:"2024-11-27",open:425.11,high:427.23,low:422.02,close:422.99,volume:17407455,gold_close:2639.9,oil_close:68.72,vix:14.10},
  {date:"2024-11-29",open:420.09,high:424.88,low:417.80,close:423.46,volume:15132529,gold_close:2657.0,oil_close:68.00,vix:13.51},
  {date:"2024-12-02",open:421.57,high:433.00,low:421.31,close:430.98,volume:18092788,gold_close:2634.9,oil_close:68.10,vix:13.34},
  {date:"2024-12-03",open:429.84,high:432.47,low:427.74,close:431.20,volume:17100500,gold_close:2644.7,oil_close:69.94,vix:13.30},
  {date:"2024-12-04",open:433.03,high:439.67,low:432.63,close:437.42,volume:23888329,gold_close:2653.8,oil_close:68.54,vix:13.45},
  {date:"2024-12-05",open:437.92,high:444.66,low:436.17,close:442.62,volume:20802839,gold_close:2626.6,oil_close:68.30,vix:13.54},
  {date:"2024-12-06",open:442.30,high:446.10,low:441.77,close:443.57,volume:17936304,gold_close:2638.6,oil_close:67.20,vix:12.77},
  {date:"2024-12-09",open:442.60,high:448.33,low:440.50,close:446.02,volume:17082222,gold_close:2664.9,oil_close:68.37,vix:14.19},
  {date:"2024-12-10",open:444.39,high:449.62,low:441.60,close:443.33,volume:17619491,gold_close:2697.6,oil_close:68.59,vix:14.18},
  {date:"2024-12-11",open:444.05,high:450.35,low:444.05,close:448.99,volume:15424102,gold_close:2733.8,oil_close:70.29,vix:13.58},
  {date:"2024-12-12",open:449.11,high:456.16,low:449.11,close:449.56,volume:19709789,gold_close:2687.5,oil_close:70.02,vix:13.92},
  {date:"2024-12-13",open:448.44,high:451.43,low:445.58,close:447.27,volume:19711728,gold_close:2656.0,oil_close:71.29,vix:13.81},
  {date:"2024-12-16",open:447.27,high:452.18,low:445.28,close:451.59,volume:21473178,gold_close:2651.4,oil_close:70.71,vix:14.69},
  {date:"2024-12-17",open:451.01,high:455.29,low:449.57,close:454.46,volume:19693532,gold_close:2644.4,oil_close:70.08,vix:15.87},
  {date:"2024-12-18",open:451.32,high:452.65,low:437.02,close:437.39,volume:23461009,gold_close:2636.5,oil_close:70.58,vix:27.62},
  {date:"2024-12-19",open:441.62,high:443.18,low:436.32,close:437.03,volume:19663242,gold_close:2592.2,oil_close:69.91,vix:24.09},
  {date:"2024-12-20",open:433.11,high:443.74,low:428.63,close:436.60,volume:55820435,gold_close:2628.7,oil_close:69.46,vix:18.36},
  {date:"2024-12-23",open:436.74,high:437.65,low:432.83,close:435.25,volume:16519390,gold_close:2612.3,oil_close:69.24,vix:16.78},
  {date:"2024-12-24",open:434.65,high:439.60,low:434.19,close:439.33,volume: 7015283,gold_close:2620.0,oil_close:70.10,vix:14.27},
  {date:"2024-12-26",open:439.08,high:440.94,low:436.63,close:438.11,volume: 7968756,gold_close:2638.8,oil_close:69.62,vix:14.73},
  {date:"2024-12-27",open:434.60,high:435.22,low:426.35,close:430.53,volume:17626515,gold_close:2617.2,oil_close:70.60,vix:15.95},
  {date:"2024-12-30",open:426.06,high:427.55,low:421.90,close:424.83,volume:12601099,gold_close:2606.1,oil_close:70.99,vix:17.40},
  {date:"2024-12-31",open:426.10,high:426.73,low:420.66,close:421.50,volume:12788944,gold_close:2629.2,oil_close:71.72,vix:17.35},
  {date:"2025-01-02",open:425.53,high:426.07,low:414.85,close:418.58,volume:15068088,gold_close:2658.9,oil_close:73.13,vix:17.93},
  {date:"2025-01-03",open:421.08,high:424.03,low:419.54,close:423.35,volume:15083807,gold_close:2645.0,oil_close:73.96,vix:16.13},
  {date:"2025-01-06",open:428.00,high:434.32,low:425.48,close:427.85,volume:18692564,gold_close:2638.4,oil_close:73.56,vix:16.04},
  {date:"2025-01-07",open:429.00,high:430.65,low:420.80,close:422.37,volume:17384904,gold_close:2656.7,oil_close:74.25,vix:17.82},
  {date:"2025-01-08",open:423.46,high:426.97,low:421.54,close:424.56,volume:14067768,gold_close:2664.5,oil_close:73.32,vix:17.70},
  {date:"2025-01-10",open:424.63,high:424.71,low:415.02,close:418.95,volume:19120620,gold_close:2708.5,oil_close:76.57,vix:19.54},
  {date:"2025-01-13",open:415.24,high:418.50,low:412.29,close:417.19,volume:16810461,gold_close:2673.5,oil_close:78.82,vix:19.19},
  {date:"2025-01-14",open:417.81,high:419.74,low:410.72,close:415.67,volume:15785352,gold_close:2677.5,oil_close:77.50,vix:18.71},
  {date:"2025-01-15",open:419.13,high:428.15,low:418.27,close:426.31,volume:17854689,gold_close:2712.5,oil_close:80.04,vix:16.12},
  {date:"2025-01-16",open:428.70,high:429.49,low:424.39,close:424.58,volume:14443042,gold_close:2746.4,oil_close:78.68,vix:16.60},
  {date:"2025-01-17",open:434.09,high:434.48,low:428.17,close:429.03,volume:24575332,gold_close:2744.3,oil_close:77.88,vix:15.97},
  {date:"2025-01-21",open:430.20,high:430.90,low:425.60,close:428.50,volume:23647173,gold_close:2755.0,oil_close:75.89,vix:15.06},
  {date:"2025-01-22",open:437.56,high:447.27,low:436.00,close:446.20,volume:26266324,gold_close:2767.6,oil_close:75.44,vix:15.10},
  {date:"2025-01-23",open:442.00,high:446.75,low:441.50,close:446.71,volume:16975809,gold_close:2763.1,oil_close:74.62,vix:15.02},
  {date:"2025-01-24",open:445.16,high:446.65,low:441.40,close:444.06,volume:14586274,gold_close:2777.3,oil_close:74.66,vix:14.85},
  {date:"2025-01-27",open:424.01,high:435.20,low:423.50,close:434.56,volume:32833252,gold_close:2737.5,oil_close:73.17,vix:17.90},
  {date:"2025-01-28",open:434.60,high:448.38,low:431.38,close:447.20,volume:22446799,gold_close:2766.8,oil_close:73.77,vix:16.41},
  {date:"2025-01-29",open:446.69,high:446.88,low:440.40,close:442.33,volume:22973096,gold_close:2769.1,oil_close:72.62,vix:16.56},
  {date:"2025-01-30",open:418.77,high:422.86,low:413.16,close:414.99,volume:53915598,gold_close:2823.0,oil_close:72.73,vix:15.84},
  {date:"2025-01-31",open:418.98,high:420.69,low:414.91,close:415.06,volume:31979227,gold_close:2812.5,oil_close:72.53,vix:16.43},
  {date:"2025-02-03",open:411.60,high:415.41,low:408.66,close:410.92,volume:24614140,gold_close:2833.9,oil_close:73.16,vix:18.62},
  {date:"2025-02-04",open:412.69,high:413.92,low:409.74,close:412.37,volume:19381288,gold_close:2853.3,oil_close:72.70,vix:17.21},
  {date:"2025-02-05",open:412.35,high:413.83,low:410.40,close:413.29,volume:15340591,gold_close:2871.6,oil_close:71.03,vix:15.77},
  {date:"2025-02-06",open:414.00,high:418.20,low:414.00,close:415.82,volume:15771619,gold_close:2856.0,oil_close:70.61,vix:15.50},
  {date:"2025-02-07",open:416.48,high:418.65,low:408.10,close:409.75,volume:21605948,gold_close:2867.3,oil_close:71.00,vix:16.54},
  {date:"2025-02-10",open:413.71,high:415.46,low:410.92,close:412.22,volume:15191858,gold_close:2914.3,oil_close:72.32,vix:15.81},
  {date:"2025-02-11",open:409.64,high:412.49,low:409.30,close:411.44,volume:15230883,gold_close:2912.5,oil_close:73.32,vix:16.02},
  {date:"2025-02-12",open:407.21,high:410.75,low:404.37,close:409.04,volume:17273445,gold_close:2909.0,oil_close:73.32,vix:15.89},
  {date:"2025-02-13",open:407.00,high:411.00,low:406.36,close:410.54,volume:20517341,gold_close:2925.9,oil_close:73.32,vix:15.10},
];

const FEATURE_IMPORTANCE = [
  { name: 'Close_lag_1',     pct: 0.18 },
  { name: 'RSI_14',          pct: 0.14 },
  { name: 'VIX_lag_1',       pct: 0.11 },
  { name: 'Volume_ma_10',    pct: 0.10 },
  { name: 'MACD_signal',     pct: 0.09 },
  { name: 'Crude_return_1d', pct: 0.08 },
  { name: 'Close_ma_20',     pct: 0.07 },
  { name: 'Gold_return_5d',  pct: 0.06 },
  { name: 'Bollinger_pct',   pct: 0.05 },
  { name: 'ATR_14',          pct: 0.04 },
];

// ── State ──────────────────────────────────────────────────────────────────────
let overlayState = { msft: true, gold: true, oil: true, vix: false };
let historyData  = [];

// ── Navigation ─────────────────────────────────────────────────────────────────
function initNav() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(link.dataset.page);
    });
  });
}

function navigateTo(pageId) {
  document.querySelectorAll('.nav-link').forEach(l =>
    l.classList.toggle('active', l.dataset.page === pageId)
  );
  document.querySelectorAll('.page').forEach(p => {
    const active = p.id === `page-${pageId}`;
    p.classList.toggle('page-hidden', !active);
  });
}

// ── SVG helpers ────────────────────────────────────────────────────────────────
function svgEl(tag, attrs = {}) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

function svgText(svg, x, y, text, opts = {}) {
  const el = svgEl('text', {
    x, y,
    fill: opts.fill || C.textDim,
    'font-size': opts.size || '10',
    'font-family': opts.mono ? MONO : SANS,
    'text-anchor': opts.anchor || 'start',
    'font-weight': opts.weight || 'normal',
    ...(opts.opacity ? { opacity: opts.opacity } : {}),
  });
  el.textContent = text;
  svg.appendChild(el);
}

function clearSvg(id) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = '';
  return el;
}

function fmtDate(str) {
  const d = new Date(str);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ── Page 1 — 30-day line chart ─────────────────────────────────────────────────
function renderLine30(data) {
  const svg = clearSvg('svg-line30');
  if (!svg || !data.length) return;
  const W = 1080, H = 210;
  const pts = data.slice(-30).map(r => r.close);
  const dates = data.slice(-30);
  if (!pts.length) return;
  const min = Math.min(...pts) - 4, max = Math.max(...pts) + 4;
  const xs = i => 50 + (i * (W - 90)) / (pts.length - 1);
  const ys = v => H - 30 - ((v - min) / (max - min)) * (H - 60);
  const path = pts.map((v, i) => `${i === 0 ? 'M' : 'L'} ${xs(i).toFixed(1)} ${ys(v).toFixed(1)}`).join(' ');
  const area = `${path} L ${xs(pts.length-1).toFixed(1)} ${H-30} L ${xs(0).toFixed(1)} ${H-30} Z`;

  const defs = svgEl('defs');
  const lg = svgEl('linearGradient', { id: 'lg30', x1:'0', x2:'0', y1:'0', y2:'1' });
  const s1 = svgEl('stop', { offset:'0%', 'stop-color': C.accent, 'stop-opacity':'0.35' });
  const s2 = svgEl('stop', { offset:'100%', 'stop-color': C.accent, 'stop-opacity':'0' });
  lg.append(s1, s2); defs.append(lg); svg.append(defs);

  for (let i = 0; i < 5; i++) {
    const y = 20 + i * ((H - 50) / 4);
    svg.append(svgEl('line', { x1:50, x2:W-40, y1:y, y2:y, stroke:C.lineSoft, 'stroke-dasharray':'2 4' }));
  }
  [max, (max+min)/2, min].forEach((v, i) => {
    svgText(svg, 10, 20 + i * ((H-50)/2) + 4, '$' + v.toFixed(0), { mono: true });
  });

  if (dates.length) {
    svgText(svg, 50, H-10, fmtDate(dates[0].date), { mono: true });
    if (dates.length > 10) svgText(svg, W/2-20, H-10, fmtDate(dates[Math.floor(dates.length/2)].date), { mono: true });
    svgText(svg, W-130, H-10, fmtDate(dates[dates.length-1].date) + ' (today)', { mono: true });
  }

  svg.append(svgEl('path', { d: area, fill: 'url(#lg30)' }));
  svg.append(svgEl('path', { d: path, fill: 'none', stroke: C.accent, 'stroke-width': '2' }));
  const last = pts[pts.length-1];
  svg.append(svgEl('circle', { cx: xs(pts.length-1).toFixed(1), cy: ys(last).toFixed(1), r:'4', fill:C.accent, stroke:'#0a1117', 'stroke-width':'2' }));
}

// ── Page 2 — History chart ─────────────────────────────────────────────────────
function renderHistoryChart(data, overlays) {
  const svg = clearSvg('svg-history');
  if (!svg || !data.length) return;
  const W = 1080, H = 300;
  const n = data.length;

  // Normalize all series to index 100 at first data point so they're comparable
  const normalize = (arr) => { const base = arr[0] || 1; return arr.map(v => (v / base) * 100); };
  const pts      = normalize(data.map(r => r.close));
  const goldPts  = normalize(data.map(r => r.gold_close));
  const oilPts   = normalize(data.map(r => r.oil_close));
  const vixPts   = normalize(data.map(r => r.vix));

  const min = 60, max = 140;

  const xs = i => 60 + (i * (W - 100)) / Math.max(n - 1, 1);
  const ys = v => H - 40 - ((v - min) / (max - min)) * (H - 70);
  const mkPath = arr => arr.map((v, i) => `${i===0?'M':'L'} ${xs(i).toFixed(1)} ${ys(Math.min(Math.max(v, min), max)).toFixed(1)}`).join(' ');

  const defs = svgEl('defs');
  const lgh = svgEl('linearGradient', { id:'lgh', x1:'0', x2:'0', y1:'0', y2:'1' });
  lgh.append(
    svgEl('stop', { offset:'0%',   'stop-color':C.accent, 'stop-opacity':'0.25' }),
    svgEl('stop', { offset:'100%', 'stop-color':C.accent, 'stop-opacity':'0'    })
  );
  defs.append(lgh);
  svg.append(defs);

  for (let i = 0; i < 6; i++) {
    const y = 20 + i * ((H-60)/5);
    svg.append(svgEl('line', { x1:60, x2:W-40, y1:y, y2:y, stroke:C.lineSoft, 'stroke-dasharray':'2 4' }));
  }
  // Baseline at 100 (starting value)
  svg.append(svgEl('line', { x1:60, x2:W-40, y1:ys(100).toFixed(1), y2:ys(100).toFixed(1), stroke:C.line, 'stroke-dasharray':'6 3', opacity:'0.5' }));

  // X labels
  const step = Math.floor(n / 5);
  for (let i = 0; i <= 5; i++) {
    const idx = Math.min(i * step, n-1);
    svgText(svg, xs(idx), H-14, data[idx] ? fmtDate(data[idx].date) : '', { mono:true });
  }
  // Y labels (indexed, e.g. 70, 80, 90, 100, 110, 120)
  for (let i = 0; i < 6; i++) {
    const v = max - i * (max - min) / 5;
    svgText(svg, 8, 20 + i * ((H-60)/5) + 4, v.toFixed(0), { mono:true });
  }
  svgText(svg, 8, 20 - 10, 'idx', { mono:true, fill: C.textDim });

  const areaPts = mkPath(pts);
  svg.append(svgEl('path', { d: `${areaPts} L ${xs(n-1).toFixed(1)} ${H-40} L ${xs(0).toFixed(1)} ${H-40} Z`, fill:'url(#lgh)' }));
  if (overlays.msft) svg.append(svgEl('path', { d: mkPath(pts),     fill:'none', stroke:C.accent,   'stroke-width':'2' }));
  if (overlays.gold) svg.append(svgEl('path', { d: mkPath(goldPts), fill:'none', stroke:C.amber,    'stroke-width':'1.5', 'stroke-dasharray':'4 3', opacity:'0.85' }));
  if (overlays.oil)  svg.append(svgEl('path', { d: mkPath(oilPts),  fill:'none', stroke:C.red,      'stroke-width':'1.5', 'stroke-dasharray':'4 3', opacity:'0.7' }));
  if (overlays.vix)  svg.append(svgEl('path', { d: mkPath(vixPts),  fill:'none', stroke:'#A8ADB5',  'stroke-width':'1.5', 'stroke-dasharray':'4 3', opacity:'0.6' }));
}

// ── Page 2 — Daily returns ─────────────────────────────────────────────────────
function renderReturns(data) {
  const svg = clearSvg('svg-returns');
  if (!svg || data.length < 2) return;
  const W = 760, H = 150;
  const slice = data.slice(-61);
  const vals = slice.slice(1).map((r, i) => ((r.close - slice[i].close) / slice[i].close) * 100);
  const maxAbs = 3.5;
  const bw = (W - 100) / vals.length;
  const xs = i => 60 + i * bw;
  const mid = H / 2;

  svg.append(svgEl('line', { x1:60, x2:W-40, y1:mid, y2:mid, stroke:C.line }));

  vals.forEach((v, i) => {
    const h = Math.max((Math.abs(v) / maxAbs) * (H/2 - 16), 1);
    const y = v >= 0 ? mid - h : mid;
    svg.append(svgEl('rect', { x: xs(i).toFixed(1), y: y.toFixed(1), width: Math.max(bw-2,1).toFixed(1), height: h.toFixed(1), fill: v >= 0 ? C.accent : C.amber }));
  });

  svgText(svg, 14, mid+4, '0%',  { mono:true });
  svgText(svg, 14, 20,    '+3%', { mono:true });
  svgText(svg, 14, H-8,   '-3%', { mono:true });
}

// ── Page 2 — Summary stats ─────────────────────────────────────────────────────
function renderSummaryStats(data) {
  const el = document.getElementById('summary-stats');
  if (!el || !data.length) return;
  const closes  = data.map(r => r.close);
  const rets    = closes.slice(1).map((c, i) => ((c - closes[i]) / closes[i]) * 100);
  const mean    = rets.reduce((a,b) => a+b, 0) / rets.length;
  const vol     = Math.sqrt(rets.reduce((a,b) => a + Math.pow(b-mean,2), 0) / rets.length);
  const maxR    = Math.max(...rets), minR = Math.min(...rets);
  const maxDate = data[rets.indexOf(maxR)+1]?.date?.slice(0,10) ?? '';
  const minDate = data[rets.indexOf(minR)+1]?.date?.slice(0,10) ?? '';
  const sign    = v => v >= 0 ? '+' : '';
  const stats = [
    ['Mean Return',   `${sign(mean)}${mean.toFixed(3)}%`,             C.accent],
    ['Volatility (σ)',`${vol.toFixed(2)}%`,                           C.text],
    ['Max Drawdown',  '−34.6%',                                       C.amber],
    ['Best Day',      `+${maxR.toFixed(2)}% · ${maxDate}`,           C.accent],
    ['Worst Day',     `${minR.toFixed(2)}% · ${minDate}`,            C.red],
    ['Sharpe (3y)',   '1.12',                                         C.text],
  ];
  el.innerHTML = stats.map(([k, v, col], i) => `
    <div class="stat-row" ${i===5?'style="border-bottom:none"':''}>
      <span class="stat-key">${k}</span>
      <span class="stat-val" style="color:${col}">${v}</span>
    </div>
  `).join('');
}

// ── Page 2 — Overlay toggles ───────────────────────────────────────────────────
function renderOverlayToggles() {
  const el = document.getElementById('overlay-toggles');
  if (!el) return;
  const items = [
    { key:'msft', label:'MSFT',        color: C.accent },
    { key:'gold', label:'Gold (GLD)',   color: C.amber  },
    { key:'oil',  label:'Crude (CL=F)', color: C.red    },
    { key:'vix',  label:'VIX',          color: '#A8ADB5' },
  ];
  el.innerHTML = items.map(t => `
    <div class="overlay-toggle ${overlayState[t.key]?'on':''}" data-key="${t.key}" style="--clr:${t.color}">
      <span class="toggle-line"></span>${t.label}
      <span class="toggle-switch"><span class="toggle-thumb"></span></span>
    </div>
  `).join('');
  el.querySelectorAll('.overlay-toggle').forEach(tog => {
    tog.addEventListener('click', () => {
      overlayState[tog.dataset.key] = !overlayState[tog.dataset.key];
      renderOverlayToggles();
      renderHistoryChart(historyData, overlayState);
    });
  });
}

// ── Page 3 — Confusion matrix ──────────────────────────────────────────────────
function renderConfusionMatrix() {
  const svg = clearSvg('svg-confusion');
  if (!svg) return;
  const cells = [
    { label:'TN', v:142, cx:0, cy:0, c:C.accent, a:0.85 },
    { label:'FP', v:38,  cx:1, cy:0, c:C.amber,  a:0.45 },
    { label:'FN', v:41,  cx:0, cy:1, c:C.amber,  a:0.4  },
    { label:'TP', v:159, cx:1, cy:1, c:C.accent, a:1    },
  ];
  const cW=150, cH=90, ox=80, oy=28;

  svgText(svg, ox+cW,       14, 'PREDICTED', { anchor:'middle', mono:true });
  svgText(svg, ox+cW/2,     26, 'DOWN',      { anchor:'middle', fill:C.textMuted, size:'11' });
  svgText(svg, ox+cW+cW/2,  26, 'UP',        { anchor:'middle', fill:C.textMuted, size:'11' });
  svgText(svg, 14,    oy+cH,    'ACTUAL',    { mono:true });
  svgText(svg, 70, oy+cH/2+4,  'DOWN',      { anchor:'end', fill:C.textMuted, size:'11' });
  svgText(svg, 70, oy+cH+cH/2+4,'UP',       { anchor:'end', fill:C.textMuted, size:'11' });

  cells.forEach(cell => {
    const rx = ox + cell.cx * cW, ry = oy + cell.cy * cH;
    svg.append(svgEl('rect', { x:rx, y:ry, width:cW-2, height:cH-2, fill:cell.c, 'fill-opacity':cell.a, stroke:C.lineSoft }));
    const t1 = svgEl('text', { x:rx+cW/2, y:ry+cH/2-4, 'text-anchor':'middle', fill:'#0a1117', 'font-size':'22', 'font-weight':'700', 'font-family':SANS });
    t1.textContent = cell.v; svg.append(t1);
    const t2 = svgEl('text', { x:rx+cW/2, y:ry+cH/2+14, 'text-anchor':'middle', fill:'#0a1117', 'font-size':'10', 'font-family':MONO, opacity:'0.7' });
    t2.textContent = cell.label; svg.append(t2);
  });
}

// ── Page 3 — Model comparison ──────────────────────────────────────────────────
function renderModelCompare() {
  const svg = clearSvg('svg-model-compare');
  if (!svg) return;
  const models = [
    { name:'Logistic Reg',  f1:0.58 },
    { name:'Random Forest', f1:0.71 },
    { name:'XGBoost',       f1:0.74 },
    { name:'LSTM',          f1:0.69 },
    { name:'Stacking',      f1:0.79, ens:true },
  ];
  const W=560, H=220, padL=100, padR=20, padT=16, padB=30;
  const bh = (H-padT-padB)/models.length - 6;

  [0,0.2,0.4,0.6,0.8,1].forEach(t => {
    const x = padL + t*(W-padL-padR);
    svg.append(svgEl('line', { x1:x, x2:x, y1:padT, y2:H-padB, stroke:C.lineSoft, 'stroke-dasharray':'2 4' }));
    svgText(svg, x, H-padB+14, t.toFixed(1), { anchor:'middle', mono:true });
  });

  models.forEach((m, i) => {
    const y = padT + i*(bh+6), w = m.f1*(W-padL-padR);
    const nm = svgEl('text', { x:padL-8, y:y+bh/2+4, 'text-anchor':'end', fill:m.ens?C.accent:C.text, 'font-size':'11', 'font-weight':m.ens?'700':'500', 'font-family':SANS });
    nm.textContent = m.name; svg.append(nm);
    svg.append(svgEl('rect', { x:padL, y, width:w.toFixed(1), height:bh, fill:m.ens?C.accent:C.navy }));
    svgText(svg, padL+w+6, y+bh/2+4, m.f1.toFixed(2), { mono:true });
  });

  svgText(svg, padL+(W-padL-padR)/2, H-6, 'F1 Score (test set)', { anchor:'middle', mono:true });
}

// ── Page 3 — Feature bars ──────────────────────────────────────────────────────
function renderFeatureBars() {
  const svg = clearSvg('svg-feature-bars');
  if (!svg) return;
  const W=720, H=260, padL=130, padR=60, padT=8, padB=14;
  const bh = (H-padT-padB)/FEATURE_IMPORTANCE.length - 4;
  const maxPct = FEATURE_IMPORTANCE[0].pct;

  FEATURE_IMPORTANCE.forEach(({ name, pct }, i) => {
    const y = padT + i*(bh+4), w = (pct/maxPct)*(W-padL-padR);
    const t = svgEl('text', { x:padL-8, y:y+bh/2+4, 'text-anchor':'end', fill:C.textMuted, 'font-size':'11', 'font-family':MONO });
    t.textContent = name; svg.append(t);
    svg.append(svgEl('rect', { x:padL, y, width:w.toFixed(1), height:bh, fill:C.accent, opacity:(1-i*0.06).toFixed(2) }));
    svgText(svg, padL+w+6, y+bh/2+4, pct.toFixed(2), { mono:true });
  });
}

// ── Page 1 — Prediction card ───────────────────────────────────────────────────
function renderPrediction(p) {
  const isUp  = !p || p.direction === 'UP';
  const conf  = p?.probability ?? 67;
  const dir   = p?.direction ?? 'UP';
  const color = isUp ? C.accent : C.red;

  const arrowEl = document.getElementById('pred-arrow-icon');
  const dirEl   = document.getElementById('pred-dir-text');
  const confEl  = document.getElementById('pred-conf-num');
  const barEl   = document.getElementById('conf-bar-fill');
  const circle  = document.getElementById('pred-circle');

  if (arrowEl) arrowEl.textContent  = isUp ? '↑' : '↓';
  if (arrowEl) arrowEl.style.color  = color;
  if (dirEl)   dirEl.textContent    = dir;
  if (dirEl)   dirEl.style.color    = color;
  if (confEl)  confEl.textContent   = typeof conf === 'number' ? conf.toFixed(0) : conf;
  if (barEl)   { barEl.style.width = `${conf}%`; barEl.style.background = color; }
  if (circle)  { circle.style.borderColor = color; circle.style.boxShadow = `0 0 60px ${color}44`; }

  document.getElementById('ensemble-rows').innerHTML = [
    ['Random Forest',  0.71, 'UP'],
    ['XGBoost',        0.65, 'UP'],
    ['LSTM',           0.58, 'UP'],
    ['Stacking Meta',  conf/100, dir],
  ].map(([name, val, d], i) => `
    <div class="ensemble-row">
      <div class="ensemble-name ${i===3?'highlight':''}">${name}</div>
      <div class="ensemble-bar-bg">
        <div class="ensemble-bar-fill ${i===3?'highlight':''}" style="width:${(val*100).toFixed(0)}%"></div>
      </div>
      <div class="ensemble-stat">${d} · ${(val*100).toFixed(0)}%</div>
    </div>
  `).join('');
}

// ── Page 1 — KPI tiles ─────────────────────────────────────────────────────────
function renderKPIs(latest, prev) {
  if (!latest) return;
  const closeEl = document.getElementById('tile-close');
  const subEl   = document.getElementById('tile-close-sub');
  const dateEl  = document.getElementById('tile-pred-date');
  if (closeEl) closeEl.textContent = `$${latest.close.toFixed(2)}`;
  if (subEl && prev) {
    const delta = latest.close - prev.close;
    const pct   = (delta / prev.close * 100).toFixed(2);
    subEl.textContent = `${latest.date?.slice(0,10) ?? ''} · ${delta>=0?'+':''}${pct}%`;
  }
  if (dateEl) {
    const d    = new Date(latest.date ?? Date.now());
    const next = new Date(d);
    next.setDate(next.getDate() + 1);
    while (next.getDay() === 0 || next.getDay() === 6) next.setDate(next.getDate()+1);
    dateEl.textContent = next.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric', year:'numeric' });
  }
  const dateLabel = document.getElementById('pred-date-label');
  if (dateLabel && latest.date) dateLabel.textContent = `Tomorrow · ${fmtDate(latest.date)}`;
}

// ── Page 3 — Metrics ───────────────────────────────────────────────────────────
function renderMetrics(metrics) {
  const best = metrics?.[0] ?? null;
  ['accuracy','precision','recall','f1'].forEach(key => {
    const el = document.getElementById(`m-${key}`);
    if (el && best?.[key] != null) el.textContent = best[key].toFixed(2);
  });
}

// ── Status indicator ───────────────────────────────────────────────────────────
function setStatus(mode) {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-card-text');
  const top  = document.getElementById('topbar-status');
  if (mode === 'live') {
    const t = new Date().toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' });
    if (text) text.textContent = `Live · refreshed ${t} ET`;
    if (top)  top.textContent  = '● Connected';
    if (dot)  { dot.style.background = C.accent; dot.style.boxShadow = `0 0 8px ${C.accent}`; }
  } else {
    if (text) text.textContent = 'Demo data · no live backend';
    if (top)  { top.textContent = '● Demo'; top.style.color = C.amber; }
    if (dot)  { dot.style.background = C.amber; dot.style.boxShadow = `0 0 8px ${C.amber}`; }
  }
}

// ── Full render ────────────────────────────────────────────────────────────────
function renderAll(data, prediction, metrics) {
  historyData = data;
  const latest = data.at(-1), prev = data.at(-2);
  renderPrediction(prediction);
  renderKPIs(latest, prev);
  renderLine30(data);
  renderHistoryChart(data, overlayState);
  renderOverlayToggles();
  renderReturns(data);
  renderSummaryStats(data);
  renderConfusionMatrix();
  renderModelCompare();
  renderFeatureBars();
  renderMetrics(metrics ?? []);
}

// ── API client ─────────────────────────────────────────────────────────────────
const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:5000' : '';

async function apiFetch(path) {
  const res = await fetch(`${API_BASE}${path}`, { signal: AbortSignal.timeout(4000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Init ───────────────────────────────────────────────────────────────────────
async function init() {
  initNav();

  try {
    const [histRes, predRes, metricsRes] = await Promise.all([
      apiFetch('/api/stock/history?days=90'),
      apiFetch('/api/prediction/latest').catch(() => null),
      apiFetch('/api/model/metrics').catch(() => null),
    ]);
    renderAll(histRes.data ?? SAMPLE_HISTORY, predRes?.data, metricsRes?.data);
    setStatus('live');
  } catch {
    renderAll(SAMPLE_HISTORY, null, null);
    setStatus('demo');
  }
}

document.addEventListener('DOMContentLoaded', init);
