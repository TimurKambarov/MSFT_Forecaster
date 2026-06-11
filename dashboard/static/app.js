'use strict';

// ── Design tokens — read from CSS variables so theme switching works ──────────
const MONO = '"JetBrains Mono","SF Mono",Menlo,monospace';
const SANS = '"Montserrat","Helvetica Neue",Helvetica,Arial,sans-serif';

function getColors() {
  const s = getComputedStyle(document.documentElement);
  const v = n => s.getPropertyValue(n).trim();
  return {
    bg:        v('--bg'),
    bgSoft:    v('--bg-soft'),
    bgSofter:  v('--bg-softer'),
    line:      v('--line'),
    lineSoft:  v('--line-soft'),
    text:      v('--text'),
    textMuted: v('--text-muted'),
    textDim:   v('--text-dim'),
    accent:    v('--accent'),
    navy:      v('--navy'),
    amber:     v('--amber'),
    red:       v('--red'),
  };
}
let C = getColors();

// ── Sample data (real MSFT + Gold + Oil + VIX, Nov 2024 – Feb 2025) ───────────
const SAMPLE_HISTORY = [
  {date:"2024-05-01",open:385.84,high:394.79,low:383.58,close:388.13,volume:23562500,gold_close:2299.9,oil_close:79.0,vix:15.39},
  {date:"2024-05-02",open:390.8,high:393.03,low:387.84,close:390.98,volume:17709400,gold_close:2299.2,oil_close:78.95,vix:14.68},
  {date:"2024-05-03",open:395.34,high:400.13,low:394.93,close:399.65,volume:17446700,gold_close:2299.0,oil_close:78.11,vix:13.49},
  {date:"2024-05-06",open:401.71,high:406.79,low:399.36,close:406.41,volume:16996600,gold_close:2321.6,oil_close:78.48,vix:13.49},
  {date:"2024-05-07",open:407.51,high:407.52,low:402.04,close:402.28,volume:20018200,gold_close:2315.2,oil_close:78.38,vix:13.23},
  {date:"2024-05-08",open:401.13,high:405.12,low:399.7,close:403.46,volume:11792300,gold_close:2313.6,oil_close:78.99,vix:13.0},
  {date:"2024-05-09",open:403.49,high:405.6,low:402.04,close:405.21,volume:14689700,gold_close:2332.1,oil_close:79.26,vix:12.69},
  {date:"2024-05-10",open:405.82,high:408.22,low:404.7,close:407.59,volume:13402300,gold_close:2367.3,oil_close:78.26,vix:12.55},
  {date:"2024-05-13",open:410.8,high:411.14,low:403.74,close:406.59,volume:15440200,gold_close:2336.1,oil_close:79.12,vix:13.6},
  {date:"2024-05-14",open:404.91,high:410.29,low:404.45,close:409.38,volume:15109300,gold_close:2353.4,oil_close:78.02,vix:13.42},
  {date:"2024-05-15",open:411.43,high:417.25,low:410.81,close:416.53,volume:22239500,gold_close:2388.7,oil_close:78.63,vix:12.45},
  {date:"2024-05-16",open:415.27,high:418.84,low:413.85,close:414.48,volume:17530100,gold_close:2380.0,oil_close:79.23,vix:12.42},
  {date:"2024-05-17",open:416.0,high:416.38,low:411.56,close:413.71,volume:15352200,gold_close:2412.2,oil_close:80.06,vix:11.99},
  {date:"2024-05-20",open:413.71,high:420.17,low:413.49,close:418.76,volume:16272100,gold_close:2433.9,oil_close:79.8,vix:12.15},
  {date:"2024-05-21",open:420.23,high:426.27,low:418.28,close:422.4,volume:21453300,gold_close:2421.7,oil_close:79.26,vix:11.86},
  {date:"2024-05-22",open:423.44,high:425.72,low:420.52,close:423.86,volume:18073700,gold_close:2389.2,oil_close:77.57,vix:12.29},
  {date:"2024-05-23",open:426.27,high:426.89,low:418.84,close:420.39,volume:17211700,gold_close:2335.0,oil_close:76.87,vix:12.77},
  {date:"2024-05-24",open:420.58,high:424.39,low:417.84,close:423.5,volume:11855300,gold_close:2332.5,oil_close:77.72,vix:11.93},
  {date:"2024-05-28",open:422.98,high:424.15,low:420.0,close:423.66,volume:15718000,gold_close:2355.2,oil_close:79.83,vix:12.92},
  {date:"2024-05-29",open:419.1,high:424.27,low:419.1,close:422.53,volume:15517100,gold_close:2340.3,oil_close:79.23,vix:14.28},
  {date:"2024-05-30",open:417.73,high:417.73,low:407.83,close:408.25,volume:28394500,gold_close:2342.9,oil_close:77.91,vix:14.47},
  {date:"2024-05-31",open:410.3,high:410.3,low:398.25,close:408.71,volume:47995300,gold_close:2322.9,oil_close:76.99,vix:12.92},
  {date:"2024-06-03",open:409.1,high:409.99,low:402.59,close:407.12,volume:17484700,gold_close:2346.6,oil_close:74.22,vix:13.11},
  {date:"2024-06-04",open:406.05,high:410.0,low:403.34,close:409.63,volume:14348900,gold_close:2325.5,oil_close:73.25,vix:13.16},
  {date:"2024-06-05",open:411.35,high:417.52,low:409.86,close:417.45,volume:16988000,gold_close:2354.1,oil_close:74.07,vix:12.63},
  {date:"2024-06-06",open:417.45,high:418.73,low:414.07,close:417.95,volume:14861300,gold_close:2370.3,oil_close:75.55,vix:12.58},
  {date:"2024-06-07",open:419.61,high:419.68,low:416.46,close:417.29,volume:13621700,gold_close:2305.2,oil_close:75.53,vix:12.22},
  {date:"2024-06-10",open:418.13,high:421.46,low:417.33,close:421.25,volume:13982900,gold_close:2307.7,oil_close:77.74,vix:12.74},
  {date:"2024-06-11",open:418.9,high:426.12,low:418.67,close:425.99,volume:14551100,gold_close:2307.5,oil_close:77.9,vix:12.85},
  {date:"2024-06-12",open:428.58,high:436.54,low:426.55,close:434.24,volume:22366200,gold_close:2336.0,oil_close:78.5,vix:12.04},
  {date:"2024-06-13",open:434.03,high:436.53,low:432.57,close:434.75,volume:15960600,gold_close:2300.2,oil_close:78.62,vix:11.94},
  {date:"2024-06-14",open:431.5,high:436.28,low:429.96,close:435.72,volume:13582000,gold_close:2331.4,oil_close:78.45,vix:12.66},
  {date:"2024-06-17",open:435.74,high:443.96,low:433.9,close:441.43,volume:20790000,gold_close:2312.4,oil_close:80.33,vix:12.75},
  {date:"2024-06-18",open:442.75,high:443.18,low:438.01,close:439.43,volume:17112500,gold_close:2330.4,oil_close:81.57,vix:12.3},
  {date:"2024-06-20",open:439.39,high:439.62,low:434.44,close:438.8,volume:19877400,gold_close:2353.8,oil_close:82.17,vix:13.28},
  {date:"2024-06-21",open:440.46,high:443.61,low:439.6,close:442.82,volume:34187100,gold_close:2316.4,oil_close:80.73,vix:13.2},
  {date:"2024-06-24",open:442.84,high:445.74,low:439.5,close:440.74,volume:15913700,gold_close:2330.0,oil_close:81.63,vix:13.33},
  {date:"2024-06-25",open:441.31,high:444.44,low:439.84,close:443.97,volume:16413400,gold_close:2316.6,oil_close:80.83,vix:12.84},
  {date:"2024-06-26",open:442.05,high:446.58,low:441.26,close:445.16,volume:16507000,gold_close:2299.2,oil_close:80.9,vix:12.55},
  {date:"2024-06-27",open:445.18,high:449.11,low:444.78,close:445.84,volume:14806300,gold_close:2324.5,oil_close:81.74,vix:12.24},
  {date:"2024-06-28",open:446.06,high:448.33,low:439.5,close:440.03,volume:28362300,gold_close:2327.7,oil_close:81.54,vix:12.44},
  {date:"2024-07-01",open:441.72,high:450.29,low:438.76,close:449.66,volume:17662800,gold_close:2327.6,oil_close:83.38,vix:12.22},
  {date:"2024-07-02",open:446.19,high:452.48,low:446.1,close:452.17,volume:13979800,gold_close:2323.0,oil_close:82.81,vix:12.03},
  {date:"2024-07-03",open:451.1,high:453.89,low:450.8,close:453.64,volume:9932800,gold_close:2359.8,oil_close:83.88,vix:12.09},
  {date:"2024-07-05",open:452.5,high:461.1,low:451.87,close:460.33,volume:16000300,gold_close:2388.5,oil_close:83.16,vix:12.48},
  {date:"2024-07-08",open:459.33,high:460.46,low:457.27,close:459.03,volume:12962300,gold_close:2355.2,oil_close:82.33,vix:12.37},
  {date:"2024-07-09",open:459.77,high:460.1,low:450.91,close:452.43,volume:17207200,gold_close:2360.1,oil_close:81.41,vix:12.51},
  {date:"2024-07-10",open:454.08,high:459.24,low:451.76,close:459.04,volume:18196100,gold_close:2372.2,oil_close:82.1,vix:12.85},
  {date:"2024-07-11",open:455.82,high:457.59,low:444.56,close:447.66,volume:23111200,gold_close:2415.0,oil_close:82.62,vix:12.92},
  {date:"2024-07-12",open:447.3,high:449.3,low:443.68,close:446.53,volume:16324300,gold_close:2414.0,oil_close:82.21,vix:12.46},
  {date:"2024-07-15",open:446.29,high:450.18,low:444.45,close:446.94,volume:14429400,gold_close:2422.9,oil_close:81.91,vix:13.12},
  {date:"2024-07-16",open:447.19,high:447.27,low:439.75,close:442.56,volume:17175700,gold_close:2462.4,oil_close:80.76,vix:13.19},
  {date:"2024-07-17",open:435.74,high:437.97,low:432.38,close:436.66,volume:21778000,gold_close:2454.8,oil_close:82.85,vix:14.48},
  {date:"2024-07-18",open:437.46,high:437.77,low:427.68,close:433.56,volume:20794800,gold_close:2451.8,oil_close:82.82,vix:15.93},
  {date:"2024-07-19",open:426.4,high:434.31,low:425.32,close:430.35,volume:20940400,gold_close:2395.5,oil_close:80.13,vix:16.52},
  {date:"2024-07-22",open:434.95,high:437.72,low:432.12,close:436.09,volume:15808800,gold_close:2392.0,oil_close:79.78,vix:14.91},
  {date:"2024-07-23",open:437.03,high:441.45,low:436.24,close:437.97,volume:13107100,gold_close:2404.6,oil_close:76.96,vix:14.72},
  {date:"2024-07-24",open:433.64,high:434.65,low:420.97,close:422.26,volume:26805800,gold_close:2413.3,oil_close:77.59,vix:18.04},
  {date:"2024-07-25",open:422.17,high:423.15,low:411.05,close:411.93,volume:29943800,gold_close:2351.9,oil_close:78.28,vix:18.46},
  {date:"2024-07-26",open:411.73,high:422.28,low:410.81,close:418.69,volume:23583800,gold_close:2380.0,oil_close:77.16,vix:16.39},
  {date:"2024-07-29",open:424.9,high:425.46,low:418.13,close:420.13,volume:15125800,gold_close:2377.3,oil_close:75.81,vix:16.6},
  {date:"2024-07-30",open:421.1,high:422.41,low:410.9,close:416.38,volume:32687600,gold_close:2405.0,oil_close:74.73,vix:17.69},
  {date:"2024-07-31",open:413.99,high:415.25,low:405.83,close:411.88,volume:42891400,gold_close:2426.5,oil_close:77.91,vix:16.36},
  {date:"2024-08-01",open:414.28,high:420.85,low:406.7,close:410.66,volume:30296400,gold_close:2435.0,oil_close:76.31,vix:18.59},
  {date:"2024-08-02",open:406.11,high:408.58,low:398.08,close:402.17,volume:29437900,gold_close:2425.7,oil_close:73.52,vix:23.39},
  {date:"2024-08-05",open:383.15,high:394.83,low:379.61,close:389.04,volume:40709200,gold_close:2401.7,oil_close:72.94,vix:38.57},
  {date:"2024-08-06",open:393.81,high:399.39,low:392.33,close:393.43,volume:24946500,gold_close:2389.1,oil_close:73.2,vix:27.71},
  {date:"2024-08-07",open:402.32,high:403.73,low:391.32,close:392.27,volume:20650900,gold_close:2390.5,oil_close:75.23,vix:27.85},
  {date:"2024-08-08",open:396.21,high:399.58,low:393.75,close:396.46,volume:20203000,gold_close:2422.2,oil_close:76.19,vix:23.79},
  {date:"2024-08-09",open:397.78,high:401.74,low:396.04,close:399.74,volume:19276700,gold_close:2432.1,oil_close:76.84,vix:20.37},
  {date:"2024-08-12",open:400.76,high:402.44,low:397.99,close:400.52,volume:16762900,gold_close:2462.4,oil_close:80.06,vix:20.71},
  {date:"2024-08-13",open:403.25,high:408.53,low:403.23,close:407.6,volume:19414300,gold_close:2466.7,oil_close:78.35,vix:18.12},
  {date:"2024-08-14",open:408.38,high:411.26,low:406.07,close:410.41,volume:18267000,gold_close:2439.4,oil_close:76.98,vix:16.19},
  {date:"2024-08-15",open:414.05,high:415.34,low:411.94,close:415.26,volume:20752100,gold_close:2453.1,oil_close:78.16,vix:15.23},
  {date:"2024-08-16",open:414.84,high:415.57,low:411.58,close:412.74,volume:22775600,gold_close:2498.6,oil_close:76.65,vix:14.8},
  {date:"2024-08-19",open:413.22,high:415.97,low:410.76,close:415.76,volume:15234000,gold_close:2501.8,oil_close:74.37,vix:14.65},
  {date:"2024-08-20",open:415.92,high:420.03,low:415.86,close:418.98,volume:16387600,gold_close:2511.3,oil_close:74.04,vix:15.88},
  {date:"2024-08-21",open:418.27,high:420.56,low:415.94,close:418.33,volume:16067300,gold_close:2508.4,oil_close:71.93,vix:16.27},
  {date:"2024-08-22",open:418.55,high:420.94,low:408.93,close:409.86,volume:19361900,gold_close:2478.9,oil_close:73.01,vix:17.55},
  {date:"2024-08-23",open:411.27,high:413.52,low:406.45,close:411.08,volume:18493800,gold_close:2508.4,oil_close:74.83,vix:15.86},
  {date:"2024-08-26",open:410.67,high:411.56,low:405.71,close:407.83,volume:13152800,gold_close:2517.7,oil_close:77.42,vix:16.15},
  {date:"2024-08-27",open:407.2,high:408.68,low:404.63,close:408.17,volume:13492900,gold_close:2516.0,oil_close:75.53,vix:15.43},
  {date:"2024-08-28",open:409.2,high:409.32,low:401.73,close:404.98,volume:14882700,gold_close:2501.0,oil_close:74.52,vix:17.11},
  {date:"2024-08-29",open:409.26,high:416.27,low:404.98,close:407.46,volume:17045200,gold_close:2525.7,oil_close:75.91,vix:15.65},
  {date:"2024-08-30",open:409.91,high:411.77,low:406.48,close:411.43,volume:24308300,gold_close:2493.8,oil_close:73.55,vix:15.0},
  {date:"2024-09-03",open:412.19,high:414.13,low:401.45,close:403.83,volume:20313600,gold_close:2489.9,oil_close:70.34,vix:20.72},
  {date:"2024-09-04",open:400.35,high:405.61,low:398.83,close:403.3,volume:15135800,gold_close:2493.4,oil_close:69.2,vix:21.32},
  {date:"2024-09-05",open:402.04,high:407.44,low:400.57,close:402.8,volume:14195500,gold_close:2511.4,oil_close:69.15,vix:19.9},
  {date:"2024-09-06",open:403.46,high:405.02,low:395.31,close:396.2,volume:19609500,gold_close:2493.5,oil_close:67.67,vix:22.38},
  {date:"2024-09-09",open:401.66,high:403.05,low:396.64,close:400.16,volume:15295100,gold_close:2501.8,oil_close:68.71,vix:19.45},
  {date:"2024-09-10",open:402.61,high:410.63,low:402.12,close:408.53,volume:19594300,gold_close:2512.3,oil_close:65.75,vix:19.08},
  {date:"2024-09-11",open:409.81,high:418.18,low:403.97,close:417.25,volume:19266900,gold_close:2512.1,oil_close:67.31,vix:17.69},
  {date:"2024-09-12",open:417.51,high:421.52,low:414.0,close:421.15,volume:17395700,gold_close:2551.2,oil_close:68.97,vix:17.07},
  {date:"2024-09-13",open:420.0,high:425.91,low:419.63,close:424.69,volume:15874600,gold_close:2581.3,oil_close:68.65,vix:16.56},
  {date:"2024-09-16",open:424.7,high:427.59,low:422.35,close:425.43,volume:13834700,gold_close:2580.4,oil_close:70.09,vix:17.14},
  {date:"2024-09-17",open:434.2,high:435.8,low:426.35,close:429.19,volume:18874200,gold_close:2564.3,oil_close:71.19,vix:17.61},
  {date:"2024-09-18",open:429.04,high:430.06,low:424.51,close:424.91,volume:18898000,gold_close:2570.7,oil_close:70.91,vix:18.23},
  {date:"2024-09-19",open:435.19,high:435.45,low:430.92,close:432.68,volume:21706600,gold_close:2588.0,oil_close:71.95,vix:16.33},
  {date:"2024-09-20",open:431.23,high:433.22,low:428.27,close:429.31,volume:55167100,gold_close:2619.9,oil_close:71.92,vix:16.15},
  {date:"2024-09-23",open:428.33,high:430.48,low:424.49,close:427.57,volume:15128900,gold_close:2626.5,oil_close:70.37,vix:15.89},
  {date:"2024-09-24",open:427.07,high:427.41,low:420.26,close:423.29,volume:17015800,gold_close:2651.2,oil_close:71.56,vix:15.39},
  {date:"2024-09-25",open:423.94,high:427.19,low:422.7,close:426.19,volume:13396400,gold_close:2659.2,oil_close:69.69,vix:15.41},
  {date:"2024-09-26",open:429.13,high:429.34,low:423.25,close:425.4,volume:14492000,gold_close:2669.9,oil_close:67.67,vix:15.37},
  {date:"2024-09-27",open:425.61,high:425.93,low:421.61,close:422.16,volume:14896100,gold_close:2644.3,oil_close:68.18,vix:16.96},
  {date:"2024-09-30",open:422.34,high:424.52,low:419.54,close:424.41,volume:16807300,gold_close:2636.1,oil_close:68.17,vix:16.73},
  {date:"2024-10-01",open:422.58,high:422.61,low:413.07,close:414.93,volume:19092900,gold_close:2667.3,oil_close:69.83,vix:19.26},
  {date:"2024-10-02",open:416.79,high:417.03,low:411.0,close:411.42,volume:16582300,gold_close:2647.1,oil_close:70.1,vix:18.9},
  {date:"2024-10-03",open:411.91,high:413.8,low:408.62,close:410.83,volume:13686400,gold_close:2657.1,oil_close:73.71,vix:20.49},
  {date:"2024-10-04",open:412.51,high:414.0,low:409.29,close:410.36,volume:19169700,gold_close:2645.8,oil_close:74.38,vix:19.21},
  {date:"2024-10-07",open:410.3,high:411.4,low:403.4,close:403.93,volume:20919800,gold_close:2644.8,oil_close:77.14,vix:22.64},
  {date:"2024-10-08",open:405.27,high:409.97,low:402.58,close:409.03,volume:19229300,gold_close:2615.0,oil_close:73.57,vix:21.42},
  {date:"2024-10-09",open:410.16,high:414.62,low:408.62,close:411.74,volume:14974300,gold_close:2606.0,oil_close:73.24,vix:20.86},
  {date:"2024-10-10",open:409.54,high:411.63,low:407.49,close:410.14,volume:13848400,gold_close:2620.6,oil_close:75.85,vix:20.93},
  {date:"2024-10-11",open:410.44,high:411.42,low:407.59,close:410.62,volume:14144900,gold_close:2657.6,oil_close:75.56,vix:20.46},
  {date:"2024-10-14",open:412.05,high:418.23,low:411.8,close:413.4,volume:16653100,gold_close:2647.8,oil_close:73.83,vix:19.7},
  {date:"2024-10-15",open:416.4,high:416.69,low:409.57,close:413.0,volume:18900200,gold_close:2661.4,oil_close:70.58,vix:20.64},
  {date:"2024-10-16",open:409.48,high:410.66,low:404.86,close:410.42,volume:15508900,gold_close:2674.0,oil_close:70.39,vix:19.58},
  {date:"2024-10-17",open:416.57,high:416.71,low:409.9,close:411.01,volume:14820000,gold_close:2691.0,oil_close:70.67,vix:19.11},
  {date:"2024-10-18",open:411.43,high:413.9,low:410.56,close:412.43,volume:17145300,gold_close:2713.7,oil_close:69.22,vix:18.03},
  {date:"2024-10-21",open:410.42,high:413.22,low:408.08,close:413.04,volume:14206100,gold_close:2723.1,oil_close:70.56,vix:18.37},
  {date:"2024-10-22",open:412.76,high:424.68,low:412.31,close:421.65,volume:25482200,gold_close:2744.2,oil_close:72.09,vix:18.2},
  {date:"2024-10-23",open:424.96,high:425.18,low:416.74,close:418.78,volume:19654400,gold_close:2714.4,oil_close:70.77,vix:19.24},
  {date:"2024-10-24",open:419.5,high:420.14,low:416.61,close:418.91,volume:13581600,gold_close:2734.9,oil_close:70.19,vix:19.08},
  {date:"2024-10-25",open:420.91,high:426.6,low:420.73,close:422.29,volume:16899100,gold_close:2740.9,oil_close:71.78,vix:20.33},
  {date:"2024-10-28",open:425.75,high:426.02,low:420.46,close:420.75,volume:14882400,gold_close:2742.9,oil_close:67.38,vix:19.8},
  {date:"2024-10-29",open:422.14,high:427.24,low:419.97,close:426.03,volume:17644100,gold_close:2768.4,oil_close:67.21,vix:19.34},
  {date:"2024-10-30",open:431.45,high:432.49,low:426.18,close:426.61,volume:29749100,gold_close:2788.5,oil_close:68.61,vix:20.35},
  {date:"2024-10-31",open:409.67,high:410.46,low:400.73,close:400.78,volume:53971000,gold_close:2738.3,oil_close:69.26,vix:23.16},
  {date:"2024-11-01",open:403.41,high:409.81,low:401.92,close:404.75,volume:24230400,gold_close:2738.6,oil_close:69.49,vix:21.88},
  {date:"2024-11-04",open:404.19,high:404.8,low:400.01,close:402.86,volume:19672300,gold_close:2736.1,oil_close:71.47,vix:21.98},
  {date:"2024-11-05",open:402.78,high:409.22,low:402.49,close:405.82,volume:17626000,gold_close:2740.3,oil_close:71.99,vix:20.49},
  {date:"2024-11-06",open:406.77,high:414.69,low:404.9,close:414.42,volume:26681800,gold_close:2667.6,oil_close:71.69,vix:16.27},
  {date:"2024-11-07",open:415.51,high:421.0,low:414.13,close:419.6,volume:19901800,gold_close:2698.4,oil_close:72.36,vix:15.2},
  {date:"2024-11-08",open:419.49,high:420.66,low:416.0,close:416.75,volume:16891400,gold_close:2687.5,oil_close:70.38,vix:14.94},
  {date:"2024-11-11",open:416.73,high:418.99,low:410.3,close:412.28,volume:24503300,gold_close:2611.2,oil_close:68.04,vix:14.97},
  {date:"2024-11-12",open:412.52,high:418.63,low:411.49,close:417.24,volume:19401200,gold_close:2600.0,oil_close:68.12,vix:14.71},
  {date:"2024-11-13",open:415.86,high:423.45,low:412.48,close:419.38,volume:21502200,gold_close:2580.8,oil_close:68.43,vix:14.02},
  {date:"2024-11-14",open:419.18,high:422.3,low:414.25,close:421.04,volume:30246900,gold_close:2568.2,oil_close:68.7,vix:14.31},
  {date:"2024-11-15",open:414.07,high:417.01,low:407.97,close:409.32,volume:28247600,gold_close:2565.7,oil_close:67.02,vix:16.14},
  {date:"2024-11-18",open:409.19,high:412.67,low:406.46,close:410.06,volume:24727000,gold_close:2610.6,oil_close:69.16,vix:15.58},
  {date:"2024-11-19",open:407.45,high:412.22,low:405.91,close:412.07,volume:18133500,gold_close:2627.1,oil_close:69.39,vix:16.35},
  {date:"2024-11-20",open:411.16,high:411.57,low:404.96,close:409.8,volume:19191700,gold_close:2648.2,oil_close:68.87,vix:17.16},
  {date:"2024-11-21",open:414.58,high:414.86,low:405.48,close:408.03,volume:20780200,gold_close:2672.1,oil_close:70.1,vix:16.87},
  {date:"2024-11-22",open:406.55,high:412.51,low:406.24,close:412.11,volume:24814600,gold_close:2709.9,oil_close:71.24,vix:15.24},
  {date:"2024-11-25",open:413.47,high:416.14,low:409.99,close:413.88,volume:27691100,gold_close:2616.8,oil_close:68.94,vix:14.6},
  {date:"2024-11-26",open:414.67,high:424.01,low:413.94,close:422.97,volume:23458900,gold_close:2620.3,oil_close:68.77,vix:14.1},
  {date:"2024-11-27",open:420.13,high:422.22,low:417.07,close:418.03,volume:18332400,gold_close:2639.9,oil_close:68.72,vix:14.1},
  {date:"2024-11-29",open:415.16,high:419.9,low:412.9,close:418.5,volume:16271900,gold_close:2657.0,oil_close:68.0,vix:13.51},
  {date:"2024-12-02",open:416.63,high:427.92,low:416.37,close:425.93,volume:20207200,gold_close:2634.9,oil_close:68.1,vix:13.34},
  {date:"2024-12-03",open:424.8,high:427.4,low:422.73,close:426.14,volume:18302000,gold_close:2644.7,oil_close:69.94,vix:13.3},
  {date:"2024-12-04",open:427.95,high:434.52,low:427.56,close:432.29,volume:26009400,gold_close:2653.8,oil_close:68.54,vix:13.45},
  {date:"2024-12-05",open:432.79,high:439.45,low:431.06,close:437.43,volume:21697800,gold_close:2626.6,oil_close:68.3,vix:13.54},
  {date:"2024-12-06",open:437.11,high:440.87,low:436.59,close:438.37,volume:18821000,gold_close:2638.6,oil_close:67.2,vix:12.77},
  {date:"2024-12-09",open:437.41,high:443.07,low:435.34,close:440.79,volume:19144400,gold_close:2664.9,oil_close:68.37,vix:14.19},
  {date:"2024-12-10",open:439.18,high:444.35,low:436.42,close:438.13,volume:18469500,gold_close:2697.6,oil_close:68.59,vix:14.18},
  {date:"2024-12-11",open:438.84,high:445.07,low:438.84,close:443.73,volume:19200200,gold_close:2733.8,oil_close:70.29,vix:13.58},
  {date:"2024-12-12",open:443.84,high:450.81,low:443.84,close:444.29,volume:20834800,gold_close:2687.5,oil_close:70.02,vix:13.92},
  {date:"2024-12-13",open:443.18,high:446.14,low:440.36,close:442.03,volume:20177800,gold_close:2656.0,oil_close:71.29,vix:13.81},
  {date:"2024-12-16",open:442.03,high:446.88,low:440.06,close:446.3,volume:23598800,gold_close:2651.4,oil_close:70.71,vix:14.69},
  {date:"2024-12-17",open:445.72,high:449.95,low:444.3,close:449.13,volume:22733500,gold_close:2644.4,oil_close:70.08,vix:15.87},
  {date:"2024-12-18",open:446.03,high:447.34,low:431.9,close:432.26,volume:24444500,gold_close:2636.5,oil_close:70.58,vix:27.62},
  {date:"2024-12-19",open:436.44,high:437.98,low:431.2,close:431.91,volume:22963700,gold_close:2592.2,oil_close:69.91,vix:24.09},
  {date:"2024-12-20",open:428.03,high:438.54,low:423.6,close:431.48,volume:64263700,gold_close:2628.7,oil_close:69.46,vix:18.36},
  {date:"2024-12-23",open:431.62,high:432.52,low:427.76,close:430.15,volume:19152500,gold_close:2612.3,oil_close:69.24,vix:16.78},
  {date:"2024-12-24",open:429.55,high:434.45,low:429.1,close:434.18,volume:7164500,gold_close:2620.0,oil_close:70.1,vix:14.27},
  {date:"2024-12-26",open:433.93,high:435.77,low:431.51,close:432.97,volume:8194200,gold_close:2638.8,oil_close:69.62,vix:14.73},
  {date:"2024-12-27",open:429.5,high:430.12,low:421.35,close:425.48,volume:18117700,gold_close:2617.2,oil_close:70.6,vix:15.95},
  {date:"2024-12-30",open:421.06,high:422.54,low:416.95,close:419.85,volume:13158700,gold_close:2606.1,oil_close:70.99,vix:17.4},
  {date:"2024-12-31",open:421.1,high:421.73,low:415.73,close:416.56,volume:13246500,gold_close:2629.2,oil_close:71.72,vix:17.35},
  {date:"2025-01-02",open:420.54,high:421.07,low:409.99,close:413.67,volume:16896500,gold_close:2658.9,oil_close:73.13,vix:17.93},
  {date:"2025-01-03",open:416.14,high:419.06,low:414.62,close:418.39,volume:16662900,gold_close:2645.0,oil_close:73.96,vix:16.13},
  {date:"2025-01-06",open:422.98,high:429.23,low:420.49,close:422.83,volume:20573600,gold_close:2638.4,oil_close:73.56,vix:16.04},
  {date:"2025-01-07",open:423.97,high:425.6,low:415.87,close:417.42,volume:18139100,gold_close:2656.7,oil_close:74.25,vix:17.82},
  {date:"2025-01-08",open:418.5,high:421.96,low:416.6,close:419.58,volume:15054600,gold_close:2664.5,oil_close:73.32,vix:17.7},
  {date:"2025-01-10",open:419.65,high:419.73,low:410.15,close:414.04,volume:20201100,gold_close:2708.5,oil_close:76.57,vix:19.54},
  {date:"2025-01-13",open:410.37,high:413.59,low:407.46,close:412.3,volume:17604800,gold_close:2673.5,oil_close:78.82,vix:19.19},
  {date:"2025-01-14",open:412.91,high:414.82,low:405.9,close:410.8,volume:16935900,gold_close:2677.5,oil_close:77.5,vix:18.71},
  {date:"2025-01-15",open:414.22,high:423.13,low:413.37,close:421.31,volume:19637800,gold_close:2712.5,oil_close:80.04,vix:16.12},
  {date:"2025-01-16",open:423.67,high:424.45,low:419.41,close:419.6,volume:15300000,gold_close:2746.4,oil_close:78.68,vix:16.6},
  {date:"2025-01-17",open:429.0,high:429.39,low:423.15,close:424.0,volume:26197500,gold_close:2744.3,oil_close:77.88,vix:15.97},
  {date:"2025-01-21",open:425.16,high:425.85,low:420.61,close:423.48,volume:26085700,gold_close:2755.0,oil_close:75.89,vix:15.06},
  {date:"2025-01-22",open:432.43,high:442.03,low:430.89,close:440.97,volume:27803800,gold_close:2767.6,oil_close:75.44,vix:15.1},
  {date:"2025-01-23",open:436.82,high:441.51,low:436.32,close:441.47,volume:18389300,gold_close:2763.1,oil_close:74.62,vix:15.02},
  {date:"2025-01-24",open:439.94,high:441.41,low:436.23,close:438.85,volume:15549500,gold_close:2777.3,oil_close:74.66,vix:14.85},
  {date:"2025-01-27",open:419.04,high:430.1,low:418.53,close:429.47,volume:35647800,gold_close:2737.5,oil_close:73.17,vix:17.9},
  {date:"2025-01-28",open:429.5,high:443.12,low:426.32,close:441.96,volume:23491700,gold_close:2766.8,oil_close:73.77,vix:16.41},
  {date:"2025-01-29",open:441.45,high:441.64,low:435.24,close:437.14,volume:23581400,gold_close:2769.1,oil_close:72.62,vix:16.56},
  {date:"2025-01-30",open:413.86,high:417.9,low:408.32,close:410.12,volume:54586300,gold_close:2823.0,oil_close:72.73,vix:15.84},
  {date:"2025-01-31",open:414.07,high:415.76,low:410.05,close:410.19,volume:34161900,gold_close:2812.5,oil_close:72.53,vix:16.43},
  {date:"2025-02-03",open:406.77,high:410.54,low:403.87,close:406.1,volume:25679100,gold_close:2833.9,oil_close:73.16,vix:18.62},
  {date:"2025-02-04",open:407.85,high:409.07,low:404.94,close:407.54,volume:20532100,gold_close:2853.3,oil_close:72.7,vix:17.21},
  {date:"2025-02-05",open:407.52,high:408.98,low:405.59,close:408.44,volume:16316700,gold_close:2871.6,oil_close:71.03,vix:15.77},
  {date:"2025-02-06",open:409.15,high:413.3,low:409.15,close:410.94,volume:16309800,gold_close:2856.0,oil_close:70.61,vix:15.5},
  {date:"2025-02-07",open:411.6,high:413.74,low:403.32,close:404.95,volume:22886800,gold_close:2867.3,oil_close:71.0,vix:16.54},
  {date:"2025-02-10",open:408.86,high:410.59,low:406.1,close:407.39,volume:20817900,gold_close:2914.3,oil_close:72.32,vix:15.81},
  {date:"2025-02-11",open:404.84,high:407.65,low:404.5,close:406.62,volume:18140600,gold_close:2912.5,oil_close:73.32,vix:16.02},
  {date:"2025-02-12",open:402.44,high:405.93,low:399.63,close:404.24,volume:19121700,gold_close:2909.0,oil_close:71.37,vix:15.89},
  {date:"2025-02-13",open:402.23,high:406.18,low:401.6,close:405.73,volume:23891700,gold_close:2925.9,oil_close:71.29,vix:15.1},
  {date:"2025-02-14",open:403.01,high:404.12,low:401.12,close:403.64,volume:22758500,gold_close:2883.6,oil_close:70.74,vix:14.77},
  {date:"2025-02-18",open:403.22,high:405.79,low:401.73,close:404.84,volume:21423100,gold_close:2931.6,oil_close:71.85,vix:15.35},
  {date:"2025-02-19",open:403.1,high:410.62,low:402.87,close:409.91,volume:24114200,gold_close:2919.4,oil_close:72.25,vix:15.27},
  {date:"2025-02-20",open:411.24,high:415.22,low:408.52,close:412.08,volume:23508700,gold_close:2940.0,oil_close:72.57,vix:15.66},
  {date:"2025-02-21",open:413.27,high:413.98,low:403.92,close:404.23,volume:27524800,gold_close:2937.6,oil_close:70.4,vix:18.21},
  {date:"2025-02-24",open:404.53,high:405.38,low:395.43,close:400.06,volume:26443700,gold_close:2947.9,oil_close:70.7,vix:18.98},
  {date:"2025-02-25",open:397.19,high:398.0,low:392.84,close:394.02,volume:29387400,gold_close:2904.5,oil_close:68.93,vix:19.43},
  {date:"2025-02-26",open:394.13,high:399.67,low:390.41,close:395.84,volume:19619000,gold_close:2916.8,oil_close:68.62,vix:19.1},
  {date:"2025-02-27",open:397.36,high:401.79,low:388.35,close:388.71,volume:21127400,gold_close:2883.2,oil_close:70.35,vix:21.13},
  {date:"2025-02-28",open:388.83,high:393.76,low:382.8,close:393.12,volume:32845700,gold_close:2836.8,oil_close:69.76,vix:19.63},
  {date:"2025-03-03",open:394.93,high:394.93,low:382.4,close:384.71,volume:23007700,gold_close:2890.2,oil_close:68.37,vix:22.78},
  {date:"2025-03-04",open:379.66,high:388.76,low:377.29,close:384.82,volume:29342900,gold_close:2909.6,oil_close:68.26,vix:23.51},
  {date:"2025-03-05",open:385.55,high:397.76,low:385.02,close:397.11,volume:23433100,gold_close:2915.3,oil_close:66.31,vix:21.93},
  {date:"2025-03-06",open:390.44,high:398.23,low:388.85,close:393.02,volume:23304600,gold_close:2916.6,oil_close:66.36,vix:24.87},
  {date:"2025-03-07",open:388.5,high:390.95,low:381.78,close:389.48,volume:22034100,gold_close:2904.7,oil_close:67.04,vix:23.37},
  {date:"2025-03-10",open:382.08,high:382.64,low:373.55,close:376.46,volume:32840100,gold_close:2891.0,oil_close:66.03,vix:27.86},
  {date:"2025-03-11",open:375.31,high:382.24,low:373.24,close:376.74,volume:30380200,gold_close:2912.9,oil_close:66.25,vix:26.92},
  {date:"2025-03-12",open:379.22,high:381.47,low:375.26,close:379.54,volume:24253600,gold_close:2939.1,oil_close:67.68,vix:24.23},
  {date:"2025-03-13",open:379.43,high:381.57,low:373.77,close:375.08,volume:20473000,gold_close:2984.3,oil_close:66.55,vix:24.66},
  {date:"2025-03-14",open:376.08,high:386.43,low:375.81,close:384.77,volume:19952800,gold_close:2994.5,oil_close:67.18,vix:21.77},
  {date:"2025-03-17",open:382.93,high:388.88,low:381.81,close:384.91,volume:22474300,gold_close:3000.0,oil_close:67.58,vix:20.51},
  {date:"2025-03-18",open:383.3,high:383.6,low:377.39,close:379.78,volume:19486900,gold_close:3035.1,oil_close:66.9,vix:21.7},
  {date:"2025-03-19",open:381.77,high:385.88,low:380.26,close:384.04,volume:19185500,gold_close:3035.9,oil_close:67.16,vix:19.9},
  {date:"2025-03-20",open:381.98,high:387.97,low:379.55,close:383.07,volume:18470500,gold_close:3040.0,oil_close:68.26,vix:19.8},
  {date:"2025-03-21",open:379.49,high:387.92,low:379.07,close:387.45,volume:39675900,gold_close:3018.2,oil_close:68.28,vix:19.28},
  {date:"2025-03-24",open:391.55,high:391.55,low:386.01,close:389.25,volume:21004500,gold_close:3013.1,oil_close:69.11,vix:17.48},
  {date:"2025-03-25",open:390.08,high:392.5,low:388.81,close:391.31,volume:15775000,gold_close:3023.7,oil_close:69.0,vix:17.15},
  {date:"2025-03-26",open:391.15,high:391.46,low:384.78,close:386.17,volume:16108400,gold_close:3020.9,oil_close:69.65,vix:18.33},
  {date:"2025-03-27",open:386.33,high:388.42,low:383.63,close:386.77,volume:13766800,gold_close:3060.2,oil_close:69.92,vix:18.69},
  {date:"2025-03-28",open:384.3,high:385.34,low:373.26,close:375.11,volume:21632000,gold_close:3086.5,oil_close:69.36,vix:21.65},
  {date:"2025-03-31",open:368.91,high:373.4,low:363.66,close:371.73,volume:35184700,gold_close:3122.8,oil_close:71.48,vix:22.28},
  {date:"2025-04-01",open:371.0,high:379.12,low:369.59,close:378.47,volume:19689500,gold_close:3118.9,oil_close:71.2,vix:21.77},
  {date:"2025-04-02",open:374.29,high:381.33,low:372.95,close:378.42,volume:16092600,gold_close:3139.9,oil_close:71.71,vix:21.51},
  {date:"2025-04-03",open:371.14,high:373.8,low:365.75,close:369.48,volume:30198000,gold_close:3097.0,oil_close:66.95,vix:30.02},
  {date:"2025-04-04",open:360.58,high:370.94,low:355.98,close:356.33,volume:49209900,gold_close:3012.0,oil_close:61.99,vix:45.31},
  {date:"2025-04-07",open:347.46,high:367.39,low:341.43,close:354.37,volume:50425000,gold_close:2951.3,oil_close:60.7,vix:46.98},
  {date:"2025-04-08",open:364.67,high:370.01,low:346.84,close:351.11,volume:35868900,gold_close:2968.4,oil_close:59.58,vix:52.33},
  {date:"2025-04-09",open:350.1,high:389.4,low:349.66,close:386.69,volume:50199700,gold_close:3056.5,oil_close:62.35,vix:33.62},
  {date:"2025-04-10",open:378.34,high:380.16,low:364.22,close:377.63,volume:38024400,gold_close:3155.2,oil_close:60.07,vix:40.72},
  {date:"2025-04-11",open:376.93,high:386.25,low:375.2,close:384.67,volume:23839200,gold_close:3222.2,oil_close:61.5,vix:37.56},
  {date:"2025-04-14",open:389.39,high:390.81,low:380.47,close:384.03,volume:19251200,gold_close:3204.8,oil_close:61.53,vix:30.89},
  {date:"2025-04-15",open:384.73,high:388.07,low:380.42,close:381.97,volume:17199900,gold_close:3218.7,oil_close:61.33,vix:30.12},
  {date:"2025-04-16",open:376.96,high:377.89,low:364.41,close:367.99,volume:21967800,gold_close:3326.6,oil_close:62.47,vix:32.64},
  {date:"2025-04-17",open:370.11,high:370.67,low:363.32,close:364.2,volume:21120200,gold_close:3308.7,oil_close:64.68,vix:29.65},
  {date:"2025-04-21",open:359.29,high:360.93,low:352.2,close:355.62,volume:20807300,gold_close:3406.2,oil_close:63.08,vix:33.82},
  {date:"2025-04-22",open:359.84,high:364.19,low:356.35,close:363.25,volume:19485000,gold_close:3400.8,oil_close:64.31,vix:30.57},
  {date:"2025-04-23",open:372.4,high:376.68,low:369.39,close:370.74,volume:20545500,gold_close:3276.3,oil_close:62.27,vix:28.45},
  {date:"2025-04-24",open:372.04,high:384.67,low:371.53,close:383.53,volume:22232300,gold_close:3332.0,oil_close:62.79,vix:26.47},
  {date:"2025-04-25",open:383.23,high:388.34,low:380.85,close:388.03,volume:18973200,gold_close:3282.4,oil_close:63.02,vix:24.84},
  {date:"2025-04-28",open:388.14,high:388.91,low:382.87,close:387.35,volume:16579400,gold_close:3332.5,oil_close:62.05,vix:25.15},
  {date:"2025-04-29",open:387.49,high:391.25,low:386.58,close:390.2,volume:14974000,gold_close:3318.8,oil_close:60.42,vix:24.17},
  {date:"2025-04-30",open:386.5,high:392.8,low:380.69,close:391.41,volume:36461100,gold_close:3305.0,oil_close:58.21,vix:24.7},
  {date:"2025-05-01",open:426.91,high:432.73,low:420.76,close:421.26,volume:58938100,gold_close:3210.0,oil_close:59.24,vix:24.6},
  {date:"2025-05-02",open:427.53,high:435.16,low:425.8,close:431.04,volume:30757400,gold_close:3231.9,oil_close:58.29,vix:22.68},
  {date:"2025-05-05",open:428.65,high:435.22,low:427.9,close:431.92,volume:20136100,gold_close:3311.3,oil_close:57.13,vix:23.64},
  {date:"2025-05-06",open:427.99,high:433.47,low:426.97,close:429.09,volume:15104200,gold_close:3411.4,oil_close:59.09,vix:24.76},
  {date:"2025-05-07",open:429.61,high:433.85,low:426.91,close:429.13,volume:23295300,gold_close:3381.4,oil_close:58.07,vix:23.55},
  {date:"2025-05-08",open:433.66,high:439.35,low:431.42,close:433.9,volume:23491300,gold_close:3296.6,oil_close:59.91,vix:22.48},
  {date:"2025-05-09",open:435.71,high:436.45,low:431.63,close:434.46,volume:15324200,gold_close:3335.4,oil_close:61.02,vix:21.9},
  {date:"2025-05-12",open:441.6,high:444.99,low:435.5,close:444.88,volume:22821900,gold_close:3220.0,oil_close:61.95,vix:18.39},
  {date:"2025-05-13",open:443.42,high:446.28,low:441.02,close:444.76,volume:23618800,gold_close:3240.3,oil_close:63.67,vix:18.22},
  {date:"2025-05-14",open:443.77,high:449.48,low:443.77,close:448.53,volume:19902800,gold_close:3181.4,oil_close:63.15,vix:18.62},
  {date:"2025-05-15",open:447.2,high:452.58,low:446.86,close:449.54,volume:21992300,gold_close:3220.7,oil_close:61.62,vix:17.83},
  {date:"2025-05-16",open:448.47,high:450.76,low:445.17,close:450.67,volume:23849800,gold_close:3182.0,oil_close:62.49,vix:17.24},
  {date:"2025-05-19",open:447.31,high:455.95,low:447.23,close:455.23,volume:21336500,gold_close:3228.9,oil_close:62.69,vix:18.14},
  {date:"2025-05-20",open:451.98,high:454.71,low:450.72,close:454.54,volume:15441800,gold_close:3280.3,oil_close:62.56,vix:18.09},
  {date:"2025-05-21",open:450.97,high:454.15,low:448.23,close:448.98,volume:19216900,gold_close:3309.3,oil_close:61.57,vix:20.87},
  {date:"2025-05-22",open:451.34,high:456.6,low:450.3,close:451.26,volume:18025600,gold_close:3292.3,oil_close:61.2,vix:20.28},
  {date:"2025-05-23",open:446.41,high:450.09,low:445.35,close:446.61,volume:16883500,gold_close:3363.6,oil_close:61.53,vix:22.29},
  {date:"2025-05-27",open:452.86,high:457.3,low:452.51,close:457.04,volume:20974300,gold_close:3299.1,oil_close:60.89,vix:18.96},
  {date:"2025-05-28",open:457.57,high:458.85,low:453.31,close:453.74,volume:17086300,gold_close:3293.6,oil_close:61.84,vix:19.31},
  {date:"2025-05-29",open:457.89,high:458.06,low:451.7,close:455.05,volume:13974800,gold_close:3317.1,oil_close:60.94,vix:19.18},
  {date:"2025-05-30",open:456.08,high:458.02,low:451.93,close:456.71,volume:34770500,gold_close:3288.9,oil_close:60.79,vix:18.57},
  {date:"2025-06-02",open:453.52,high:458.45,low:453.27,close:458.31,volume:16626500,gold_close:3370.6,oil_close:62.52,vix:18.36},
  {date:"2025-06-03",open:457.81,high:460.46,low:457.21,close:459.3,volume:15743800,gold_close:3350.2,oil_close:63.41,vix:17.69},
  {date:"2025-06-04",open:460.32,high:462.0,low:459.35,close:460.19,volume:14162700,gold_close:3373.5,oil_close:62.85,vix:17.61},
  {date:"2025-06-05",open:461.28,high:465.93,low:460.35,close:463.97,volume:20131700,gold_close:3350.7,oil_close:63.37,vix:18.48},
  {date:"2025-06-06",open:466.36,high:469.59,low:465.07,close:466.65,volume:15285600,gold_close:3322.7,oil_close:64.58,vix:16.77},
  {date:"2025-06-09",open:465.98,high:469.68,low:464.91,close:469.0,volume:16469900,gold_close:3332.1,oil_close:65.29,vix:17.16},
  {date:"2025-06-10",open:467.46,high:469.05,low:463.26,close:467.19,volume:15375900,gold_close:3320.9,oil_close:64.98,vix:16.95},
  {date:"2025-06-11",open:466.3,high:471.7,low:465.94,close:468.87,volume:16399200,gold_close:3321.3,oil_close:68.15,vix:17.26},
  {date:"2025-06-12",open:471.26,high:476.61,low:469.77,close:475.08,volume:18950600,gold_close:3380.9,oil_close:68.04,vix:18.02},
  {date:"2025-06-13",open:472.63,high:475.38,low:469.01,close:471.2,volume:16814500,gold_close:3431.2,oil_close:72.98,vix:20.82},
  {date:"2025-06-16",open:471.44,high:476.88,low:471.24,close:475.34,volume:15626100,gold_close:3396.4,oil_close:71.77,vix:19.11},
  {date:"2025-06-17",open:471.63,high:474.95,low:470.32,close:474.25,volume:15414100,gold_close:3386.6,oil_close:74.84,vix:21.6},
  {date:"2025-06-18",open:474.21,high:477.19,low:470.7,close:476.43,volume:17526500,gold_close:3389.8,oil_close:75.14,vix:20.14},
  {date:"2025-06-20",open:478.41,high:479.63,low:473.09,close:473.62,volume:37576200,gold_close:3368.1,oil_close:74.93,vix:20.62},
  {date:"2025-06-23",open:474.42,high:483.88,low:468.77,close:482.15,volume:24864000,gold_close:3377.7,oil_close:68.51,vix:19.83},
  {date:"2025-06-24",open:485.08,high:487.95,low:482.94,close:486.23,volume:22305600,gold_close:3317.4,oil_close:64.37,vix:17.48},
  {date:"2025-06-25",open:488.14,high:490.64,low:485.51,close:488.37,volume:17495100,gold_close:3327.1,oil_close:64.92,vix:16.76},
  {date:"2025-06-26",open:489.07,high:494.09,low:488.9,close:493.51,volume:21578900,gold_close:3333.5,oil_close:65.24,vix:16.59},
  {date:"2025-06-27",open:493.61,high:495.34,low:489.12,close:492.01,volume:34539200,gold_close:3273.7,oil_close:65.52,vix:16.32},
  {date:"2025-06-30",open:493.1,high:496.79,low:491.4,close:493.47,volume:28369000,gold_close:3294.4,oil_close:65.11,vix:16.73},
  {date:"2025-07-01",open:492.54,high:494.1,low:487.09,close:488.15,volume:19945400,gold_close:3336.7,oil_close:65.45,vix:16.83},
  {date:"2025-07-02",open:486.11,high:489.59,low:484.83,close:487.2,volume:16319600,gold_close:3348.0,oil_close:67.45,vix:16.64},
  {date:"2025-07-03",open:489.9,high:496.17,low:489.53,close:494.89,volume:13984800,gold_close:3331.6,oil_close:67.0,vix:16.38},
  {date:"2025-07-07",open:493.44,high:494.8,low:491.31,close:493.78,volume:13981600,gold_close:3332.2,oil_close:67.93,vix:17.79},
  {date:"2025-07-08",open:493.3,high:494.25,low:490.19,close:492.68,volume:11846600,gold_close:3307.0,oil_close:68.33,vix:16.81},
  {date:"2025-07-09",open:496.34,high:502.76,low:495.78,close:499.52,volume:18659500,gold_close:3311.6,oil_close:68.38,vix:15.94},
  {date:"2025-07-10",open:499.06,high:500.44,low:493.81,close:497.51,volume:16492100,gold_close:3317.4,oil_close:66.57,vix:15.78},
  {date:"2025-07-11",open:494.52,high:501.03,low:493.86,close:499.33,volume:16459500,gold_close:3356.0,oil_close:68.45,vix:16.4},
  {date:"2025-07-14",open:497.55,high:499.98,low:497.06,close:499.03,volume:12058800,gold_close:3351.5,oil_close:66.98,vix:17.2},
  {date:"2025-07-15",open:499.03,high:504.27,low:498.81,close:501.81,volume:14927200,gold_close:3329.8,oil_close:66.52,vix:17.38},
  {date:"2025-07-16",open:501.18,high:502.7,low:497.91,close:501.61,volume:15154400,gold_close:3352.5,oil_close:66.38,vix:17.16},
  {date:"2025-07-17",open:501.67,high:509.3,low:501.61,close:507.65,volume:17503100,gold_close:3340.1,oil_close:67.54,vix:16.52},
  {date:"2025-07-18",open:510.4,high:510.56,low:503.41,close:506.01,volume:21209700,gold_close:3353.0,oil_close:67.34,vix:16.41},
  {date:"2025-07-21",open:502.69,high:508.03,low:501.54,close:506.02,volume:14066800,gold_close:3401.9,oil_close:67.2,vix:16.65},
  {date:"2025-07-22",open:506.92,high:507.15,low:501.27,close:501.27,volume:13868600,gold_close:3439.2,oil_close:66.21,vix:16.5},
  {date:"2025-07-23",open:502.73,high:502.77,low:496.73,close:501.86,volume:16396600,gold_close:3394.1,oil_close:65.25,vix:15.37},
  {date:"2025-07-24",open:504.74,high:509.6,low:503.28,close:506.83,volume:16107000,gold_close:3371.0,oil_close:66.03,vix:15.39},
  {date:"2025-07-25",open:508.41,high:514.18,low:506.32,close:509.64,volume:19125700,gold_close:3334.0,oil_close:65.16,vix:14.93},
  {date:"2025-07-28",open:510.01,high:510.92,low:506.08,close:508.44,volume:14308000,gold_close:3309.1,oil_close:66.71,vix:15.03},
  {date:"2025-07-29",open:511.44,high:513.52,low:507.51,close:508.51,volume:16469200,gold_close:3323.4,oil_close:69.21,vix:15.98},
  {date:"2025-07-30",open:511.09,high:511.86,low:505.4,close:509.17,volume:26380400,gold_close:3295.8,oil_close:70.0,vix:15.48},
  {date:"2025-07-31",open:550.83,high:551.05,low:527.69,close:529.27,volume:51617300,gold_close:3293.2,oil_close:69.26,vix:16.72},
  {date:"2025-08-01",open:530.76,high:531.55,low:516.73,close:519.96,volume:28977600,gold_close:3347.7,oil_close:67.33,vix:20.38},
  {date:"2025-08-04",open:524.08,high:533.98,low:523.94,close:531.4,volume:25349000,gold_close:3374.4,oil_close:66.29,vix:17.52},
  {date:"2025-08-05",open:532.92,high:533.04,low:523.06,close:523.57,volume:19171600,gold_close:3381.9,oil_close:65.16,vix:17.85},
  {date:"2025-08-06",open:526.69,high:527.49,low:519.88,close:520.78,volume:21355700,gold_close:3380.0,oil_close:64.35,vix:16.77},
  {date:"2025-08-07",open:522.63,high:523.91,low:513.45,close:516.71,volume:16079100,gold_close:3400.3,oil_close:63.88,vix:16.57},
  {date:"2025-08-08",open:518.46,high:520.5,low:515.29,close:517.9,volume:15531000,gold_close:3439.1,oil_close:63.88,vix:15.15},
  {date:"2025-08-11",open:518.16,high:523.41,low:515.6,close:517.64,volume:20194400,gold_close:3353.1,oil_close:63.96,vix:16.25},
  {date:"2025-08-12",open:519.6,high:526.77,low:518.56,close:525.05,volume:18667000,gold_close:3348.9,oil_close:63.17,vix:14.73},
  {date:"2025-08-13",open:527.89,high:528.48,low:515.25,close:516.45,volume:19619200,gold_close:3358.7,oil_close:62.65,vix:14.49},
  {date:"2025-08-14",open:518.42,high:521.78,low:516.02,close:518.34,volume:20269100,gold_close:3335.2,oil_close:63.96,vix:14.83},
  {date:"2025-08-15",open:518.63,high:521.93,low:514.97,close:516.05,volume:25213300,gold_close:3336.0,oil_close:62.8,vix:15.09},
  {date:"2025-08-18",open:517.46,high:518.68,low:509.95,close:513.0,volume:23760600,gold_close:3331.7,oil_close:63.42,vix:14.99},
  {date:"2025-08-19",open:510.92,high:511.08,low:504.52,close:505.73,volume:21481000,gold_close:3313.4,oil_close:62.35,vix:15.57},
  {date:"2025-08-20",open:505.83,high:506.95,low:500.44,close:501.71,volume:27723000,gold_close:3343.4,oil_close:63.21,vix:15.69},
  {date:"2025-08-21",open:500.52,high:504.44,low:499.56,close:501.07,volume:18443300,gold_close:3336.9,oil_close:63.52,vix:16.6},
  {date:"2025-08-22",open:501.08,high:507.52,low:499.25,close:504.04,volume:24324200,gold_close:3374.4,oil_close:63.66,vix:14.22},
  {date:"2025-08-25",open:503.44,high:504.99,low:500.95,close:501.09,volume:21638600,gold_close:3373.8,oil_close:64.8,vix:14.79},
  {date:"2025-08-26",open:501.19,high:501.8,low:495.37,close:498.88,volume:30835700,gold_close:3388.6,oil_close:63.25,vix:14.62},
  {date:"2025-08-27",open:498.84,high:504.1,low:496.75,close:503.55,volume:17277900,gold_close:3404.6,oil_close:64.15,vix:14.85},
  {date:"2025-08-28",open:503.9,high:507.87,low:502.32,close:506.43,volume:18015600,gold_close:3431.8,oil_close:64.6,vix:14.43},
  {date:"2025-08-29",open:505.46,high:506.39,low:501.32,close:503.5,volume:20961600,gold_close:3473.7,oil_close:64.01,vix:15.36},
  {date:"2025-09-02",open:497.32,high:502.82,low:493.68,close:501.94,volume:18128000,gold_close:3549.4,oil_close:65.59,vix:17.17},
  {date:"2025-09-03",open:500.62,high:504.59,low:499.16,close:502.17,volume:16345100,gold_close:3593.2,oil_close:63.97,vix:16.35},
  {date:"2025-09-04",open:501.13,high:504.95,low:499.98,close:504.77,volume:15509500,gold_close:3565.8,oil_close:63.48,vix:15.3},
  {date:"2025-09-05",open:505.87,high:508.75,low:489.27,close:491.88,volume:31994800,gold_close:3613.2,oil_close:61.87,vix:15.18},
  {date:"2025-09-08",open:494.98,high:498.05,low:491.91,close:495.06,volume:16771000,gold_close:3638.1,oil_close:62.26,vix:15.11},
  {date:"2025-09-09",open:498.27,high:499.09,low:494.57,close:495.27,volume:14410500,gold_close:3643.3,oil_close:62.63,vix:15.04},
  {date:"2025-09-10",open:499.81,high:500.06,low:493.59,close:497.22,volume:21611800,gold_close:3643.6,oil_close:63.67,vix:15.35},
  {date:"2025-09-11",open:499.09,high:500.0,low:494.75,close:497.86,volume:18881600,gold_close:3636.9,oil_close:62.37,vix:14.71},
  {date:"2025-09-12",open:503.46,high:509.32,low:500.68,close:506.69,volume:23624900,gold_close:3649.4,oil_close:62.69,vix:14.76},
  {date:"2025-09-15",open:505.59,high:512.23,low:503.81,close:512.12,volume:17143800,gold_close:3682.2,oil_close:63.3,vix:15.69},
  {date:"2025-09-16",open:513.63,high:513.97,low:505.4,close:505.84,volume:19711900,gold_close:3688.9,oil_close:64.52,vix:16.36},
  {date:"2025-09-17",open:507.41,high:508.07,low:502.75,close:506.81,volume:15816600,gold_close:3681.8,oil_close:64.05,vix:15.72},
  {date:"2025-09-18",open:508.27,high:509.84,low:504.47,close:505.25,volume:18913700,gold_close:3643.7,oil_close:63.57,vix:15.7},
  {date:"2025-09-19",open:507.35,high:516.03,low:507.1,close:514.67,volume:52474100,gold_close:3671.5,oil_close:62.68,vix:15.45},
  {date:"2025-09-22",open:512.35,high:514.48,low:509.31,close:511.21,volume:20009300,gold_close:3740.7,oil_close:62.64,vix:16.1},
  {date:"2025-09-23",open:510.57,high:511.35,low:504.12,close:506.03,volume:19799600,gold_close:3780.6,oil_close:63.41,vix:16.64},
  {date:"2025-09-24",open:507.17,high:509.25,low:503.73,close:506.94,volume:13533700,gold_close:3732.1,oil_close:64.99,vix:16.18},
  {date:"2025-09-25",open:505.1,high:506.8,low:501.86,close:503.84,volume:15786500,gold_close:3736.9,oil_close:64.98,vix:16.74},
  {date:"2025-09-26",open:506.85,high:510.71,low:503.43,close:508.24,volume:16213100,gold_close:3775.3,oil_close:65.72,vix:15.29},
  {date:"2025-09-29",open:508.28,high:513.6,low:505.68,close:511.36,volume:17617800,gold_close:3820.9,oil_close:63.45,vix:16.12},
  {date:"2025-09-30",open:510.01,high:514.9,low:506.45,close:514.69,volume:19728200,gold_close:3840.8,oil_close:62.37,vix:16.28},
  {date:"2025-10-01",open:511.56,high:517.23,low:508.47,close:516.44,volume:22632300,gold_close:3867.5,oil_close:61.78,vix:16.29},
  {date:"2025-10-02",open:514.38,high:518.32,low:507.47,close:512.49,volume:21222900,gold_close:3839.7,oil_close:60.48,vix:16.63},
  {date:"2025-10-03",open:513.85,high:517.21,low:511.76,close:514.09,volume:15112300,gold_close:3880.8,oil_close:60.88,vix:16.65},
  {date:"2025-10-06",open:515.35,high:527.69,low:514.94,close:525.24,volume:21388600,gold_close:3948.5,oil_close:61.69,vix:16.37},
  {date:"2025-10-07",open:524.97,high:526.47,low:518.16,close:520.68,volume:14615200,gold_close:3976.6,oil_close:61.73,vix:17.24},
  {date:"2025-10-08",open:519.99,high:523.63,low:519.8,close:521.55,volume:13363400,gold_close:4043.3,oil_close:62.55,vix:16.3},
  {date:"2025-10-09",open:519.05,high:521.03,low:514.14,close:519.11,volume:18343600,gold_close:3946.3,oil_close:61.51,vix:16.43},
  {date:"2025-10-10",open:516.37,high:520.28,low:506.42,close:507.74,volume:24133800,gold_close:3975.9,oil_close:58.9,vix:21.66},
  {date:"2025-10-13",open:513.16,high:513.16,low:508.46,close:510.81,volume:14284200,gold_close:4108.6,oil_close:59.49,vix:19.03},
  {date:"2025-10-14",open:507.02,high:512.04,low:502.82,close:510.34,volume:14684300,gold_close:4138.7,oil_close:58.7,vix:20.81},
  {date:"2025-10-15",open:511.72,high:513.94,low:506.79,close:510.2,volume:14694700,gold_close:4176.9,oil_close:58.27,vix:20.64},
  {date:"2025-10-16",open:509.35,high:513.6,low:504.93,close:508.39,volume:15559600,gold_close:4280.2,oil_close:57.46,vix:25.31},
  {date:"2025-10-17",open:505.84,high:512.24,low:504.12,close:510.35,volume:19867800,gold_close:4189.9,oil_close:57.54,vix:20.78},
  {date:"2025-10-20",open:511.37,high:515.44,low:510.2,close:513.54,volume:14665600,gold_close:4336.4,oil_close:57.52,vix:18.23},
  {date:"2025-10-21",open:514.24,high:515.43,low:509.81,close:514.4,volume:15586200,gold_close:4087.7,oil_close:57.82,vix:17.87},
  {date:"2025-10-22",open:517.87,high:521.92,low:514.45,close:517.26,volume:18962700,gold_close:4044.4,oil_close:58.5,vix:18.6},
  {date:"2025-10-23",open:519.17,high:520.65,low:515.35,close:517.28,volume:14023500,gold_close:4125.5,oil_close:61.79,vix:17.3},
  {date:"2025-10-24",open:519.5,high:522.04,low:517.43,close:520.31,volume:15532400,gold_close:4118.4,oil_close:61.5,vix:16.37},
  {date:"2025-10-27",open:528.43,high:531.22,low:525.68,close:528.17,volume:18734700,gold_close:4001.9,oil_close:61.31,vix:15.79},
  {date:"2025-10-28",open:546.54,high:550.24,low:537.37,close:538.66,volume:29986700,gold_close:3966.2,oil_close:60.15,vix:16.42},
  {date:"2025-10-29",open:541.51,high:542.83,low:533.35,close:538.14,volume:36023000,gold_close:3983.7,oil_close:60.48,vix:16.92},
  {date:"2025-10-30",open:527.14,high:531.6,low:518.83,close:522.45,volume:41023100,gold_close:4001.3,oil_close:60.57,vix:16.91},
  {date:"2025-10-31",open:525.55,high:525.99,low:511.86,close:514.55,volume:34006400,gold_close:3982.2,oil_close:60.98,vix:17.44},
  {date:"2025-11-03",open:516.54,high:521.66,low:511.35,close:513.78,volume:22374700,gold_close:4000.3,oil_close:61.05,vix:17.17},
  {date:"2025-11-04",open:508.54,high:512.31,low:504.64,close:511.09,volume:20958700,gold_close:3947.7,oil_close:60.56,vix:19.0},
  {date:"2025-11-05",open:510.07,high:511.59,low:503.39,close:503.97,volume:23024300,gold_close:3980.3,oil_close:59.6,vix:18.01},
  {date:"2025-11-06",open:502.48,high:502.52,low:492.69,close:493.97,volume:27406500,gold_close:3979.9,oil_close:59.43,vix:19.5},
  {date:"2025-11-07",open:493.82,high:496.24,low:490.15,close:493.69,volume:24019800,gold_close:3999.4,oil_close:59.75,vix:19.08},
  {date:"2025-11-10",open:496.89,high:503.66,low:495.66,close:502.82,volume:26101500,gold_close:4111.8,oil_close:60.13,vix:17.6},
  {date:"2025-11-11",open:501.62,high:506.39,low:499.19,close:505.48,volume:17980000,gold_close:4106.8,oil_close:61.04,vix:17.28},
  {date:"2025-11-12",open:506.15,high:508.45,low:495.98,close:507.92,volume:26574900,gold_close:4204.4,oil_close:58.49,vix:17.51},
  {date:"2025-11-13",open:507.1,high:510.27,low:498.14,close:500.12,volume:25273100,gold_close:4186.9,oil_close:58.69,vix:20.0},
  {date:"2025-11-14",open:495.09,high:508.38,low:494.31,close:506.97,volume:28505700,gold_close:4087.6,oil_close:60.09,vix:19.83},
  {date:"2025-11-17",open:505.25,high:508.9,low:501.73,close:504.3,volume:19092800,gold_close:4068.3,oil_close:59.91,vix:22.38},
  {date:"2025-11-18",open:492.25,high:499.81,low:483.72,close:490.68,volume:33815100,gold_close:4061.3,oil_close:60.74,vix:24.69},
  {date:"2025-11-19",open:487.02,high:492.07,low:479.79,close:484.05,volume:23245300,gold_close:4077.7,oil_close:59.44,vix:23.66},
  {date:"2025-11-20",open:490.53,high:491.38,low:473.39,close:476.31,volume:26802500,gold_close:4056.5,oil_close:59.14,vix:26.42},
  {date:"2025-11-21",open:476.38,high:476.8,low:466.19,close:470.03,volume:31769200,gold_close:4076.7,oil_close:58.06,vix:23.43},
  {date:"2025-11-24",open:472.89,high:474.79,low:465.95,close:471.9,volume:34421000,gold_close:4091.9,oil_close:58.84,vix:20.52},
  {date:"2025-11-25",open:471.97,high:477.03,low:462.83,close:474.88,volume:28019800,gold_close:4139.2,oil_close:57.95,vix:18.56},
  {date:"2025-11-26",open:484.15,high:486.15,low:479.07,close:483.35,volume:25709100,gold_close:4165.2,oil_close:58.65,vix:17.19},
  {date:"2025-11-28",open:485.44,high:490.45,low:484.49,close:489.83,volume:14386700,gold_close:4218.3,oil_close:58.55,vix:16.35},
  {date:"2025-12-01",open:486.27,high:487.69,low:482.5,close:484.58,volume:23964000,gold_close:4239.3,oil_close:59.32,vix:17.24},
  {date:"2025-12-02",open:484.56,high:491.31,low:484.16,close:487.83,volume:19562700,gold_close:4186.6,oil_close:58.64,vix:16.59},
  {date:"2025-12-03",open:474.21,high:482.09,low:473.09,close:475.61,volume:34615100,gold_close:4199.3,oil_close:58.95,vix:16.08},
  {date:"2025-12-04",open:477.63,high:479.19,low:474.38,close:478.71,volume:22318200,gold_close:4211.8,oil_close:59.67,vix:15.78},
  {date:"2025-12-05",open:480.38,high:481.26,low:476.76,close:481.02,volume:22608700,gold_close:4212.9,oil_close:60.08,vix:15.41},
  {date:"2025-12-08",open:482.74,high:490.12,low:482.23,close:488.84,volume:21965900,gold_close:4187.2,oil_close:58.88,vix:16.66},
  {date:"2025-12-09",open:486.93,high:489.94,low:486.33,close:489.84,volume:14696100,gold_close:4206.7,oil_close:58.25,vix:16.93},
  {date:"2025-12-10",open:481.88,high:482.1,low:472.97,close:476.44,volume:35756200,gold_close:4196.4,oil_close:58.46,vix:15.77},
  {date:"2025-12-11",open:474.52,high:483.88,low:473.75,close:481.33,volume:24669200,gold_close:4285.5,oil_close:57.6,vix:14.85},
  {date:"2025-12-12",open:477.69,high:480.31,low:474.23,close:476.41,volume:21248100,gold_close:4300.1,oil_close:57.44,vix:15.74},
  {date:"2025-12-15",open:477.97,high:478.59,low:470.43,close:472.71,volume:23727700,gold_close:4306.7,oil_close:56.82,vix:16.5},
  {date:"2025-12-16",open:469.82,high:475.77,low:468.79,close:474.28,volume:20705600,gold_close:4304.5,oil_close:55.27,vix:16.48},
  {date:"2025-12-17",open:474.8,high:477.87,low:472.89,close:474.01,volume:24527200,gold_close:4347.5,oil_close:55.94,vix:17.62},
  {date:"2025-12-18",open:476.07,high:487.43,low:475.77,close:481.83,volume:28573500,gold_close:4339.5,oil_close:56.15,vix:16.87},
  {date:"2025-12-19",open:485.2,high:485.69,low:480.35,close:483.77,volume:70836100,gold_close:4361.4,oil_close:56.66,vix:14.91},
  {date:"2025-12-22",open:483.96,high:486.56,low:480.55,close:482.77,volume:16963000,gold_close:4444.6,oil_close:58.01,vix:14.08},
  {date:"2025-12-23",open:482.83,high:485.67,low:482.59,close:484.69,volume:14683600,gold_close:4482.8,oil_close:58.38,vix:14.0},
  {date:"2025-12-24",open:483.53,high:486.99,low:482.68,close:485.86,volume:5855900,gold_close:4480.6,oil_close:58.35,vix:13.47},
  {date:"2025-12-26",open:484.55,high:485.96,low:483.81,close:485.55,volume:8842200,gold_close:4529.1,oil_close:56.74,vix:13.6},
  {date:"2025-12-29",open:482.71,high:486.18,low:482.03,close:484.94,volume:10893400,gold_close:4325.1,oil_close:58.08,vix:14.2},
  {date:"2025-12-30",open:483.78,high:487.51,low:483.35,close:485.32,volume:13944500,gold_close:4370.1,oil_close:57.95,vix:14.33},
  {date:"2025-12-31",open:485.68,high:485.98,low:481.16,close:481.48,volume:15601600,gold_close:4325.6,oil_close:57.42,vix:14.95},
  {date:"2026-01-02",open:482.24,high:482.51,low:468.08,close:470.84,volume:25571600,gold_close:4314.4,oil_close:57.32,vix:14.51},
  {date:"2026-01-05",open:471.96,high:473.96,low:467.42,close:470.75,volume:25250300,gold_close:4436.9,oil_close:58.32,vix:14.9},
  {date:"2026-01-06",open:471.7,high:476.62,low:467.67,close:476.39,volume:23037700,gold_close:4482.2,oil_close:57.13,vix:14.75},
  {date:"2026-01-07",open:477.63,high:487.53,low:475.83,close:481.33,volume:25564200,gold_close:4449.3,oil_close:55.99,vix:15.38},
  {date:"2026-01-08",open:479.11,high:480.52,low:473.75,close:475.99,volume:18162600,gold_close:4449.7,oil_close:57.76,vix:15.45},
  {date:"2026-01-09",open:471.96,high:477.69,low:470.11,close:477.16,volume:18491000,gold_close:4490.3,oil_close:59.12,vix:14.49},
  {date:"2026-01-12",open:474.56,high:478.86,low:473.57,close:475.06,volume:23519900,gold_close:4604.3,oil_close:59.5,vix:15.12},
  {date:"2026-01-13",open:472.58,high:473.67,low:463.88,close:468.58,volume:28545800,gold_close:4589.2,oil_close:61.15,vix:15.98},
  {date:"2026-01-14",open:464.39,high:466.12,low:455.14,close:457.34,volume:28184300,gold_close:4626.3,oil_close:62.02,vix:16.75},
  {date:"2026-01-15",open:462.06,high:462.19,low:453.88,close:454.64,volume:23225800,gold_close:4616.3,oil_close:59.19,vix:15.84},
  {date:"2026-01-16",open:455.8,high:461.14,low:454.46,close:457.82,volume:34246700,gold_close:4588.4,oil_close:59.44,vix:15.86},
  {date:"2026-01-20",open:449.22,high:454.77,low:447.29,close:452.5,volume:26130000,gold_close:4759.6,oil_close:60.34,vix:20.09},
  {date:"2026-01-21",open:450.59,high:450.68,low:436.74,close:442.14,volume:37980500,gold_close:4831.8,oil_close:60.62,vix:16.9},
  {date:"2026-01-22",open:445.64,high:450.83,low:442.73,close:449.14,volume:25349400,gold_close:4908.8,oil_close:59.36,vix:15.64},
  {date:"2026-01-23",open:449.87,high:469.01,low:448.53,close:463.88,volume:38000200,gold_close:4976.2,oil_close:61.07,vix:16.09},
  {date:"2026-01-26",open:463.25,high:472.15,low:459.95,close:468.19,volume:29291200,gold_close:5079.7,oil_close:60.63,vix:16.15},
  {date:"2026-01-27",open:471.6,high:480.73,low:471.06,close:478.45,volume:29213900,gold_close:5079.9,oil_close:62.39,vix:16.35},
  {date:"2026-01-28",open:481.07,high:481.6,low:475.88,close:479.49,volume:36875400,gold_close:5301.6,oil_close:63.21,vix:16.35},
  {date:"2026-01-29",open:438.04,high:440.54,low:419.15,close:431.58,volume:128855300,gold_close:5318.4,oil_close:65.42,vix:16.88},
  {date:"2026-01-30",open:437.22,high:437.65,low:424.56,close:428.38,volume:58566800,gold_close:4713.9,oil_close:65.21,vix:17.44},
  {date:"2026-02-02",open:428.33,high:428.83,low:420.38,close:421.49,volume:42219900,gold_close:4622.5,oil_close:62.14,vix:16.34},
  {date:"2026-02-03",open:420.14,high:420.18,low:406.75,close:409.39,volume:61424100,gold_close:4903.7,oil_close:63.21,vix:18.0},
  {date:"2026-02-04",open:409.18,high:417.94,low:407.43,close:412.35,volume:45012400,gold_close:4920.4,oil_close:65.14,vix:18.64},
  {date:"2026-02-05",open:405.63,high:406.49,low:390.58,close:391.92,volume:66289200,gold_close:4861.4,oil_close:63.29,vix:21.77},
  {date:"2026-02-06",open:397.4,high:400.01,low:391.18,close:399.36,volume:53515300,gold_close:4951.2,oil_close:63.55,vix:20.37},
  {date:"2026-02-09",open:403.06,high:413.05,low:399.09,close:411.77,volume:45480500,gold_close:5050.9,oil_close:64.36,vix:17.36},
  {date:"2026-02-10",open:417.76,high:421.8,low:410.87,close:411.44,volume:44857900,gold_close:5003.8,oil_close:63.96,vix:17.79},
  {date:"2026-02-11",open:414.33,high:414.61,low:399.23,close:402.58,volume:42491000,gold_close:5071.6,oil_close:64.63,vix:17.65},
  {date:"2026-02-12",open:403.2,high:404.4,low:396.25,close:400.06,volume:40802400,gold_close:4923.7,oil_close:62.84,vix:20.82},
  {date:"2026-02-13",open:402.66,high:403.74,low:396.29,close:399.54,volume:34091600,gold_close:5022.0,oil_close:62.89,vix:20.6},
  {date:"2026-02-17",open:397.45,high:398.74,low:392.78,close:395.1,volume:32078800,gold_close:4882.9,oil_close:62.33,vix:20.29},
  {date:"2026-02-18",open:396.36,high:400.78,low:394.56,close:397.83,volume:23223400,gold_close:4986.5,oil_close:65.19,vix:19.62},
  {date:"2026-02-19",open:399.82,high:403.56,low:395.81,close:397.6,volume:28234000,gold_close:4975.9,oil_close:66.43,vix:20.23},
  {date:"2026-02-20",open:395.25,high:399.26,low:394.31,close:396.37,volume:34015200,gold_close:5059.3,oil_close:66.39,vix:19.09},
  {date:"2026-02-23",open:394.15,high:394.51,low:382.27,close:383.64,volume:43238300,gold_close:5204.7,oil_close:66.31,vix:21.01},
  {date:"2026-02-24",open:383.31,high:388.52,low:380.89,close:388.16,volume:33884700,gold_close:5155.8,oil_close:65.63,vix:19.55},
  {date:"2026-02-25",open:389.69,high:400.6,low:389.32,close:399.73,volume:43625500,gold_close:5206.4,oil_close:65.42,vix:17.93},
  {date:"2026-02-26",open:403.84,high:406.61,low:397.88,close:400.85,volume:34405900,gold_close:5176.5,oil_close:65.21,vix:18.63},
  {date:"2026-02-27",open:390.04,high:395.96,low:389.04,close:391.89,volume:51367200,gold_close:5230.5,oil_close:67.02,vix:19.86},
  {date:"2026-03-02",open:392.01,high:400.32,low:389.79,close:397.69,volume:35474900,gold_close:5294.4,oil_close:71.23,vix:21.44},
  {date:"2026-03-03",open:392.29,high:405.82,low:391.82,close:403.06,volume:38199200,gold_close:5107.4,oil_close:74.56,vix:23.57},
  {date:"2026-03-04",open:400.4,high:410.14,low:399.44,close:404.32,volume:35808000,gold_close:5120.2,oil_close:74.66,vix:21.15},
  {date:"2026-03-05",open:403.55,high:410.72,low:403.53,close:409.79,volume:39001300,gold_close:5065.3,oil_close:81.01,vix:23.75},
  {date:"2026-03-06",open:408.32,high:412.16,low:407.63,close:408.08,volume:31123900,gold_close:5146.1,oil_close:90.9,vix:29.49},
  {date:"2026-03-09",open:404.04,high:409.32,low:402.63,close:408.53,volume:30131900,gold_close:5091.5,oil_close:94.77,vix:25.5},
  {date:"2026-03-10",open:409.14,high:409.31,low:402.06,close:404.88,volume:31706400,gold_close:5229.7,oil_close:83.45,vix:24.93},
  {date:"2026-03-11",open:404.69,high:408.13,low:400.72,close:404.0,volume:25512100,gold_close:5167.4,oil_close:87.25,vix:24.23},
  {date:"2026-03-12",open:403.76,high:405.24,low:400.84,close:400.99,volume:27263900,gold_close:5115.8,oil_close:95.73,vix:27.29},
  {date:"2026-03-13",open:400.13,high:403.93,low:393.4,close:394.7,volume:26848000,gold_close:5052.5,oil_close:98.71,vix:27.19},
  {date:"2026-03-16",open:397.21,high:399.76,low:393.94,close:399.09,volume:27733700,gold_close:4994.0,oil_close:93.5,vix:23.51},
  {date:"2026-03-17",open:399.4,high:403.53,low:396.89,close:398.55,volume:26228300,gold_close:5001.0,oil_close:96.21,vix:22.37},
  {date:"2026-03-18",open:396.27,high:397.14,low:390.15,close:390.94,volume:25908500,gold_close:4889.9,oil_close:96.32,vix:25.09},
  {date:"2026-03-19",open:389.26,high:391.64,low:386.22,close:388.18,volume:25138800,gold_close:4600.7,oil_close:96.14,vix:24.06},
  {date:"2026-03-20",open:385.95,high:386.16,low:379.3,close:381.04,volume:50853200,gold_close:4570.4,oil_close:98.32,vix:26.78},
  {date:"2026-03-23",open:383.07,high:386.37,low:380.86,close:382.17,volume:29680100,gold_close:4404.1,oil_close:88.13,vix:26.15},
  {date:"2026-03-24",open:381.53,high:381.64,low:371.05,close:371.93,volume:42733600,gold_close:4399.3,oil_close:92.35,vix:26.95},
  {date:"2026-03-25",open:376.11,high:376.25,low:368.83,close:370.24,volume:31181200,gold_close:4549.8,oil_close:90.32,vix:25.33},
  {date:"2026-03-26",open:370.02,high:373.91,low:364.4,close:365.18,volume:36836600,gold_close:4375.5,oil_close:94.48,vix:27.44},
  {date:"2026-03-27",open:361.12,high:361.67,low:355.74,close:356.0,volume:37883400,gold_close:4492.0,oil_close:99.64,vix:31.05},
  {date:"2026-03-30",open:361.12,high:364.57,low:355.51,close:358.18,volume:44797000,gold_close:4526.0,oil_close:102.88,vix:30.61},
  {date:"2026-03-31",open:363.76,high:372.09,low:362.29,close:369.37,volume:45244400,gold_close:4647.6,oil_close:101.38,vix:25.25},
  {date:"2026-04-01",open:372.68,high:373.18,low:367.4,close:368.57,volume:29417200,gold_close:4783.2,oil_close:100.12,vix:24.54},
  {date:"2026-04-02",open:366.42,high:372.83,low:363.36,close:372.65,volume:24099100,gold_close:4651.5,oil_close:111.54,vix:23.87},
  {date:"2026-04-06",open:372.68,high:372.92,low:368.7,close:372.07,volume:16146600,gold_close:4656.8,oil_close:112.41,vix:24.17},
  {date:"2026-04-07",open:369.54,high:371.65,low:365.77,close:371.49,volume:21443300,gold_close:4657.1,oil_close:112.95,vix:25.78},
  {date:"2026-04-08",open:384.15,high:384.17,low:370.61,close:373.52,volume:33064800,gold_close:4749.5,oil_close:94.41,vix:21.04},
  {date:"2026-04-09",open:371.69,high:372.69,low:366.26,close:372.26,volume:30435300,gold_close:4792.2,oil_close:97.87,vix:19.49},
  {date:"2026-04-10",open:372.17,high:374.83,low:369.23,close:370.07,volume:28111100,gold_close:4761.9,oil_close:96.57,vix:19.23},
  {date:"2026-04-13",open:372.8,high:383.71,low:370.22,close:383.54,volume:35745800,gold_close:4742.4,oil_close:99.08,vix:19.12},
  {date:"2026-04-14",open:387.08,high:393.84,low:385.68,close:392.26,volume:37504500,gold_close:4825.0,oil_close:91.28,vix:18.36},
  {date:"2026-04-15",open:397.14,high:413.47,low:395.87,close:410.33,volume:45063400,gold_close:4800.0,oil_close:91.29,vix:18.17},
  {date:"2026-04-16",open:418.95,high:419.91,low:411.25,close:419.35,volume:41642400,gold_close:4785.4,oil_close:94.69,vix:17.94},
  {date:"2026-04-17",open:423.9,high:430.65,low:419.78,close:421.88,volume:48568200,gold_close:4857.6,oil_close:83.85,vix:17.48},
  {date:"2026-04-20",open:420.24,high:422.42,low:415.4,close:417.17,volume:27582200,gold_close:4806.6,oil_close:89.61,vix:18.87},
  {date:"2026-04-21",open:419.33,high:426.26,low:416.3,close:423.24,volume:32048500,gold_close:4698.4,oil_close:92.13,vix:19.5},
  {date:"2026-04-22",open:425.27,high:432.76,low:422.75,close:431.98,volume:29378200,gold_close:4732.5,oil_close:92.96,vix:18.92},
  {date:"2026-04-23",open:418.98,high:422.74,low:410.52,close:414.85,volume:38308000,gold_close:4705.1,oil_close:95.85,vix:19.31},
  {date:"2026-04-24",open:416.07,high:424.03,low:414.9,close:423.7,volume:27457400,gold_close:4722.3,oil_close:94.4,vix:18.71},
  {date:"2026-04-27",open:421.47,high:426.19,low:416.17,close:423.9,volume:30867300,gold_close:4675.4,oil_close:96.37,vix:18.02},
  {date:"2026-04-28",open:423.65,high:428.99,low:420.99,close:428.32,volume:30438100,gold_close:4591.5,oil_close:99.93,vix:17.83},
  {date:"2026-04-29",open:423.66,high:425.9,low:419.38,close:423.54,volume:38288300,gold_close:4545.2,oil_close:106.88,vix:18.81},
  {date:"2026-04-30",open:409.92,high:413.52,low:397.15,close:406.9,volume:70909400,gold_close:4614.7,oil_close:105.07,vix:16.89},
  {date:"2026-05-01",open:411.91,high:416.21,low:409.55,close:413.54,volume:31372400,gold_close:4629.9,oil_close:101.94,vix:16.99},
  {date:"2026-05-04",open:410.65,high:419.87,low:409.91,close:412.73,volume:28066500,gold_close:4519.5,oil_close:106.42,vix:18.29},
  {date:"2026-05-05",open:414.42,high:415.88,low:407.92,close:410.49,volume:25700900,gold_close:4555.8,oil_close:102.27,vix:17.38},
  {date:"2026-05-06",open:407.12,high:417.52,low:404.23,close:413.07,volume:30285900,gold_close:4681.9,oil_close:95.08,vix:17.39},
  {date:"2026-05-07",open:419.2,high:427.06,low:417.85,close:419.86,volume:34942400,gold_close:4699.8,oil_close:94.81,vix:17.08},
  {date:"2026-05-08",open:416.49,high:417.73,low:413.11,close:414.22,volume:33383800,gold_close:4720.4,oil_close:95.42,vix:17.19},
  {date:"2026-05-11",open:406.99,high:411.8,low:404.62,close:411.77,volume:35657900,gold_close:4718.7,oil_close:98.07,vix:18.38},
  {date:"2026-05-12",open:413.58,high:414.6,low:405.76,close:406.89,volume:38594200,gold_close:4677.6,oil_close:102.18,vix:17.99},
  {date:"2026-05-13",open:402.33,high:405.43,low:400.16,close:404.33,volume:29667100,gold_close:4697.7,oil_close:101.02,vix:17.87},
  {date:"2026-05-14",open:403.61,high:410.95,low:400.01,close:408.55,volume:27077500,gold_close:4678.1,oil_close:101.17,vix:17.26},
  {date:"2026-05-15",open:413.37,high:427.24,low:412.02,close:421.01,volume:50771200,gold_close:4555.8,oil_close:105.42,vix:18.43},
  {date:"2026-05-18",open:415.72,high:424.2,low:414.71,close:422.62,volume:32564100,gold_close:4552.5,oil_close:108.66,vix:17.82},
  {date:"2026-05-19",open:428.97,high:431.76,low:415.59,close:416.52,volume:33018700,gold_close:4506.3,oil_close:107.77,vix:18.06},
  {date:"2026-05-20",open:413.27,high:421.19,low:410.41,close:420.15,volume:27864000,gold_close:4531.3,oil_close:98.26,vix:17.44},
  {date:"2026-05-21",open:424.75,high:426.34,low:415.71,close:419.09,volume:31393500,gold_close:4539.8,oil_close:96.35,vix:16.76},
  {date:"2026-05-22",open:419.54,high:424.4,low:416.33,close:418.57,volume:22390300,gold_close:4521.0,oil_close:96.6,vix:16.7},
  {date:"2026-05-26",open:416.43,high:419.77,low:413.02,close:416.03,volume:30398000,gold_close:4500.4,oil_close:93.89,vix:17.01},
  {date:"2026-05-27",open:411.01,high:415.94,low:409.58,close:412.67,volume:28901500,gold_close:4447.5,oil_close:88.68,vix:16.29},
  {date:"2026-05-28",open:412.98,high:429.49,low:412.67,close:426.99,volume:47147800,gold_close:4499.3,oil_close:88.9,vix:15.74}
];

const FEATURE_IMPORTANCE = [
  { name: 'nvda_rel_strength',  pct: 0.0689 },
  { name: 'macd',               pct: 0.0599 },
  { name: 'amzn_volume_ratio',  pct: 0.0558 },
  { name: 'return_8w',          pct: 0.0538 },
  { name: 'amzn_return_1w',     pct: 0.0529 },
  { name: 'rolling_std_5',      pct: 0.0527 },
  { name: 'lag_return_2',       pct: 0.0525 },
  { name: 'nvda_lag_return_1',  pct: 0.0518 },
  { name: 'amzn_lag_return_1',  pct: 0.0507 },
  { name: 'return_4w',          pct: 0.0502 },
  { name: 'amzn_rel_strength',  pct: 0.0496 },
  { name: 'macd_hist',          pct: 0.0490 },
  { name: 'nvda_volume_ratio',  pct: 0.0483 },
  { name: 'nvda_return_1w',     pct: 0.0464 },
  { name: 'rsi_14',             pct: 0.0462 },
  { name: 'price_range_pct',    pct: 0.0445 },
  { name: 'lag_return_1',       pct: 0.0443 },
  { name: 'return_1w',          pct: 0.0438 },
  { name: 'macd_signal',        pct: 0.0414 },
  { name: 'volume_ratio',       pct: 0.0373 },
];

// ── Settings ───────────────────────────────────────────────────────────────────
const CURRENCY_SYMBOLS = { USD: '$', EUR: '€', GBP: '£', JPY: '¥' };
const FALLBACK_RATES = { USD: 1, EUR: 0.92, GBP: 0.79, JPY: 157 };
let exchangeRates = { ...FALLBACK_RATES };
let baseCloseUSD  = null;

async function fetchExchangeRates() {
  try {
    const res  = await fetch('https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data.rates?.EUR) {
      exchangeRates = { USD: 1, ...data.rates };
      console.log('Live exchange rates loaded:', exchangeRates);
    }
  } catch (e) {
    console.warn('Exchange rate fetch failed, using fallback rates:', e.message);
    exchangeRates = { ...FALLBACK_RATES };
  }
}

const I18N = {
  en: {
    settings: 'Settings', display: 'Display', currency: 'Currency',
    'currency-note': 'Display only — no live conversion',
    language: 'Language', charts: 'Charts', 'default-period': 'Default period',
    'chart-style': 'Chart style', area: 'Area', line: 'Line only',
    predictions: 'Predictions', 'show-conf-bar': 'Show confidence bar',
    'auto-refresh': 'Auto-refresh data', 'auto-refresh-note': 'Reload predictions every 15 min',
    'show-disclaimer': 'Show disclaimer',
    tomorrow: 'Next week', 'model-conf': 'Accuracy', 'ens-label': 'Model breakdown',
  },
  nl: {
    settings: 'Instellingen', display: 'Weergave', currency: 'Valuta',
    'currency-note': 'Alleen weergave — geen live conversie',
    language: 'Taal', charts: 'Grafieken', 'default-period': 'Standaard periode',
    'chart-style': 'Grafiekstijl', area: 'Vlak', line: 'Alleen lijn',
    predictions: 'Voorspellingen', 'show-conf-bar': 'Betrouwbaarheidsbalk tonen',
    'auto-refresh': 'Data automatisch verversen', 'auto-refresh-note': 'Herlaad voorspellingen elke 15 min',
    'show-disclaimer': 'Disclaimer tonen',
    tomorrow: 'Volgende week', 'model-conf': 'Nauwkeurigheid', 'ens-label': 'Model overzicht',
  },
  de: {
    settings: 'Einstellungen', display: 'Anzeige', currency: 'Währung',
    'currency-note': 'Nur Anzeige — keine Live-Konvertierung',
    language: 'Sprache', charts: 'Diagramme', 'default-period': 'Standardzeitraum',
    'chart-style': 'Diagrammstil', area: 'Fläche', line: 'Nur Linie',
    predictions: 'Vorhersagen', 'show-conf-bar': 'Konfidenzbalken anzeigen',
    'auto-refresh': 'Daten automatisch aktualisieren', 'auto-refresh-note': 'Vorhersagen alle 15 Min neu laden',
    'show-disclaimer': 'Haftungsausschluss anzeigen',
    tomorrow: 'Nächste Woche', 'model-conf': 'Genauigkeit', 'ens-label': 'Modell-Übersicht',
  },
  fr: {
    settings: 'Paramètres', display: 'Affichage', currency: 'Devise',
    'currency-note': 'Affichage uniquement — pas de conversion en direct',
    language: 'Langue', charts: 'Graphiques', 'default-period': 'Période par défaut',
    'chart-style': 'Style de graphique', area: 'Zone', line: 'Ligne seulement',
    predictions: 'Prédictions', 'show-conf-bar': 'Afficher la barre de confiance',
    'auto-refresh': 'Actualisation automatique', 'auto-refresh-note': 'Recharger les prédictions toutes les 15 min',
    'show-disclaimer': 'Afficher l\'avertissement',
    tomorrow: 'Semaine prochaine', 'model-conf': 'Précision', 'ens-label': 'Détail du modèle',
  },
  es: {
    settings: 'Configuración', display: 'Visualización', currency: 'Moneda',
    'currency-note': 'Solo visualización — sin conversión en vivo',
    language: 'Idioma', charts: 'Gráficos', 'default-period': 'Período predeterminado',
    'chart-style': 'Estilo de gráfico', area: 'Área', line: 'Solo línea',
    predictions: 'Predicciones', 'show-conf-bar': 'Mostrar barra de confianza',
    'auto-refresh': 'Actualización automática', 'auto-refresh-note': 'Recargar predicciones cada 15 min',
    'show-disclaimer': 'Mostrar descargo de responsabilidad',
    tomorrow: 'Próxima semana', 'model-conf': 'Precisión', 'ens-label': 'Desglose del modelo',
  },
};

const DEFAULT_SETTINGS = {
  currency: 'USD', language: 'en', defaultPeriod: '1M',
  chartStyle: 'area', showConfBar: true, autoRefresh: false, showDisclaimer: true,
};
let appSettings = { ...DEFAULT_SETTINGS };

function loadSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem('appSettings') || '{}');
    appSettings = { ...DEFAULT_SETTINGS, ...saved, currency: 'USD' };
  }
  catch { appSettings = { ...DEFAULT_SETTINGS }; }
}
function saveSettings() { localStorage.setItem('appSettings', JSON.stringify(appSettings)); }

function applyI18n() {
  const L = I18N[appSettings.language] || I18N.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (L[key]) el.textContent = L[key];
  });
  const confLabel = document.querySelector('.pred-conf-label');
  if (confLabel) confLabel.textContent = L['model-conf'];
  const ensLabel = document.querySelector('.ensemble-label');
  if (ensLabel) ensLabel.textContent = L['ens-label'];
}

function applySettings() {
  applyI18n();
  const sym  = CURRENCY_SYMBOLS[appSettings.currency] || '$';
  const rate = exchangeRates[appSettings.currency] || 1;
  const decimals = appSettings.currency === 'JPY' ? 0 : 2;
  const closeEl = document.getElementById('tile-close');
  if (closeEl && baseCloseUSD !== null) closeEl.textContent = `${sym}${(baseCloseUSD * rate).toFixed(decimals)}`;
  const confBg = document.querySelector('.conf-bar-bg');
  if (confBg) confBg.style.display = appSettings.showConfBar ? '' : 'none';
  const disclaimer = document.querySelector('.disclaimer-bar');
  if (disclaimer) disclaimer.style.display = appSettings.showDisclaimer ? '' : 'none';
  if (homeRenderData.length) drawHomeChart();
}

function syncSettingsUI() {
  const setActive = (id, val) => {
    document.getElementById(id)?.querySelectorAll('.btn-group-item')
      .forEach(b => b.classList.toggle('active', b.dataset.val === val));
  };
  setActive('setting-currency',    appSettings.currency);
  setActive('setting-period',      appSettings.defaultPeriod);
  setActive('setting-chart-style', appSettings.chartStyle);
  const langEl = document.getElementById('setting-language');
  if (langEl) langEl.value = appSettings.language;
  const cb = document.getElementById('setting-conf-bar');
  if (cb) cb.checked = appSettings.showConfBar;
  const ar = document.getElementById('setting-auto-refresh');
  if (ar) ar.checked = appSettings.autoRefresh;
  const di = document.getElementById('setting-disclaimer');
  if (di) di.checked = appSettings.showDisclaimer;
}

function initSettings() {
  loadSettings();
  const overlay = document.getElementById('settings-overlay');
  document.getElementById('settings-btn')?.addEventListener('click', () => {
    overlay.classList.add('settings-open');
    syncSettingsUI();
  });

  document.getElementById('setting-language')?.addEventListener('change', e => {
    appSettings.language = e.target.value; saveSettings(); applySettings();
  });

  const BTN_GROUP_MAP = { currency: 'currency', period: 'defaultPeriod', 'chart-style': 'chartStyle' };
  document.querySelectorAll('.btn-group[id^="setting-"]').forEach(group => {
    const key = BTN_GROUP_MAP[group.id.replace('setting-', '')];
    group.querySelectorAll('.btn-group-item').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.btn-group-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (key) { appSettings[key] = btn.dataset.val; saveSettings(); applySettings(); }
      });
    });
  });

  document.getElementById('setting-conf-bar')?.addEventListener('change', e => {
    appSettings.showConfBar = e.target.checked; saveSettings(); applySettings();
  });
  document.getElementById('setting-auto-refresh')?.addEventListener('change', e => {
    appSettings.autoRefresh = e.target.checked; saveSettings();
  });
  document.getElementById('setting-disclaimer')?.addEventListener('change', e => {
    appSettings.showDisclaimer = e.target.checked; saveSettings(); applySettings();
  });

  applySettings();
}

// ── State ──────────────────────────────────────────────────────────────────────
let overlayState = { msft: true, nvda: true, amzn: true, gold: false, oil: false, vix: false };
let historyData  = [];
let filteredData = [];

// ── Home chart pan/crosshair state ─────────────────────────────────────────────
let histRenderData  = [];
let histRenderXs    = null;
let histIsDragging  = false;
let histDragStartX  = 0;
let histDragStartVS = 0;
let histDragStartVE = 0;
let histRafId       = null;

let homeWinEnd        = 0;
let homeWinSize       = 22;
let homeIsDragging    = false;
let homeDragStartX    = 0;
let homeDragStartWinEnd = 0;
let homeRafId         = null;
let homeRenderData    = [];
let homeRenderXs      = null;
let homeRenderYs      = null;
const PERIOD_WIN_SIZES = { '1W': 5, '1M': 22, '3M': 65, '1Y': 252, 'MAX': Infinity };

// ── Navigation ─────────────────────────────────────────────────────────────────
function initNav() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(link.dataset.page);
    });
  });
}

// ── Chart view state (indices into historyData) ────────────────────────────
let viewStart = 0;
let viewEnd   = 0;

function updateDateDisplay() {
  const s = document.getElementById('disp-start');
  const e = document.getElementById('disp-end');
  if (s && historyData[viewStart]) s.textContent = historyData[viewStart].date?.slice(0, 10) ?? '—';
  if (e && historyData[viewEnd])   e.textContent = historyData[viewEnd].date?.slice(0, 10) ?? '—';
}

function renderView() {
  filteredData = historyData.slice(viewStart, viewEnd + 1);
  renderHistoryChart(filteredData, overlayState);
  renderOverlayToggles();
  renderReturns(filteredData);
  renderSummaryStats(filteredData);
  updateDateDisplay();
}

function setPeriod(period) {
  if (!historyData.length) return;
  const last = new Date(historyData.at(-1).date);
  let cutoff = null;
  if (period === '1W') { cutoff = new Date(last); cutoff.setDate(cutoff.getDate() - 7); }
  else if (period === '1M') { cutoff = new Date(last); cutoff.setMonth(cutoff.getMonth() - 1); }
  else if (period === '3M') { cutoff = new Date(last); cutoff.setMonth(cutoff.getMonth() - 3); }
  else if (period === '1Y') { cutoff = new Date(last); cutoff.setFullYear(cutoff.getFullYear() - 1); }

  if (cutoff) {
    const cutStr = cutoff.toISOString().slice(0, 10);
    viewStart = historyData.findIndex(r => r.date >= cutStr);
    if (viewStart < 0) viewStart = 0;
  } else {
    viewStart = 0;
  }
  viewEnd = historyData.length - 1;

  document.querySelectorAll('.period-bar-btn').forEach(b =>
    b.classList.toggle('period-bar-active', b.dataset.period === period)
  );
  renderView();
}

function initChartInteraction() {
  // ── Home chart period bar ──────────────────────────────────────────────────
  document.querySelectorAll('#home-period-bar .period-bar-btn[data-period]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.disabled) return;
      document.querySelectorAll('#home-period-bar .period-bar-btn').forEach(b => b.classList.remove('period-bar-active'));
      btn.classList.add('period-bar-active');
      const size = PERIOD_WIN_SIZES[btn.dataset.period];
      homeWinSize = (size === undefined || !isFinite(size)) ? historyData.length : size;
      homeWinEnd  = historyData.length - 1;
      drawHomeChart();
    });
  });

  // ── History chart period bar ───────────────────────────────────────────────
  document.querySelectorAll('.period-bar-btn[data-period]').forEach(btn => {
    if (btn.closest('#home-period-bar')) return;
    btn.addEventListener('click', () => setPeriod(btn.dataset.period));
  });

  // ── Calendar modal ─────────────────────────────────────────────────────────
  const overlay  = document.getElementById('cal-overlay');
  const btnCal   = document.getElementById('btn-cal');
  const btnClose = document.getElementById('cal-close');
  const btnCancel= document.getElementById('cal-cancel');
  const btnGoto  = document.getElementById('cal-goto');
  let activeTab  = 'single';
  let calTarget  = 'history';

  function openModal() { overlay.classList.add('cal-open'); }
  function closeModal(){ overlay.classList.remove('cal-open'); }

  btnCal?.addEventListener('click', () => { calTarget = 'history'; openModal(); });
  document.getElementById('btn-home-cal')?.addEventListener('click', () => { calTarget = 'home'; openModal(); });
  btnClose?.addEventListener('click', closeModal);
  btnCancel?.addEventListener('click', closeModal);
  overlay?.addEventListener('click', e => { if (e.target === overlay) closeModal(); });

  document.querySelectorAll('.cal-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      activeTab = tab.dataset.tab;
      document.querySelectorAll('.cal-tab').forEach(t => t.classList.toggle('cal-tab-active', t === tab));
      document.getElementById('cal-tab-single').classList.toggle('cal-hidden', activeTab !== 'single');
      document.getElementById('cal-tab-range').classList.toggle('cal-hidden', activeTab !== 'range');
    });
  });

  btnGoto?.addEventListener('click', () => {
    if (activeTab === 'single') {
      const d = document.getElementById('cal-single-date').value;
      if (!d) return;
      if (calTarget === 'home') {
        const idx = historyData.findIndex(r => r.date >= d);
        if (idx >= 0) {
          homeWinEnd  = Math.min(historyData.length - 1, idx + 15);
          homeWinSize = 31;
          document.querySelectorAll('#home-period-bar .period-bar-btn').forEach(b => b.classList.remove('period-bar-active'));
          drawHomeChart();
        }
      } else {
        const idx = historyData.findIndex(r => r.date >= d);
        if (idx >= 0) {
          viewStart = Math.max(0, idx - 30);
          viewEnd   = Math.min(historyData.length - 1, idx + 30);
          document.querySelectorAll('.period-bar-btn:not(#home-period-bar .period-bar-btn)').forEach(b => b.classList.remove('period-bar-active'));
          renderView();
        }
      }
    } else {
      const s = document.getElementById('cal-range-start').value;
      const e = document.getElementById('cal-range-end').value;
      if (!s || !e) return;
      if (calTarget === 'home') {
        const si = historyData.findIndex(r => r.date >= s);
        const ei = historyData.findLastIndex(r => r.date <= e);
        if (si >= 0 && ei >= si) {
          homeWinEnd  = ei;
          homeWinSize = ei - si + 1;
          document.querySelectorAll('#home-period-bar .period-bar-btn').forEach(b => b.classList.remove('period-bar-active'));
          drawHomeChart();
        }
      } else {
        const si = historyData.findIndex(r => r.date >= s);
        const ei = historyData.findLastIndex(r => r.date <= e);
        if (si >= 0 && ei >= si) {
          viewStart = si;
          viewEnd   = ei;
          document.querySelectorAll('.period-bar-btn:not(#home-period-bar .period-bar-btn)').forEach(b => b.classList.remove('period-bar-active'));
          renderView();
        }
      }
    }
    closeModal();
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
function updatePeriodBtnAvailability() {
  document.querySelectorAll('#home-period-bar .period-bar-btn[data-period]').forEach(btn => {
    btn.disabled = false;
    btn.style.opacity = '';
    btn.style.cursor  = '';
    btn.title = '';
  });
}

function filterByPeriod(data, period) {
  if (!data.length) return data;
  const last = new Date(data.at(-1).date);
  let cutoff = null;
  if (period === '1W') { cutoff = new Date(last); cutoff.setDate(cutoff.getDate() - 7); }
  else if (period === '1M') { cutoff = new Date(last); cutoff.setMonth(cutoff.getMonth() - 1); }
  else if (period === '3M') { cutoff = new Date(last); cutoff.setMonth(cutoff.getMonth() - 3); }
  else if (period === '1Y') { cutoff = new Date(last); cutoff.setFullYear(cutoff.getFullYear() - 1); }
  else if (period === 'YTD') { cutoff = new Date(last.getFullYear(), 0, 1); }
  if (!cutoff) return data;
  const cutStr = cutoff.toISOString().slice(0, 10);
  return data.filter(r => r.date >= cutStr);
}

function drawHomeChart() {
  const n = historyData.length;
  if (!n) return;
  const winEnd  = Math.min(homeWinEnd, n - 1);
  const winSize = isFinite(homeWinSize) ? Math.min(homeWinSize, n) : n;
  const winStart = Math.max(0, winEnd - winSize + 1);
  renderLine30(historyData.slice(winStart, winEnd + 1));
}

function renderLine30(data) {
  const svg = clearSvg('svg-line30');
  if (!svg || !data.length) return;
  const W = 1080, H = 210;
  const pts = data.map(r => r.close);
  if (!pts.length) return;
  const minV = Math.min(...pts) - 4, maxV = Math.max(...pts) + 4;
  const xs = i => 50 + (i * (W - 90)) / Math.max(pts.length - 1, 1);
  const ys = v => H - 30 - ((v - minV) / (maxV - minV || 1)) * (H - 60);
  const path = pts.map((v, i) => `${i===0?'M':'L'} ${xs(i).toFixed(1)} ${ys(v).toFixed(1)}`).join(' ');
  const area = `${path} L ${xs(pts.length-1).toFixed(1)} ${H-30} L ${xs(0).toFixed(1)} ${H-30} Z`;

  const defs = svgEl('defs');
  const lg = svgEl('linearGradient', { id:'lg30', x1:'0', x2:'0', y1:'0', y2:'1' });
  lg.append(
    svgEl('stop', { offset:'0%',   'stop-color':C.accent, 'stop-opacity':'0.35' }),
    svgEl('stop', { offset:'100%', 'stop-color':C.accent, 'stop-opacity':'0'    })
  );
  defs.append(lg); svg.append(defs);

  for (let i = 0; i < 5; i++) {
    const y = 20 + i * ((H-50)/4);
    svg.append(svgEl('line', { x1:50, x2:W-40, y1:y, y2:y, stroke:C.lineSoft, 'stroke-dasharray':'2 4' }));
  }
  // Axis labels rendered as HTML (no SVG distortion)
  _renderHomeAxisLabels(data, minV, maxV);

  svg.append(svgEl('path', { d:area, fill:'url(#lg30)' }));
  svg.append(svgEl('path', { d:path, fill:'none', stroke:C.accent, 'stroke-width':'2' }));
  const last = pts[pts.length-1];
  const actualW = svg.getBoundingClientRect().width || W;
  const rx = (4*W/actualW).toFixed(2);
  svg.append(svgEl('ellipse', { cx:xs(pts.length-1).toFixed(1), cy:ys(last).toFixed(1), rx, ry:'4', fill:C.accent, stroke:C.bg, 'stroke-width':'2', 'vector-effect':'non-scaling-stroke' }));

  // ── Crosshair overlay ──────────────────────────────────────────────────────
  const xhairG = svgEl('g'); xhairG.style.pointerEvents = 'none'; xhairG.setAttribute('visibility','hidden');
  xhairG.append(
    svgEl('line', { id:'hx-hl', x1:50, x2:W-40, y1:0,  y2:0,    stroke:`${C.accent}33`, 'stroke-width':'1', 'stroke-dasharray':'3 4' }),
    svgEl('line', { id:'hx-vl', x1:0,  x2:0,    y1:20, y2:H-30, stroke:C.accent, 'stroke-width':'1.5', opacity:'0.7' }),
    svgEl('circle', { id:'hx-dot', r:'3.5', fill:C.accent, stroke:C.bg, 'stroke-width':'1.5' })
  );
  svg.append(xhairG);
  svg._xhairG = xhairG;

  // Store render params for interaction handler
  homeRenderData = data;
  homeRenderXs   = xs;
  homeRenderYs   = ys;
}

function _renderHomeAxisLabels(data, minV, maxV) {
  const wrapper = document.getElementById('svg-line30')?.parentElement;
  if (!wrapper) return;
  wrapper.querySelectorAll('.hx-axis-label').forEach(el => el.remove());

  const W = 1080, H = 210;
  const sym  = CURRENCY_SYMBOLS[appSettings.currency] || '$';
  const rate = exchangeRates[appSettings.currency] || 1;
  const dec  = appSettings.currency === 'JPY' ? 0 : 2;

  // Y-axis (3 price labels on left)
  [maxV, (maxV + minV) / 2, minV].forEach((v, i) => {
    const yPct = ((20 + i * ((H - 50) / 2) + 4) / H) * 100;
    const el = document.createElement('div');
    el.className = 'hx-axis-label hx-y-label';
    el.style.top = yPct + '%';
    el.textContent = sym + (v * rate).toFixed(dec);
    wrapper.appendChild(el);
  });

  // X-axis (date labels at bottom)
  if (data.length) {
    const isLatest = homeWinEnd >= historyData.length - 1 || !historyData.length;
    const xItems = [
      { xPct: (50 / W) * 100,       text: fmtDate(data[0].date),                                         anchor: 'left' },
      ...(data.length > 10 ? [{ xPct: ((W / 2 - 20) / W) * 100, text: fmtDate(data[Math.floor(data.length / 2)].date), anchor: 'center' }] : []),
      { xPct: ((W - 130) / W) * 100, text: fmtDate(data[data.length - 1].date) + (isLatest ? ' (today)' : ''), anchor: 'right' },
    ];
    xItems.forEach(({ xPct, text, anchor }) => {
      const el = document.createElement('div');
      el.className = 'hx-axis-label hx-x-label';
      el.style.left = xPct + '%';
      if (anchor === 'center') el.style.transform = 'translateX(-50%)';
      if (anchor === 'right')  el.style.transform = 'translateX(-100%)';
      el.textContent = text;
      wrapper.appendChild(el);
    });
  }
}

// ── Home chart interaction (set up once) ──────────────────────────────────────
function initHomeInteraction() {
  const svg = document.getElementById('svg-line30');
  if (!svg) return;
  const W = 1080, H = 210;

  function svgPx(e) {
    const r = svg.getBoundingClientRect();
    return (e.clientX - r.left) * (W / (r.width || W));
  }

  function nearestIdx(px) {
    if (!homeRenderData.length) return 0;
    const ppp = (W - 90) / Math.max(homeRenderData.length - 1, 1);
    return Math.max(0, Math.min(homeRenderData.length - 1, Math.round((px - 50) / ppp)));
  }

  function showXhair(e) {
    const px = svgPx(e);
    const xhairG = svg._xhairG;
    if (!xhairG || px < 50 || px > W - 40 || !homeRenderData.length) {
      xhairG?.setAttribute('visibility', 'hidden'); return;
    }
    const i  = nearestIdx(px);
    const d  = homeRenderData[i];
    const cx = homeRenderXs(i);
    const cy = homeRenderYs(d.close);
    const sym  = CURRENCY_SYMBOLS[appSettings.currency] || '$';
    const rate = exchangeRates[appSettings.currency] || 1;
    const dec  = appSettings.currency === 'JPY' ? 0 : 2;
    const priceStr = sym + (d.close * rate).toFixed(dec);
    const dateStr  = d.date.slice(0, 10);

    const el = id => xhairG.querySelector('#' + id);
    el('hx-vl').setAttribute('x1', cx); el('hx-vl').setAttribute('x2', cx);
    el('hx-hl').setAttribute('y1', cy); el('hx-hl').setAttribute('y2', cy);
    el('hx-dot').setAttribute('cx', cx); el('hx-dot').setAttribute('cy', cy);
    xhairG.setAttribute('visibility', 'visible');

    // HTML labels (no SVG distortion)
    const svgRect = svg.getBoundingClientRect();
    const H = 210;
    const pxX = (cx / W) * svgRect.width;
    const pxY = (cy / H) * svgRect.height;
    const dateLbl  = document.getElementById('hx-date-lbl');
    const priceLbl = document.getElementById('hx-price-lbl');
    if (dateLbl)  { dateLbl.textContent  = dateStr;  dateLbl.style.left  = pxX + 'px'; dateLbl.style.display  = 'block'; }
    if (priceLbl) { priceLbl.textContent = priceStr; priceLbl.style.top  = pxY + 'px'; priceLbl.style.display = 'block'; }
  }

  svg.addEventListener('mousemove', e => { if (!homeIsDragging) showXhair(e); });
  function hideXhair() {
    svg._xhairG?.setAttribute('visibility', 'hidden');
    const dl = document.getElementById('hx-date-lbl');
    const pl = document.getElementById('hx-price-lbl');
    if (dl) dl.style.display = 'none';
    if (pl) pl.style.display = 'none';
  }
  svg.addEventListener('mouseleave', () => { if (!homeIsDragging) hideXhair(); });

  svg.addEventListener('pointerdown', e => {
    homeIsDragging      = true;
    homeDragStartX      = e.clientX;
    homeDragStartWinEnd = homeWinEnd;
    svg.setPointerCapture(e.pointerId);
    svg.style.cursor    = 'grabbing';
    hideXhair();
    e.preventDefault();
  });

  svg.addEventListener('pointermove', e => {
    if (!homeIsDragging) return;
    const rect    = svg.getBoundingClientRect();
    const scaleX  = W / (rect.width || W);
    const svgDelta = (e.clientX - homeDragStartX) * scaleX;
    const pxPerPt  = (W - 90) / Math.max(homeRenderData.length - 1, 1);
    const ptDelta  = Math.round(svgDelta / pxPerPt);
    const minEnd   = isFinite(homeWinSize) ? homeWinSize - 1 : historyData.length - 1;
    const newEnd   = Math.max(minEnd, Math.min(historyData.length - 1, homeDragStartWinEnd - ptDelta));
    if (newEnd !== homeWinEnd) {
      homeWinEnd = newEnd;
      if (homeRafId) cancelAnimationFrame(homeRafId);
      homeRafId = requestAnimationFrame(drawHomeChart);
    }
    e.preventDefault();
  });

  const endDrag = () => {
    homeIsDragging = false;
    svg.style.cursor = 'crosshair';
    if (homeRafId) { cancelAnimationFrame(homeRafId); homeRafId = null; }
  };
  svg.addEventListener('pointerup',     endDrag);
  svg.addEventListener('pointercancel', endDrag);
  svg.style.cursor = 'crosshair';
}

// ── Page 2 — History chart ─────────────────────────────────────────────────────
function renderPredictionHistory(res) {
  const table = document.getElementById('pred-hist-table');
  const accEl = document.getElementById('pred-hist-accuracy');
  const note  = document.querySelector('.pred-hist-dummy-note');
  if (!table) return;
  if (!res || !res.data?.length) { table.innerHTML = '<p style="padding:12px;color:var(--text-dim)">No data available.</p>'; return; }

  if (accEl) accEl.textContent = res.accuracy != null ? `Accuracy: ${res.accuracy}%` : '';
  if (note)  note.textContent  = res.has_dummy ? '★ estimated predictions' : '';

  const dir = (d) => d === 1
    ? '<span class="ph-dir ph-up">↑ UP</span>'
    : d === 2
      ? '<span class="ph-dir ph-neutral">– SAME</span>'
      : '<span class="ph-dir ph-down">↓ DOWN</span>';

  table.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Close</th>
          <th>Prediction</th>
          <th>Confidence</th>
          <th>Actual</th>
          <th>Result</th>
        </tr>
      </thead>
      <tbody>
        ${res.data.map(r => `
          <tr>
            <td>${r.date}</td>
            <td>$${r.close.toFixed(2)}</td>
            <td>${dir(r.predicted_direction)} ${r.is_dummy ? '<span class="ph-dummy">(est.)</span>' : ''}</td>
            <td class="ph-conf">${r.confidence}%</td>
            <td>${dir(r.actual_direction)}</td>
            <td><span class="ph-badge ${r.correct === null ? 'neutral' : (r.correct ? 'correct' : 'incorrect')}">${r.correct === null ? '– Same' : (r.correct ? '● Correct' : '● Wrong')}</span></td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

function renderHistoryChart(data, overlays) {
  const svg = clearSvg('svg-history');
  if (!svg || !data.length) return;
  const W = 1080, H = 300;
  const n = data.length;

  // Scale every series independently to fit within chart bounds (shows trend shape)
  const fitToRange = (arr, lo = 74, hi = 126) => {
    const vals = arr.filter(v => v != null);
    if (!vals.length) return arr;
    const dMin = Math.min(...vals), dMax = Math.max(...vals);
    const span = dMax - dMin || 1;
    return arr.map(v => v == null ? null : lo + ((v - dMin) / span) * (hi - lo));
  };
  // Smooth window scales with dataset size
  const w = n > 500 ? Math.floor(n / 150) : n > 100 ? 3 : 1;
  const smooth = (arr, win = w) => win <= 1 ? arr : arr.map((v, i) => {
    if (v == null) return null;
    const slice = arr.slice(Math.max(0, i - win + 1), i + 1).filter(x => x != null);
    return slice.reduce((a, b) => a + b, 0) / slice.length;
  });
  const pts      = smooth(fitToRange(data.map(r => r.close)));
  const nvdaPts  = smooth(fitToRange(data.map(r => r.nvda_close)));
  const amznPts  = smooth(fitToRange(data.map(r => r.amzn_close)));
  const goldPts  = smooth(fitToRange(data.map(r => r.gold_close)));
  const oilPts   = smooth(fitToRange(data.map(r => r.oil_close)));
  const vixPts   = smooth(fitToRange(data.map(r => r.vix)));

  const min = 60, max = 140;

  const xs = i => 50 + (i * (W - 100)) / Math.max(n - 1, 1);
  const ys = v => H - 45 - ((v - min) / (max - min)) * (H - 70);
  const mkPath = arr => {
    let d = '', gap = true;
    arr.forEach((v, i) => {
      if (v == null) { gap = true; return; }
      const cmd = gap ? 'M' : 'L';
      d += `${cmd} ${xs(i).toFixed(1)} ${ys(Math.min(Math.max(v, min), max)).toFixed(1)} `;
      gap = false;
    });
    return d.trim();
  };

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
    svg.append(svgEl('line', { x1:50, x2:W-50, y1:y, y2:y, stroke:C.lineSoft, 'stroke-dasharray':'2 4' }));
  }
  // Baseline at 100 (starting value)
  svg.append(svgEl('line', { x1:50, x2:W-50, y1:ys(100).toFixed(1), y2:ys(100).toFixed(1), stroke:C.line, 'stroke-dasharray':'6 3', opacity:'0.5' }));

  // Axis labels via HTML (no SVG distortion)
  _renderHistoryAxisLabels(data, xs, ys, n, min, max, H, W);

  if (overlays.msft) {
    const areaPts = mkPath(pts);
    svg.append(svgEl('path', { d: `${areaPts} L ${xs(n-1).toFixed(1)} ${H-40} L ${xs(0).toFixed(1)} ${H-40} Z`, fill:'url(#lgh)' }));
    svg.append(svgEl('path', { d: mkPath(pts), fill:'none', stroke:C.accent, 'stroke-width':'2' }));
  }
  if (overlays.nvda) svg.append(svgEl('path', { d: mkPath(nvdaPts), fill:'none', stroke:'#DBD56E',  'stroke-width':'1.5', 'stroke-dasharray':'5 2', opacity:'0.85' }));
  if (overlays.amzn) svg.append(svgEl('path', { d: mkPath(amznPts), fill:'none', stroke:'#2A2A72',  'stroke-width':'1.5', 'stroke-dasharray':'5 2', opacity:'0.85' }));
  if (overlays.gold) svg.append(svgEl('path', { d: mkPath(goldPts), fill:'none', stroke:C.amber,    'stroke-width':'1.5', 'stroke-dasharray':'4 3', opacity:'0.85' }));
  if (overlays.oil)  svg.append(svgEl('path', { d: mkPath(oilPts),  fill:'none', stroke:C.red,      'stroke-width':'1.5', 'stroke-dasharray':'4 3', opacity:'0.7' }));
  if (overlays.vix)  svg.append(svgEl('path', { d: mkPath(vixPts),  fill:'none', stroke:'#2A2A72',  'stroke-width':'1.5', 'stroke-dasharray':'4 3', opacity:'0.6' }));

  // Crosshair vertical line
  const xhairG = svgEl('g'); xhairG.style.pointerEvents = 'none'; xhairG.setAttribute('visibility','hidden');
  xhairG.append(svgEl('line', { id:'hh-vl', x1:0, x2:0, y1:20, y2:H-40, stroke:C.accent, 'stroke-width':'1.5', opacity:'0.7' }));
  svg.append(xhairG);
  svg._histXhairG = xhairG;

  histRenderData = data;
  histRenderXs   = xs;
}

function _renderHistoryAxisLabels(data, xs, ys, n, min, max, H, W) {
  const wrap = document.getElementById('hist-chart-wrap');
  if (!wrap) return;
  wrap.querySelectorAll('.hx-axis-label').forEach(el => el.remove());


  // X-axis: 6 date labels at bottom
  const step = Math.floor(n / 5);
  for (let i = 0; i <= 5; i++) {
    const idx  = Math.min(i * step, n - 1);
    if (!data[idx]) continue;
    const xPct = (xs(idx) / W) * 100;
    const el = document.createElement('div');
    el.className = 'hx-axis-label hx-x-label';
    el.style.left = xPct + '%';
    if (i === 0) el.style.transform = 'none';
    else if (i === 5) el.style.transform = 'translateX(-100%)';
    else el.style.transform = 'translateX(-50%)';
    el.textContent = fmtDate(data[idx].date);
    wrap.appendChild(el);
  }
}

function _hideHistXhair() {
  document.getElementById('svg-history')?._histXhairG?.setAttribute('visibility', 'hidden');
  const dl = document.getElementById('hh-date-lbl');
  const tip = document.getElementById('hist-tooltip');
  if (dl)  dl.style.display  = 'none';
  if (tip) tip.style.display = 'none';
}

function initHistoryInteraction() {
  const svg = document.getElementById('svg-history');
  if (!svg) return;
  const W = 1080, H = 300;

  function svgPx(e) {
    const r = svg.getBoundingClientRect();
    return (e.clientX - r.left) * (W / (r.width || W));
  }

  function nearestIdx(px) {
    if (!histRenderData.length) return 0;
    const ppp = (W - 100) / Math.max(histRenderData.length - 1, 1);
    return Math.max(0, Math.min(histRenderData.length - 1, Math.round((px - 60) / ppp)));
  }

  svg.addEventListener('mousemove', e => {
    if (histIsDragging) return;
    const px = svgPx(e);
    if (px < 60 || px > W - 40 || !histRenderData.length) { _hideHistXhair(); return; }

    const i  = nearestIdx(px);
    const cx = histRenderXs(i);
    const d  = histRenderData[i];

    // Crosshair line
    const xhG = svg._histXhairG;
    if (xhG) {
      xhG.querySelector('#hh-vl').setAttribute('x1', cx);
      xhG.querySelector('#hh-vl').setAttribute('x2', cx);
      xhG.setAttribute('visibility', 'visible');
    }

    // Date label (HTML, top of line)
    const svgRect = svg.getBoundingClientRect();
    const pxX = (cx / W) * svgRect.width;
    const dl = document.getElementById('hh-date-lbl');
    if (dl) { dl.textContent = d.date.slice(0, 10); dl.style.left = pxX + 'px'; dl.style.display = 'block'; }

    // Tooltip card
    const base = histRenderData[0];
    const sym  = CURRENCY_SYMBOLS[appSettings.currency] || '$';
    const rate = exchangeRates[appSettings.currency] || 1;
    const dec  = appSettings.currency === 'JPY' ? 0 : 2;
    const sign = v => v >= 0 ? `+${v.toFixed(1)}%` : `${v.toFixed(1)}%`;
    const col  = v => v >= 0 ? C.accent : C.red;

    const msftPct = (d.close - base.close) / base.close * 100;
    let html = `<div class="hist-tip-date">${d.date.slice(0,10)}</div>`;
    html += `<div class="hist-tip-row">
      <span class="hist-tip-key" style="color:${C.accent}">MSFT</span>
      <span class="hist-tip-val">${sym}${(d.close * rate).toFixed(dec)}</span>
      <span class="hist-tip-pct" style="color:${col(msftPct)}">${sign(msftPct)}</span>
    </div>`;
    if (overlayState.nvda && d.nvda_close && base.nvda_close) {
      const p = (d.nvda_close - base.nvda_close) / base.nvda_close * 100;
      html += `<div class="hist-tip-row"><span class="hist-tip-key" style="color:#DBD56E">NVDA</span><span class="hist-tip-val">${sym}${(d.nvda_close * rate).toFixed(dec)}</span><span class="hist-tip-pct" style="color:${col(p)}">${sign(p)}</span></div>`;
    }
    if (overlayState.amzn && d.amzn_close && base.amzn_close) {
      const p = (d.amzn_close - base.amzn_close) / base.amzn_close * 100;
      html += `<div class="hist-tip-row"><span class="hist-tip-key" style="color:#2A2A72">AMZN</span><span class="hist-tip-val">${sym}${(d.amzn_close * rate).toFixed(dec)}</span><span class="hist-tip-pct" style="color:${col(p)}">${sign(p)}</span></div>`;
    }
    if (overlayState.gold && d.gold_close && base.gold_close) {
      const p = (d.gold_close - base.gold_close) / base.gold_close * 100;
      html += `<div class="hist-tip-row"><span class="hist-tip-key" style="color:${C.amber}">Gold</span><span class="hist-tip-val">${sym}${(d.gold_close * rate).toFixed(dec)}</span><span class="hist-tip-pct" style="color:${col(p)}">${sign(p)}</span></div>`;
    }
    if (overlayState.oil && d.oil_close && base.oil_close) {
      const p = (d.oil_close - base.oil_close) / base.oil_close * 100;
      html += `<div class="hist-tip-row"><span class="hist-tip-key" style="color:${C.red}">Crude</span><span class="hist-tip-val">${sym}${(d.oil_close * rate).toFixed(dec)}</span><span class="hist-tip-pct" style="color:${col(p)}">${sign(p)}</span></div>`;
    }
    if (overlayState.vix && d.vix && base.vix) {
      const p = (d.vix - base.vix) / base.vix * 100;
      html += `<div class="hist-tip-row"><span class="hist-tip-key" style="color:#2A2A72">VIX</span><span class="hist-tip-val">${d.vix.toFixed(1)}</span><span class="hist-tip-pct" style="color:${col(-p)}">${sign(p)}</span></div>`;
    }

    const tip = document.getElementById('hist-tooltip');
    if (tip) {
      tip.innerHTML = html;
      tip.style.display = 'block';
      const relX = e.clientX - svgRect.left;
      const relY = e.clientY - svgRect.top;
      const tipW = tip.offsetWidth || 160;
      let left = relX + 14;
      let top  = relY - 20;
      if (left + tipW > svgRect.width - 10) left = relX - tipW - 14;
      if (top < 5) top = 5;
      tip.style.left = left + 'px';
      tip.style.top  = top  + 'px';
    }
  });

  svg.addEventListener('mouseleave', () => { if (!histIsDragging) _hideHistXhair(); });

  // ── Drag to pan ────────────────────────────────────────────────────────────
  svg.addEventListener('pointerdown', e => {
    histIsDragging  = true;
    histDragStartX  = e.clientX;
    histDragStartVS = viewStart;
    histDragStartVE = viewEnd;
    svg.setPointerCapture(e.pointerId);
    svg.style.cursor = 'grabbing';
    _hideHistXhair();
    e.preventDefault();
  });

  svg.addEventListener('pointermove', e => {
    if (!histIsDragging) return;
    const rect     = svg.getBoundingClientRect();
    const scaleX   = W / (rect.width || W);
    const svgDelta = (e.clientX - histDragStartX) * scaleX;
    const winSize  = histDragStartVE - histDragStartVS;
    const pxPerPt  = (W - 100) / Math.max(winSize, 1);
    const ptDelta  = Math.round(svgDelta / pxPerPt);

    const newVS = Math.max(0, Math.min(historyData.length - 1 - winSize, histDragStartVS - ptDelta));
    const newVE = newVS + winSize;

    if (newVS !== viewStart || newVE !== viewEnd) {
      viewStart = newVS;
      viewEnd   = newVE;
      document.querySelectorAll('.period-bar-btn:not(#home-period-bar .period-bar-btn)').forEach(b => b.classList.remove('period-bar-active'));
      if (histRafId) cancelAnimationFrame(histRafId);
      histRafId = requestAnimationFrame(renderView);
    }
    e.preventDefault();
  });

  const endHistDrag = () => {
    histIsDragging = false;
    svg.style.cursor = 'crosshair';
    if (histRafId) { cancelAnimationFrame(histRafId); histRafId = null; }
  };
  svg.addEventListener('pointerup',     endHistDrag);
  svg.addEventListener('pointercancel', endHistDrag);

  svg.style.cursor = 'crosshair';
}

// ── Page 2 — Daily returns ─────────────────────────────────────────────────────
function renderReturns(data) {
  const svg = clearSvg('svg-returns');
  if (!svg || data.length < 2) return;
  const W = 760, H = 150;
  const slice = data.slice(-61);
  const vals = slice.slice(1).map((r, i) => ((r.close - slice[i].close) / slice[i].close) * 100);
  const rawMax = Math.max(...vals.map(Math.abs));
  const maxAbs = Math.max(2, Math.ceil(rawMax * 2) / 2);
  const bw = (W - 100) / vals.length;
  const xs = i => 60 + i * bw;
  const mid = H / 2;               // 75
  const maxH = mid - 14;           // 61 — bar max height, labels align to this

  // Gridlines at scale extremes and zero
  svg.append(svgEl('line', { x1:60, x2:W-40, y1:mid-maxH, y2:mid-maxH, stroke:C.lineSoft, 'stroke-dasharray':'2,4' }));
  svg.append(svgEl('line', { x1:60, x2:W-40, y1:mid,      y2:mid,      stroke:C.line }));
  svg.append(svgEl('line', { x1:60, x2:W-40, y1:mid+maxH, y2:mid+maxH, stroke:C.lineSoft, 'stroke-dasharray':'2,4' }));

  vals.forEach((v, i) => {
    const h = Math.max((Math.abs(v) / maxAbs) * maxH, 1);
    const y = v >= 0 ? mid - h : mid;
    svg.append(svgEl('rect', { x: xs(i).toFixed(1), y: y.toFixed(1), width: Math.max(bw-2,1).toFixed(1), height: h.toFixed(1), fill: v >= 0 ? '#009FFD' : '#DBD56E' }));
  });

  const lbl = v => `${Math.abs(v) >= 10 ? v.toFixed(0) : v.toFixed(1)}%`;
  // Labels sit the same distance (9px) below their respective gridline
  svgText(svg, 8, mid - maxH + 9, `+${lbl(maxAbs)}`, { mono:true, size:'9' });
  svgText(svg, 8, mid + 5,         '0.0%',            { mono:true, size:'9' });
  svgText(svg, 8, mid + maxH + 9, `-${lbl(maxAbs)}`, { mono:true, size:'9' });
}

// ── Page 2 — Summary stats ─────────────────────────────────────────────────────
function renderSummaryStats(data) {
  const el = document.getElementById('summary-stats');
  if (!el || !data.length) return;
  const closes  = data.map(r => r.close);
  const rets    = closes.slice(1).map((c, i) => ((c - closes[i]) / closes[i]) * 100);
  if (!rets.length) return;
  const mean    = rets.reduce((a,b) => a+b, 0) / rets.length;
  const vol     = Math.sqrt(rets.reduce((a,b) => a + Math.pow(b-mean,2), 0) / rets.length);
  const maxR    = Math.max(...rets), minR = Math.min(...rets);
  const maxDate = data[rets.indexOf(maxR)+1]?.date?.slice(0,10) ?? '';
  const minDate = data[rets.indexOf(minR)+1]?.date?.slice(0,10) ?? '';
  const sign    = v => v >= 0 ? '+' : '';

  // Max Drawdown: peak-to-trough over the displayed period
  let peak = closes[0], maxDD = 0;
  closes.forEach(c => {
    if (c > peak) peak = c;
    const dd = (peak - c) / peak * 100;
    if (dd > maxDD) maxDD = dd;
  });

  // Annualised Sharpe (252 trading days, risk-free ≈ 0)
  const sharpe = vol > 0 ? (mean / vol) * Math.sqrt(252) : 0;

  const stats = [
    ['Mean Return',    `${sign(mean)}${mean.toFixed(3)}%`,          C.accent],
    ['Volatility (σ)', `${vol.toFixed(2)}%`,                        C.text],
    ['Max Drawdown',   `−${maxDD.toFixed(1)}%`,                     C.amber],
    ['Best Day',       `+${maxR.toFixed(2)}% · ${maxDate}`,         C.accent],
    ['Worst Day',      `${minR.toFixed(2)}% · ${minDate}`,          C.red],
    ['Sharpe (ann.)',  sharpe.toFixed(2),                            C.text],
  ];
  el.innerHTML = stats.map(([k, v, col], i) => `
    <div class="stat-row" ${i===5?'style="border-bottom:none"':''}>
      <span class="stat-key">${k}</span>
      <span class="stat-val" style="color:${col}">${v}</span>
    </div>
  `).join('');
}

// ── Page 2 — Overlay toggles ───────────────────────────────────────────────────
const OVERLAY_INFO = {
  msft: 'Microsoft Corporation (MSFT)\nThe predicted stock.\nTech giant — cloud, software & AI.',
  nvda: 'NVIDIA Corporation (NVDA)\nPeer feature used by the model.\nRelative strength vs MSFT is the #1 predictor.',
  amzn: 'Amazon.com (AMZN)\nPeer feature used by the model.\nVolume momentum and relative return vs MSFT.',
};

function renderOverlayToggles() {
  const el = document.getElementById('overlay-toggles');
  if (!el) return;
  const items = [
    { key:'msft', label:'MSFT', color: C.accent  },
    { key:'nvda', label:'NVDA', color: '#DBD56E' },
    { key:'amzn', label:'AMZN', color: '#2A2A72' },
  ];
  el.innerHTML = items.map(t => `
    <div class="overlay-toggle ${overlayState[t.key]?'on':''}" data-key="${t.key}" style="--clr:${t.color}">
      <span class="toggle-line"></span>${t.label}
      <span class="toggle-switch"><span class="toggle-thumb"></span></span>
    </div>
  `).join('') + `
    <div class="overlay-info-btn" tabindex="0" aria-label="Series info">
      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6">
        <circle cx="7.5" cy="7.5" r="6.5"/>
        <line x1="7.5" y1="6.5" x2="7.5" y2="11"/>
        <circle cx="7.5" cy="4.5" r="0.7" fill="currentColor" stroke="none"/>
      </svg>
      <div class="overlay-info-tip">
        ${items.map(t => `<div class="info-tip-row"><span class="info-tip-dot" style="background:${t.color}"></span><div><b>${t.label}</b><br><span>${OVERLAY_INFO[t.key].split('\n').slice(1).join('<br>')}</span></div></div>`).join('')}
      </div>
    </div>
  `;
  el.querySelectorAll('.overlay-toggle').forEach(tog => {
    tog.addEventListener('click', () => {
      overlayState[tog.dataset.key] = !overlayState[tog.dataset.key];
      renderOverlayToggles();
      renderHistoryChart(historyData, overlayState);
    });
  });
}

// ── Page 3 — Confusion matrix (3×3) ───────────────────────────────────────────
function renderConfusionMatrix() {
  const svg = clearSvg('svg-confusion');
  if (!svg) return;

  // Rows = actual, cols = predicted. Labels: 0=DOWN, 1=UP, 2=SAME
  // XGBoost Weekly · 48 test weeks · diagonal sum = 19 · total = 48
  const matrix = [
    [ 6, 5, 5],  // actual DOWN  (16 total)
    [ 5, 8, 7],  // actual UP    (20 total)
    [ 3, 4, 5],  // actual SAME  (12 total)
  ];
  const labels = ['DOWN', 'UP', 'SAME'];
  const cW = 96, cH = 72, ox = 90, oy = 44;

  svgText(svg, ox + cW * 1.5, 14, 'PREDICTED', { anchor:'middle', mono:true });
  labels.forEach((lbl, i) => {
    svgText(svg, ox + i * cW + cW / 2, 32, lbl, { anchor:'middle', fill:C.textMuted, size:'10' });
    svgText(svg, ox - 8, oy + i * cH + cH / 2 + 4, lbl, { anchor:'end', fill:C.textMuted, size:'10' });
  });
  svgText(svg, 12, oy + cH * 1.5, 'ACTUAL', { mono:true });

  matrix.forEach((row, cy) => {
    row.forEach((v, cx) => {
      const isDiag = cx === cy;
      const rx = ox + cx * cW, ry = oy + cy * cH;
      svg.append(svgEl('rect', { x:rx, y:ry, width:cW-2, height:cH-2,
        fill: isDiag ? C.accent : C.amber,
        'fill-opacity': isDiag ? (0.5 + v / 30) : 0.25 + v / 40,
        stroke: C.lineSoft }));
      const t = svgEl('text', { x:rx+cW/2, y:ry+cH/2+6, 'text-anchor':'middle',
        fill: isDiag ? '#fff' : '#232528',
        'font-size':'20', 'font-weight':'700', 'font-family':SANS });
      t.textContent = v; svg.append(t);
    });
  });
}

// ── Page 3 — Model comparison ──────────────────────────────────────────────────
function renderModelCompare() {
  const svg = clearSvg('svg-model-compare');
  if (!svg) return;
  const models = [
    { name:'Naive Bayes',     f1: 0.31 },
    { name:'ARIMA',           f1: 0.33 },
    { name:'Random Forest',   f1: MODEL_METRICS.rf_weekly.f1 },
    { name:'XGBoost Weekly',  f1: MODEL_METRICS.xgb_weekly.f1, ens:true },
  ];
  const W=560, H=220, padL=110, padR=40, padT=20, padB=36;
  const gap = 10;
  const bh  = (H - padT - padB - gap * (models.length - 1)) / models.length;
  const barW = W - padL - padR;

  // Grid lines at 0, 0.2, 0.4, 0.6, 0.8, 1.0
  [0, 0.2, 0.4, 0.6, 0.8, 1.0].forEach(t => {
    const x = padL + t * barW;
    svg.append(svgEl('line', { x1:x, x2:x, y1:padT, y2:H-padB, stroke:C.lineSoft, 'stroke-dasharray':'2 4' }));
    svgText(svg, x, H - padB + 16, t.toFixed(1), { anchor:'middle', mono:true, size:'10' });
  });

  models.forEach((m, i) => {
    const y = padT + i * (bh + gap);
    const w = m.f1 * barW;
    // Bar background track
    svg.append(svgEl('rect', { x:padL, y, width:barW, height:bh, fill:C.bgSofter, rx:'3' }));
    // Value bar
    svg.append(svgEl('rect', { x:padL, y, width:w.toFixed(1), height:bh, fill:m.ens ? C.accent : C.navy, rx:'3' }));
    // Label
    const nm = svgEl('text', { x:padL-10, y:y+bh/2+4, 'text-anchor':'end', fill:m.ens?C.accent:C.text, 'font-size':'12', 'font-weight':m.ens?'700':'400', 'font-family':SANS });
    nm.textContent = m.name; svg.append(nm);
    // Value
    svgText(svg, padL + w + 7, y + bh/2 + 4, m.f1.toFixed(2), { mono:true, size:'11', fill: m.ens ? C.accent : C.textMuted });
  });

  svgText(svg, padL + barW/2, H - 4, 'F1 Score (test set)', { anchor:'middle', mono:true, size:'10', fill:C.textDim });
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
  const dir      = p?.direction ?? 'UP';
  const isUp     = dir === 'UP';
  const isNeutral= dir === 'SAME';
  const conf     = p?.probability ?? null;
  const color    = isNeutral ? '#2A2A72' : (isUp ? C.accent : C.red);
  const arrow    = isNeutral ? '–' : (isUp ? '↑' : '↓');

  const key      = modelKeyFromName(p?.model_name);
  const accVal   = MODEL_METRICS[key]?.accuracy ?? null;
  const accPct   = accVal !== null ? accVal * 100 : null;

  const arrowEl = document.getElementById('pred-arrow-icon');
  const dirEl   = document.getElementById('pred-dir-text');
  const confEl  = document.getElementById('pred-conf-num');
  const pctEl   = document.getElementById('pred-conf-pct');
  const barEl   = document.getElementById('conf-bar-fill');
  const circle  = document.getElementById('pred-circle');
  const label   = document.querySelector('.pred-conf-label');

  if (arrowEl) arrowEl.textContent  = arrow;
  if (arrowEl) arrowEl.style.color  = color;
  if (dirEl)   dirEl.textContent    = dir;
  if (dirEl)   dirEl.style.color    = color;
  if (label)   label.textContent    = 'Accuracy';
  if (confEl)  confEl.textContent   = accPct !== null ? accPct.toFixed(1) : '–';
  if (pctEl)   pctEl.style.display  = accPct !== null ? '' : 'none';
  if (barEl)   { barEl.style.width = accPct !== null ? `${accPct}%` : '0%'; barEl.style.background = C.accent; }
  if (circle)  { circle.style.borderColor = color; circle.style.boxShadow = `0 0 60px ${color}44`; }

  const modelName = p?.model_name ?? 'Random Forest Weekly';
  document.getElementById('ensemble-rows').innerHTML = `
    <div class="ensemble-row">
      <div class="ensemble-name highlight">${modelName}</div>
      <div class="ensemble-bar-bg">
        <div class="ensemble-bar-fill highlight" style="width:${accPct !== null ? accPct.toFixed(1) : 0}%"></div>
      </div>
      <div class="ensemble-stat">${accPct !== null ? accPct.toFixed(1) + '%' : '–'}</div>
    </div>
  `;
}

// ── Page 1 — KPI tiles ─────────────────────────────────────────────────────────
function renderKPIs(latest, prev) {
  if (!latest) return;
  const closeEl = document.getElementById('tile-close');
  const subEl   = document.getElementById('tile-close-sub');
  const dateEl  = document.getElementById('tile-pred-date');
  baseCloseUSD = latest.close;
  const sym  = CURRENCY_SYMBOLS[appSettings.currency] || '$';
  const rate = exchangeRates[appSettings.currency] || 1;
  const decimals = appSettings.currency === 'JPY' ? 0 : 2;
  if (closeEl) closeEl.textContent = `${sym}${(baseCloseUSD * rate).toFixed(decimals)}`;
  if (subEl && prev) {
    const delta = latest.close - prev.close;
    const pct   = (delta / prev.close * 100).toFixed(2);
    subEl.textContent = `${latest.date?.slice(0,10) ?? ''} · ${delta>=0?'+':''}${pct}%`;
  }
  const nextTradingDay = (() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + 1);
    return d;
  })();
  if (dateEl) {
    dateEl.textContent = nextTradingDay.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric', year:'numeric' });
  }
  const dateLabel = document.getElementById('pred-date-label');
  if (dateLabel) {
    const label = nextTradingDay.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const weekNr = (() => { const d = new Date(nextTradingDay); d.setHours(0,0,0,0); d.setDate(d.getDate()+3-(d.getDay()+6)%7); const w = new Date(d.getFullYear(),0,4); return 'W'+String(1+Math.round(((d-w)/86400000-3+(w.getDay()+6)%7)/7)).padStart(2,'0'); })();
    dateLabel.textContent = `MSFT · Next week · ${weekNr} · ${label}`;
  }
}

// ── Page 3 — Metrics ───────────────────────────────────────────────────────────
const MODEL_METRICS = {
  xgboost:    { accuracy: 0.5223, precision: 0.5272, recall: 0.5223, f1: 0.5222, label: 'XGBoost (it3)',            days: 471 },
  rf:         { accuracy: 0.4841, precision: 0.4827, recall: 0.4841, f1: 0.4832, label: 'Random Forest (it3)',       days: 471 },
  lr:         { accuracy: 0.4862, precision: 0.4983, recall: 0.4862, f1: 0.4737, label: 'Logistic Regression (it3)', days: 471 },
  rf_weekly:  { accuracy: 0.4375, precision: 0.4481, recall: 0.4308, f1: 0.4254, label: 'Random Forest Weekly',      days: 32  },
  xgb_weekly: { accuracy: 0.3958, precision: 0.4459, recall: 0.3877, f1: 0.3763, label: 'XGBoost Weekly',            days: 48  },
};

function renderMetrics(metrics) {
  const best = metrics?.[0] ?? null;
  ['accuracy','precision','recall','f1'].forEach(key => {
    const el = document.getElementById(`m-${key}`);
    if (el && best?.[key] != null) el.textContent = best[key].toFixed(2);
  });
}

function applyModelSelection(key) {
  const m = MODEL_METRICS[key] || MODEL_METRICS.xgb_weekly;
  const correct = Math.round(m.accuracy * m.days);
  document.getElementById('m-accuracy').textContent  = m.accuracy.toFixed(4);
  document.getElementById('m-precision').textContent = m.precision.toFixed(4);
  document.getElementById('m-recall').textContent    = m.recall.toFixed(4);
  document.getElementById('m-f1').textContent        = m.f1.toFixed(4);
  const accSub = document.querySelector('#m-accuracy')?.closest('.tile')?.querySelector('.tile-sub');
  if (accSub) accSub.textContent = `${correct} / ${m.days} correct`;
}

function modelKeyFromName(name) {
  if (!name) return 'xgb_weekly';
  const n = name.toLowerCase();
  if (n.includes('xgboost') && n.includes('weekly')) return 'xgb_weekly';
  if (n.includes('xgb_weekly'))                      return 'xgb_weekly';
  if (n.includes('rf_weekly') || (n.includes('random') && n.includes('weekly'))) return 'rf_weekly';
  if (n.includes('xgb') || n.includes('xgboost'))   return 'xgboost';
  if (n.includes('random') || n.includes('forest') || n.includes('rf')) return 'rf';
  if (n.includes('logistic') || n.includes('lr'))   return 'lr';
  return 'xgb_weekly';
}

function setActiveModel(modelName) {
  const key = modelKeyFromName(modelName);
  applyModelSelection(key);
  const nameEl = document.getElementById('active-model-name');
  if (nameEl && modelName) nameEl.textContent = modelName;
  // Home tile
  const tileModel = document.getElementById('tile-model-name');
  const tileSub   = tileModel?.closest('.tile')?.querySelector('.tile-sub');
  if (tileModel && modelName) tileModel.textContent = modelName;
  if (tileSub)  tileSub.textContent = MODEL_METRICS[key]?.label ?? modelName;
}

function initModelSelect() {}

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
  historyData  = data;
  filteredData = data;
  viewStart    = 0;
  viewEnd      = data.length - 1;
  const latest = data.at(-1), prev = data.at(-2);
  updatePeriodBtnAvailability(data);
  renderPrediction(prediction);
  renderKPIs(latest, prev);
  const defPeriod = appSettings.defaultPeriod || '1M';
  const defSize   = PERIOD_WIN_SIZES[defPeriod];
  homeWinSize = (defSize === undefined || !isFinite(defSize)) ? data.length : defSize;
  homeWinEnd  = data.length - 1;
  document.querySelectorAll('#home-period-bar .period-bar-btn').forEach(b =>
    b.classList.toggle('period-bar-active', b.dataset.period === defPeriod)
  );
  drawHomeChart();
  renderHistoryChart(filteredData, overlayState);
  renderOverlayToggles();
  renderReturns(filteredData);
  renderSummaryStats(filteredData);
  updateDateDisplay();
  setPeriod('MAX');
  renderConfusionMatrix();
  renderModelCompare();
  renderFeatureBars();
  renderMetrics(metrics ?? []);
  apiFetch('/api/prediction/history?n=10').then(renderPredictionHistory).catch(() => {});
}

// ── Prediction details modal ───────────────────────────────────────────────────
let lastPrediction = null;

function initModalClosers() {
  document.addEventListener('click', e => {
    const closeBtn = e.target.closest('[data-close-overlay]');
    if (closeBtn) {
      document.getElementById(closeBtn.dataset.closeOverlay)?.classList.remove('settings-open');
      return;
    }
    if (e.target.classList.contains('settings-overlay')) {
      e.target.classList.remove('settings-open');
    }
  });
}

function openPredDetails() {
  const overlay = document.getElementById('pred-details-overlay');
  if (!overlay) return;

  const p    = lastPrediction;
  const isUp = !p || p.direction === 'UP';
  const dir  = p?.direction ?? '–';
  const conf = p?.probability ?? null;
  const color = isUp ? C.accent : C.red;

  document.getElementById('pred-detail-hero').innerHTML = `
    <div class="pred-detail-dir" style="color:${color}">${isUp ? '↑' : '↓'} ${dir}</div>
    <div style="display:flex;gap:32px">
      <div class="pred-detail-meta">
        <div class="pred-detail-label">Confidence</div>
        <div class="pred-detail-val" style="color:${color}">${conf !== null ? conf.toFixed(1) + '%' : '–'}</div>
      </div>
      <div class="pred-detail-meta">
        <div class="pred-detail-label">Prediction date</div>
        <div class="pred-detail-val">${(() => { const d = new Date(); d.setDate(d.getDate()+1); while(d.getDay()===0||d.getDay()===6) d.setDate(d.getDate()+1); return d.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'}); })()}</div>
      </div>
    </div>`;

  document.getElementById('pred-detail-info').innerHTML = `
    <div class="pred-detail-row"><span class="pred-detail-key">Model</span><span class="pred-detail-val2">${p?.model_name ?? 'Random Forest Weekly'}</span></div>
    <div class="pred-detail-row"><span class="pred-detail-key">Features</span><span class="pred-detail-val2">20 technical + peer (MSFT · NVDA · AMZN)</span></div>
    <div class="pred-detail-row"><span class="pred-detail-key">Training data</span><span class="pred-detail-val2">2015 – 2025 · weekly bars</span></div>
    <div class="pred-detail-row"><span class="pred-detail-key">Test accuracy</span><span class="pred-detail-val2">39.58% (19/48 weeks)</span></div>
    <div class="pred-detail-row"><span class="pred-detail-key">Last close</span><span class="pred-detail-val2">${p ? `${CURRENCY_SYMBOLS[appSettings.currency] || '$'}${((p.close ?? 0) * (exchangeRates[appSettings.currency] || 1)).toFixed(appSettings.currency === 'JPY' ? 0 : 2)}` : '–'}</span></div>`;

  overlay.classList.add('settings-open');
}

// ── CSV download modal ─────────────────────────────────────────────────────────
function initCsvModal() {
  const overlay  = document.getElementById('csv-overlay');
  const btnOpen  = document.getElementById('btn-download-csv');
  const btnClose = document.getElementById('csv-close');
  const btnDl    = document.getElementById('csv-download-btn');

  function openCsv() {
    if (historyData.length) {
      document.getElementById('csv-date-from').value = historyData[0].date.slice(0,10);
      document.getElementById('csv-date-to').value   = historyData.at(-1).date.slice(0,10);
      updateCsvRowCount();
    }
    overlay.classList.add('settings-open');
  }

  function updateCsvRowCount() {
    const from = document.getElementById('csv-date-from').value;
    const to   = document.getElementById('csv-date-to').value;
    const rows = historyData.filter(r => r.date >= from && r.date <= to).length;
    const el   = document.getElementById('csv-row-count');
    if (el) el.textContent = `${rows} trading day${rows !== 1 ? 's' : ''} selected`;
  }

  btnOpen?.addEventListener('click', openCsv);
  document.getElementById('csv-date-from')?.addEventListener('change', updateCsvRowCount);
  document.getElementById('csv-date-to')?.addEventListener('change', updateCsvRowCount);

  document.getElementById('csv-format')?.querySelectorAll('.btn-group-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('csv-format').querySelectorAll('.btn-group-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  btnDl?.addEventListener('click', () => {
    const from    = document.getElementById('csv-date-from').value;
    const to      = document.getElementById('csv-date-to').value;
    const prices  = document.getElementById('csv-prices').checked;
    const indic   = document.getElementById('csv-indicators').checked;
    const rets    = document.getElementById('csv-returns').checked;
    const fmt     = document.getElementById('csv-format')?.querySelector('.active')?.dataset.val ?? 'csv';

    const rows = historyData.filter(r => r.date >= from && r.date <= to);

    const r2 = (v) => v != null ? Math.round(v * 100) / 100 : '';

    const clean = rows.map((r, i) => {
      const prev = rows[i - 1];
      const ret  = prev ? r2(((r.close - prev.close) / prev.close) * 100) : '';
      const obj  = { Date: r.date };
      if (prices) { obj['Open ($)'] = r2(r.open); obj['High ($)'] = r2(r.high); obj['Low ($)'] = r2(r.low); obj['Close ($)'] = r2(r.close); obj['Volume'] = r.volume ?? ''; }
      if (indic)  { obj['Gold ($)'] = r2(r.gold_close); obj['Oil ($)'] = r2(r.oil_close); obj['VIX'] = r2(r.vix); }
      if (rets)   { obj['Daily Return (%)'] = ret; }
      return obj;
    });

    if (fmt === 'json') {
      const blob = new Blob([JSON.stringify(clean, null, 2)], { type: 'application/json' });
      triggerDownload(blob, 'msft_report.json');
    } else {
      const headers = Object.keys(clean[0] || {});
      const lines   = clean.map(r => headers.map(h => r[h]).join(','));
      const blob    = new Blob([[headers.join(','), ...lines].join('\r\n')], { type: 'text/csv;charset=utf-8;' });
      triggerDownload(blob, 'msft_report.csv');
    }
    overlay.classList.remove('settings-open');
  });
}

function triggerDownload(blob, filename) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── API client ─────────────────────────────────────────────────────────────────
const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:5000' : '';

async function apiFetch(path) {
  const sep = path.includes('?') ? '&' : '?';
  const res = await fetch(`${API_BASE}${path}${sep}_=${Date.now()}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Init ───────────────────────────────────────────────────────────────────────
function initTheme() {
  const btn = document.getElementById('theme-toggle');
  const saved = localStorage.getItem('theme') ?? 'light';
  document.documentElement.dataset.theme = saved;
  btn.textContent = saved === 'dark' ? '☀' : '☾';

  btn?.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
    btn.textContent = next === 'dark' ? '☀' : '☾';
    // Re-read CSS vars and re-render all SVG charts
    C = getColors();
    if (filteredData.length) {
      drawHomeChart();
      renderHistoryChart(filteredData, overlayState);
      renderReturns(filteredData);
    }
    renderConfusionMatrix();
    renderModelCompare();
    renderFeatureBars();
  });
}

async function init() {
  initNav();
  initTheme();
  C = getColors();
  initModalClosers();
  initSettings();
  initChartInteraction();

  await fetchExchangeRates();

  const [histRes, predRes, metricsRes] = await Promise.all([
    apiFetch('/api/stock/history?days=9999').catch(() => null),
    apiFetch('/api/prediction/latest').catch(() => null),
    apiFetch('/api/model/metrics').catch(() => null),
  ]);

  const data = histRes?.data?.length ? histRes.data : SAMPLE_HISTORY;
  lastPrediction = predRes?.data ?? null;
  renderAll(data, predRes?.data, metricsRes?.data);

  initModelSelect();
  setActiveModel(lastPrediction?.model_name ?? null);
  initHomeInteraction();
  initHistoryInteraction();
  document.getElementById('btn-pred-details')?.addEventListener('click', openPredDetails);
  initCsvModal();
}

document.addEventListener('DOMContentLoaded', init);
