// Reaaliaikaiset 1 min kynttiläkaaviot + botin toteutuneet paperikaupat ja ohitetut signaalit.
// Vain lukeva: tiedot tulevat botin tallentamista avaus-/sulkutapahtumista (/api/kaaviot).
(function () {
  const TOKEN = new URLSearchParams(location.search).get("token") || "";
  const NS = "http://www.w3.org/2000/svg";
  const TZ = "Europe/Helsinki";
  const SLOT = 8, H = 250, PADB = 20, PADT = 10, AXW = 58;
  const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const hm = t => new Intl.DateTimeFormat("fi-FI", {timeZone: TZ, hour: "2-digit", minute: "2-digit"}).format(new Date(t));
  const dhm = t => t == null ? "–" : new Intl.DateTimeFormat("fi-FI", {timeZone: TZ, day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit"}).format(new Date(t));
  const hms = t => new Intl.DateTimeFormat("fi-FI", {timeZone: TZ, hour: "2-digit", minute: "2-digit", second: "2-digit"}).format(new Date(t));
  const num = x => x == null ? "–" : Number(x).toLocaleString("fi-FI", {maximumSignificantDigits: 7});
  const usd = (x, s) => x == null ? "–" : (s && x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toLocaleString("fi-FI", {minimumFractionDigits: 2, maximumFractionDigits: 2}) + " $";
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  const OUT = {tavoite: {txt: "Tavoite", ch: "T", col: "--good"}, stop: {txt: "Stop", ch: "S", col: "--bad"},
    aikaraja: {txt: "15 min aikaraja", ch: "A", col: "--muted"}, "epäselvä": {txt: "Epäselvä (tavoite ja stop samassa kynttilässä)", ch: "?", col: "--warn-line"},
    muu: {txt: "Muu", ch: "M", col: "--muted"}};
  const BOTCOL = ["--s1", "--s2"];

  const store = {get(k, d) { try { const v = localStorage.getItem("kc_" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("kc_" + k, JSON.stringify(v)); } catch (e) {} }};
  let hours = store.get("hours", window.matchMedia("(max-width: 600px)").matches ? 1 : 3);
  let showSkips = store.get("skips", true), DATA = null, lastOk = 0, selected = store.get("selected", {});
  const saveSel = () => store.set("selected", selected);
  const dur = ms_ => { const s = Math.max(0, Math.round(ms_ / 1000)); return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`; };
  const root = document.getElementById("kaaviot");

  root.innerHTML = `
    <div class="kc-controls">
      <div class="kc-win" role="group" aria-label="Aikaikkuna">${[1, 3, 6, 12, 24].map(h => `<button data-h="${h}">${h} h</button>`).join("")}</div>
      <label class="kc-chk"><input type="checkbox" id="kc-skips" checked> Näytä tunnistetut, avaamatta jääneet signaalit</label>
      <span class="kc-upd" id="kc-upd">Ladataan…</span>
    </div>
    <div id="kc-alert"></div>
    <div class="kc-legend">
      <span><svg width="14" height="12"><path d="M7 1 L13 11 L1 11 Z" fill="${cssv("--good")}"/></svg> long avattu</span>
      <span><svg width="14" height="12"><path d="M1 1 L13 1 L7 11 Z" fill="${cssv("--bad")}"/></svg> short avattu</span>
      <span><svg width="14" height="12"><path d="M7 1 L13 11 L1 11 Z" fill="none" stroke="${cssv("--good")}" stroke-width="1.5"/></svg><svg width="14" height="12"><path d="M1 1 L13 1 L7 11 Z" fill="none" stroke="${cssv("--bad")}" stroke-width="1.5"/></svg> tunnistettu, ei avattu</span>
      <span>merkin numero: <b>1</b> = v1.1-T2, <b>2</b> = v2-T2</span>
      <span><svg width="22" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="${cssv("--good")}" stroke-width="1.5" stroke-dasharray="4 3"/></svg> suunniteltu tavoite</span>
      <span><svg width="22" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="${cssv("--bad")}" stroke-width="1.5" stroke-dasharray="4 3"/></svg> suunniteltu stop</span>
      <span><svg width="22" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="${cssv("--s1")}" stroke-width="2"/></svg> avoimen position avaushinta</span>
      <span><svg width="30" height="12"><circle cx="4" cy="6" r="3" fill="${cssv("--s1")}"/><line x1="4" y1="6" x2="24" y2="6" stroke="${cssv("--s1")}" stroke-width="1.5"/><circle cx="24" cy="6" r="5" fill="${cssv("--good")}"/></svg> avaus → toteutunut sulku (aika ja hinta)</span>
      <span>sulun syy: <b style="color:${cssv("--good")}">T</b> tavoite · <b style="color:${cssv("--bad")}">S</b> stop · <b>A</b> 15 min aikaraja · <b style="color:${cssv("--warn-line")}">?</b> epäselvä</span>
    </div>
    <div id="kc-summary"></div>
    <div class="kc-hint">Napauta merkkiä nähdäksesi avausperusteen, kellonajat ja tuloksen. Vieritä kaaviota sivusuunnassa nähdäksesi aiemmat minuutit.</div>
    <div id="kc-charts"></div>`;
  root.querySelectorAll(".kc-win button").forEach(b => b.addEventListener("click", () => { hours = +b.dataset.h; store.set("hours", hours); markWin(); load(true); }));
  root.querySelector("#kc-skips").checked = showSkips;
  root.querySelector("#kc-skips").addEventListener("change", e => { showSkips = e.target.checked; store.set("skips", showSkips); DATA && renderAll(false); });
  function markWin() { root.querySelectorAll(".kc-win button").forEach(b => b.classList.toggle("on", +b.dataset.h === hours)); }
  markWin();

  function sumTable(d, pick) {
    const rows = [];
    d.versions.forEach((v, i) => {
      const s = pick(v);
      if (!s) return;
      ["long", "short"].forEach(side => {
        const x = s[side];
        rows.push(`<tr><td class="l"><span class="sw" style="background:${cssv(BOTCOL[i])}"></span> ${i + 1} · ${esc(v)}</td><td class="l">${side === "long" ? "Long" : "Short"}</td>
          <td>${x.kauppoja}</td><td>${x.tavoite}</td><td>${x.stop}</td><td>${x.aikaraja}</td><td>${x["epäselvä"]}</td><td>${x.avoinna}</td></tr>`);
      });
    });
    return `<div class="tbl"><table><thead><tr><th class="l">Botti</th><th class="l">Suunta</th><th>Suljettuja</th><th>Tavoite</th><th>Stop</th><th>Aikaraja</th><th>Epäselvä</th><th>Avoinna</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
  }
  const coin = s => s.replace("PF_", "").replace("USD", "");
  function summary(d) {
    const note = `<div class="kc-note">Epäselvä = tavoite ja stop osuivat samaan 1 min kynttilään, eikä järjestystä voi tietää. Botin kirjanpidossa se on kirjattu stopiksi (varovainen oletus).</div>`;
    if (!d.switch) return sumTable(d, v => d.summary[v]) + `<div class="kc-note">Koko testijakson luvut.</div>` + note;
    return `<div class="kc-seg"><b>Markkinavaihdon jälkeen</b> (${dhm(d.switch.time)} alkaen: ${d.switch.new.map(coin).join(", ")})</div>`
      + sumTable(d, v => d.seg_summary[v] && d.seg_summary[v]["jälkeen"])
      + `<div class="kc-seg"><b>Ennen markkinavaihtoa</b> (${d.switch.old.map(coin).join(", ")}) – eri kaupankäyntikohteet, ei yhdistetä</div>`
      + sumTable(d, v => d.seg_summary[v] && d.seg_summary[v]["ennen"]) + note;
  }

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  function chartBlock(sym) {
    let b = document.getElementById("kc-" + sym);
    if (b) return b;
    b = document.createElement("div");
    b.className = "kc-chart";
    b.id = "kc-" + sym;
    b.innerHTML = `<div class="kc-head"><b>${esc(sym.replace("PF_", "").replace("USD", "/USD"))}</b> <span class="kc-px"></span> <span class="kc-stale"></span></div>
      <div class="kc-why"></div>
      <div class="kc-open"></div>
      <div class="kc-body"><div class="kc-scroll"></div><svg class="kc-axis" width="${AXW}" height="${H}"></svg></div>
      <div class="kc-detail" hidden></div>`;
    document.getElementById("kc-charts").appendChild(b);
    return b;
  }

  function render(sym, d, keepScroll) {
    const b = chartBlock(sym);
    const sc = b.querySelector(".kc-scroll"), ax = b.querySelector(".kc-axis");
    const atEnd = !keepScroll || sc.scrollLeft + sc.clientWidth >= sc.scrollWidth - 40;
    const prevLeft = sc.scrollLeft;
    const cs = d.candles[sym] || [];
    const t0 = Math.floor((d.generated - d.hours * 3600e3) / 60000) * 60000;
    const tEnd = Math.floor(d.generated / 60000) * 60000;
    const n = Math.round((tEnd - t0) / 60000) + 1;
    const W = n * SLOT + 24;
    const X = t => (t - t0) / 60000 * SLOT + SLOT / 2;       // kynttilän keskikohta
    const XT = t => (t - t0) / 60000 * SLOT;                  // todellinen ajanhetki (kynttilöiden rajat = minuutin vaihde)
    const inWin = t => t >= t0 && t <= tEnd;
    const trades = d.trades.filter(t => t.symbol === sym && t.exit_time >= t0 && t.entry_time <= tEnd);
    const opens = d.opens.filter(t => t.symbol === sym);
    const skips = showSkips ? d.skips.filter(s => s.symbol === sym && inWin(s.time)) : [];
    // hinta-alue: kynttilät + näkyvien kauppojen tasot
    let lo = Infinity, hi = -Infinity;
    cs.forEach(c => { if (c[0] >= t0) { lo = Math.min(lo, c[3]); hi = Math.max(hi, c[2]); } });
    [...trades, ...opens].forEach(t => [t.stop, t.target, t.entry_price, t.exit_price].forEach(p => { if (p != null) { lo = Math.min(lo, p); hi = Math.max(hi, p); } }));
    if (!isFinite(lo)) { lo = 0; hi = 1; }
    const pad = (hi - lo) * 0.08 || hi * 0.001;
    lo -= pad; hi += pad;
    const Y = p => PADT + (hi - p) / (hi - lo) * (H - PADT - PADB);
    const byT = new Map(cs.map(c => [c[0], c]));

    const svg = el("svg", {width: W, height: H, class: "kc-svg"});
    // ruudukko ja aika-akseli
    const step = d.hours <= 1 ? 10 : d.hours <= 3 ? 30 : d.hours <= 6 ? 60 : d.hours <= 12 ? 120 : 180;
    for (let k = 0; k <= 4; k++) el("line", {x1: 0, x2: W, y1: PADT + k * (H - PADT - PADB) / 4, y2: PADT + k * (H - PADT - PADB) / 4, stroke: cssv("--grid")}, svg);
    for (let t = Math.ceil(t0 / (step * 60000)) * step * 60000; t <= tEnd; t += step * 60000) {
      el("line", {x1: X(t), x2: X(t), y1: PADT, y2: H - PADB, stroke: cssv("--grid")}, svg);
      const lab = el("text", {x: X(t), y: H - 6, "text-anchor": "middle", "font-size": 10, fill: cssv("--text-2")}, svg);
      lab.textContent = hm(t);
    }
    // kynttilät (neutraalit värit, jotta long/short-merkit erottuvat)
    const up = cssv("--text-2"), bw = SLOT - 3;
    cs.forEach(c => {
      if (c[0] < t0) return;
      const x = X(c[0]), rising = c[4] >= c[1];
      el("line", {x1: x, x2: x, y1: Y(c[2]), y2: Y(c[3]), stroke: up, "stroke-width": 1}, svg);
      const y1 = Y(Math.max(c[1], c[4])), y2 = Y(Math.min(c[1], c[4]));
      el("rect", {x: x - bw / 2, y: y1, width: bw, height: Math.max(1, y2 - y1),
        fill: rising ? cssv("--surface") : up, stroke: up, "stroke-width": 1}, svg);
    });
    const hits = [];
    const tri = (x, y, side, fill, stroke) => {
      const s = 6;
      const dpath = side === "long" ? `M${x} ${y - s} L${x + s} ${y + s} L${x - s} ${y + s} Z` : `M${x - s} ${y - s} L${x + s} ${y - s} L${x} ${y + s} Z`;
      return el("path", {d: dpath, fill, stroke, "stroke-width": fill === "none" ? 1.6 : 1}, svg);
    };
    const markY = (t, side, k) => {
      const c = byT.get(t);
      const base = c ? (side === "long" ? Y(c[3]) + 12 : Y(c[2]) - 12) : (side === "long" ? H - PADB - 10 : PADT + 10);
      return side === "long" ? base + k * 16 : base - k * 16;
    };
    const stack = new Map();
    const slotK = (t, side) => { const k = `${t}|${side}`; const v = stack.get(k) || 0; stack.set(k, v + 1); return v; };
    const label = (x, y, txt, col) => { const e = el("text", {x, y: y + 4, "font-size": 10, "font-weight": 700, fill: col}, svg); e.textContent = txt; };

    // suunnitellut sulkurajat (katkoviiva) – suljetuilla avauksesta toteutuneeseen sulkuun
    const lvl = (xa, xb, p, col, op) => el("line", {x1: xa, x2: xb, y1: Y(p), y2: Y(p), stroke: cssv(col), "stroke-width": 1.5, "stroke-dasharray": "4 3", opacity: op}, svg);
    trades.forEach(t => {
      const xa = XT(t.entry_time), xb = XT(t.exit_time);
      lvl(xa, xb, t.target, "--good", 0.7);
      lvl(xa, xb, t.stop, "--bad", 0.7);
    });
    const xNow = XT(d.generated);
    opens.forEach(t => {
      const xa = XT(t.entry_time), col = cssv(BOTCOL[t.bot - 1]);
      lvl(xa, W, t.target, "--good", 1);
      lvl(xa, W, t.stop, "--bad", 1);
      el("line", {x1: xa, x2: W, y1: Y(t.entry_price), y2: Y(t.entry_price), stroke: col, "stroke-width": 2}, svg);
      const lab = (p, txt, c) => {
        const tx = el("text", {x: Math.min(xNow + 6, W - 4), y: Y(p) - 4, "font-size": 10, "font-weight": 700, fill: cssv(c), "text-anchor": xNow + 150 > W ? "end" : "start"}, svg);
        tx.textContent = txt;
      };
      lab(t.target, `Tavoite ${num(t.target)} (${t.bot})`, "--good");
      lab(t.stop, `Stop ${num(t.stop)} (${t.bot})`, "--bad");
      // aikarajan hetki pystyviivana
      if (t.time_limit) {
        const xl = XT(t.time_limit);
        if (xl <= W) el("line", {x1: xl, x2: xl, y1: PADT, y2: H - PADB, stroke: cssv("--muted"), "stroke-dasharray": "2 3"}, svg);
      }
    });
    // toteutunut kulku: avauspiste -> sulkupiste
    trades.forEach(t => {
      const col = cssv(BOTCOL[t.bot - 1]);
      el("line", {x1: XT(t.entry_time), y1: Y(t.entry_price), x2: XT(t.exit_time), y2: Y(t.exit_price), stroke: col, "stroke-width": 1.5}, svg);
      el("circle", {cx: XT(t.entry_time), cy: Y(t.entry_price), r: 3, fill: col}, svg);
    });
    opens.forEach(t => el("circle", {cx: XT(t.entry_time), cy: Y(t.entry_price), r: 3, fill: cssv(BOTCOL[t.bot - 1])}, svg));

    // ohitetut signaalit (yhdistetään botit samaan merkkiin)
    const sk = new Map();
    skips.forEach(s => {
      if ([...trades, ...opens].some(t => t.bot === s.bot && t.entry_time === s.time)) return;
      const k = `${s.time}|${s.side}`;
      if (!sk.has(k)) sk.set(k, []);
      sk.get(k).push(s);
    });
    // avatut kaupat
    [...trades, ...opens].forEach(t => {
      if (!inWin(t.entry_time)) return;
      const x = X(t.entry_time), y = markY(t.entry_time, t.side, slotK(t.entry_time, t.side));
      tri(x, y, t.side, cssv(t.side === "long" ? "--good" : "--bad"), cssv("--surface"));
      label(x + 8, y, String(t.bot), cssv("--text"));
      hits.push({x, y, kind: "trade", item: t});
    });
    sk.forEach((arr, k) => {
      const s = arr[0];
      const x = X(s.time), y = markY(s.time, s.side, slotK(s.time, s.side));
      tri(x, y, s.side, "none", cssv(s.side === "long" ? "--good" : "--bad"));
      label(x + 8, y, arr.map(a => a.bot).join(","), cssv("--muted"));
      hits.push({x, y, kind: "skip", item: arr});
    });
    // toteutuneet sulut: todellinen sulkuhetki ja toteutunut sulkuhinta
    trades.forEach(t => {
      if (t.exit_time < t0 || t.exit_time > d.generated + 60000) return;
      const o = OUT[t.outcome] || OUT.muu;
      const x = XT(t.exit_time), y = Y(t.exit_price);
      el("circle", {cx: x, cy: y, r: 6, fill: cssv(o.col), stroke: cssv("--surface"), "stroke-width": 2}, svg);
      label(x + 8, y, o.ch + t.bot, cssv(o.col));
      hits.push({x, y, kind: "trade", item: t});
    });
    // napautusalueet
    hits.forEach((h, i) => {
      const r = el("circle", {cx: h.x, cy: h.y, r: 14, fill: "transparent", style: "cursor:pointer", "data-i": i}, svg);
      r.addEventListener("click", () => { selected[sym] = keyOf(h); saveSel(); showDetail(sym, h); });
    });

    sc.innerHTML = "";
    sc.appendChild(svg);
    // hinta-akseli (kiinteä oikealla)
    ax.innerHTML = "";
    for (let k = 0; k <= 4; k++) {
      const p = hi - (hi - lo) * k / 4, y = PADT + k * (H - PADT - PADB) / 4;
      const tx = el("text", {x: 4, y: y + 4, "font-size": 10, fill: cssv("--text-2")}, ax);
      tx.textContent = num(Number(p.toPrecision(6)));
    }
    const lastC = cs[cs.length - 1];
    if (lastC) {
      const y = Y(lastC[4]);
      el("rect", {x: 0, y: y - 8, width: AXW, height: 16, rx: 3, fill: cssv("--text")}, ax);
      const tx = el("text", {x: 4, y: y + 4, "font-size": 10, "font-weight": 700, fill: cssv("--surface")}, ax);
      tx.textContent = num(Number(lastC[4].toPrecision(6)));
    }
    opens.forEach(t => [[t.target, "--good"], [t.stop, "--bad"]].forEach(([p, c]) => {
      const y = Y(p);
      el("rect", {x: 0, y: y - 8, width: AXW, height: 16, rx: 3, fill: cssv(c)}, ax);
      const tx = el("text", {x: 4, y: y + 4, "font-size": 10, "font-weight": 700, fill: "#fff"}, ax);
      tx.textContent = num(Number(p.toPrecision(6)));
    }));
    sc.scrollLeft = atEnd ? sc.scrollWidth : prevLeft;
    const wb = b.querySelector(".kc-why");
    wb.innerHTML = whyBlock(sym, d);
    const det = wb.querySelector("details");
    if (det) det.addEventListener("toggle", () => { openWhy[sym] = det.open; store.set("openWhy", openWhy); });
    b.querySelector(".kc-open").innerHTML = opens.map(t => `<div class="kc-orow">
      <b class="${t.side === "long" ? "side-long" : "side-short"}">${t.side === "long" ? "LONG" : "SHORT"} ${t.bot}</b>
      avattu ${hm(t.entry_time)} @ ${num(t.entry_price)} ·
      <span style="color:${cssv("--good")}">tavoite ${num(t.target)}</span> ·
      <span style="color:${cssv("--bad")}">stop ${num(t.stop)}</span> ·
      aikaraja ${t.time_limit ? hm(t.time_limit) : "–"} (<span class="kc-cd" data-tl="${t.time_limit || ""}"></span>) ·
      ennen kuluja <b class="${t.gross_now > 0 ? "pos" : t.gross_now < 0 ? "neg" : ""}">${usd(t.gross_now, true)}</b> ·
      kulujen jälkeen <b class="${t.net_now > 0 ? "pos" : t.net_now < 0 ? "neg" : ""}">${usd(t.net_now, true)}</b> <span class="kc-muted">(arvio nykyhinnalla)</span></div>`).join("");
    tickCountdowns();
    // otsikko ja tuoreus
    const lc = d.last_candle[sym];
    b.querySelector(".kc-px").textContent = lastC ? `${num(lastC[4])} · viimeisin kynttilä ${hm(lc)}` : "ei dataa";
    const stale = !lc || d.generated - lc > 3 * 60000;
    b.querySelector(".kc-stale").innerHTML = stale ? `<span class="kc-warn">Markkinadata ei päivity</span>` : "";
    // pidä valittu merkki auki päivityksen yli
    if (selected[sym]) {
      const h = hits.find(h => keyOf(h) === selected[sym]);
      if (h) showDetail(sym, h); else b.querySelector(".kc-detail").hidden = true;
    }
  }

  function keyOf(h) {
    return h.kind === "trade" ? `t|${h.item.bot}|${h.item.id}` : `s|${h.item[0].time}|${h.item[0].side}`;
  }

  function showDetail(sym, h) {
    const box = document.getElementById("kc-" + sym).querySelector(".kc-detail");
    let html = "";
    if (h.kind === "trade") {
      const t = h.item, open = t.exit_time == null;
      const o = OUT[t.outcome] || {};
      html = `<div class="kc-dh"><span class="sw" style="background:${cssv(BOTCOL[t.bot - 1])}"></span> <b>Botti ${t.bot} · ${esc(t.version)}</b> · <b class="${t.side === "long" ? "side-long" : "side-short"}">${t.side === "long" ? "LONG" : "SHORT"}</b> · paperikauppa #${t.id}</div>
        <dl class="kc-dl">
          <dt>Avausperuste</dt><dd>${esc(t.open_reason)}</dd>
          <dt>Signaalikynttilä</dt><dd>${dhm(t.signal_time)} (vahvistui ${t.signal_time ? hm(t.signal_time + 60000) : "–"})</dd>
          <dt>Avaus</dt><dd>${dhm(t.entry_time)}, toteutunut avaushinta <b>${num(t.entry_price)}</b>${t.entry_ref ? ` (kynttilän avaus ${num(t.entry_ref)})` : ""}</dd>
          <dt>Suunnitellut sulkurajat</dt><dd>tavoite ${num(t.target)} · stop ${num(t.stop)} · aikaraja ${hm(t.entry_time + 15 * 60000)} (15 min)</dd>
          ${open ? `
          <dt>Tila</dt><dd><b>Avoinna</b>, aikarajaan <span class="kc-cd" data-tl="${t.time_limit || ""}"></span></dd>
          <dt>Kesto tähän asti</dt><dd>${dur(Date.now() - t.entry_time)}</dd>
          <dt>Nyt ennen kuluja</dt><dd class="${t.gross_now > 0 ? "pos" : t.gross_now < 0 ? "neg" : ""}">${usd(t.gross_now, true)} <span class="kc-muted">(keskihinta ${num(t.price)})</span></dd>
          <dt>Nyt kulujen jälkeen</dt><dd class="${t.net_now > 0 ? "pos" : t.net_now < 0 ? "neg" : ""}">${usd(t.net_now, true)} <span class="kc-muted">(arvio: sulku bid/ask + liukuma, palkkiot, funding tähän asti)</span></dd>` : `
          <dt>Toteutunut sulku</dt><dd>${dhm(t.exit_time)} · <b>${esc(o.txt || t.outcome)}</b> · toteutunut sulkuhinta <b>${num(t.exit_price)}</b></dd>
          <dt>Sulun peruste</dt><dd>${esc(t.reason)}${t.outcome === "tavoite" || t.outcome === "stop" || t.outcome === "epäselvä" ? ` – botti totesi osuman kynttilän ${hm(t.exit_time - 60000)} sulkeutuessa` : ""}</dd>
          <dt>Kesto</dt><dd>${dur(t.exit_time - t.entry_time)}</dd>
          <dt>Tulos ennen kuluja</dt><dd class="${t.gross_move > 0 ? "pos" : t.gross_move < 0 ? "neg" : ""}">${usd(t.gross_move, true)}</dd>
          <dt>Kulut</dt><dd>${usd(-t.costs)} (palkkiot ${usd(-t.fees)}, spread ja liukuma ${usd(-t.spread_slippage)}, funding ${usd(-t.funding)})</dd>
          <dt>Lopullinen tulos</dt><dd class="${t.net > 0 ? "pos" : t.net < 0 ? "neg" : ""}"><b>${usd(t.net, true)}</b></dd>`}
        </dl>`;
    } else {
      const arr = h.item, s = arr[0];
      html = `<div class="kc-dh"><b>Tunnistettu signaali – EI avattu</b> · <b class="${s.side === "long" ? "side-long" : "side-short"}">${s.side === "long" ? "LONG" : "SHORT"}</b></div>
        <dl class="kc-dl"><dt>Signaali</dt><dd>${esc(s.reason)}</dd>
        <dt>Avaus olisi ollut</dt><dd>${dhm(s.time)}</dd>
        ${arr.map(a => `<dt>Botti ${a.bot} · ${esc(a.version)}</dt><dd>${esc(a.why)}</dd>`).join("")}</dl>`;
    }
    box.innerHTML = html + `<button class="kc-close" type="button">Sulje</button>`;
    box.hidden = false;
    tickCountdowns();
    box.querySelector(".kc-close").addEventListener("click", () => { box.hidden = true; delete selected[sym]; saveSel(); });
  }

  function renderAll(keepScroll) {
    const d = DATA;
    document.getElementById("kc-summary").innerHTML = summary(d);
    d.symbols.forEach(s => render(s, d, keepScroll));
  }

  function status() {
    const u = document.getElementById("kc-upd");
    const age = Date.now() - lastOk;
    u.textContent = lastOk ? `Päivitetty ${hms(lastOk)} (10 s välein)` : "Ladataan…";
    const al = [];
    if (DATA) {
      DATA.errors.forEach(e => al.push(e));
      if (DATA.kraken_ok_at && DATA.generated - DATA.kraken_ok_at > 60000) al.push(`Markkinadata ei päivity: viimeisin onnistunut haku Krakenista ${hms(DATA.kraken_ok_at)}.`);
    }
    if (lastOk && age > 45000) al.push(`Sivu ei ole saanut uutta dataa ${Math.round(age / 1000)} sekuntiin.`);
    document.getElementById("kc-alert").innerHTML = al.map(x => `<div class="alert">${esc(x)}</div>`).join("");
  }

  function tickCountdowns() {
    document.querySelectorAll(".kc-cd").forEach(e => {
      const tl = +e.dataset.tl;
      if (!tl) { e.textContent = "–"; return; }
      const left = tl - Date.now();
      e.textContent = left > 0 ? `${dur(left)} jäljellä` : "aikaraja täynnä – botti sulkee seuraavalla kierroksella";
    });
  }
  setInterval(tickCountdowns, 1000);

  const openWhy = store.get("openWhy", {});
  const pct2 = (a, b) => ((b / a - 1) * 100).toLocaleString("fi-FI", {minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: "exceptZero"}) + " %";
  function whyBlock(sym, d) {
    const ex = (d.explain || {})[sym] || [];
    const le = (d.last_bot_event || {})[sym];
    let top;
    if (le && le.length) {
      const e = le[0], side = e.side === "long" ? "LONG" : "SHORT";
      top = `<b>Botin viimeisin signaali:</b> ${hm(e.time)} <b class="${e.side === "long" ? "side-long" : "side-short"}">${side}</b> ${esc(e.reason)} → `
        + le.map(x => `botti ${x.bot}: ${x.why === "avattu" ? "<b>avattu</b>" : "ohitettu – " + esc(x.why)}`).join("; ");
    } else {
      top = `<b>Botin viimeisin signaali:</b> ei signaaleja valitussa aikaikkunassa${d.switch ? ` (vaihdon ${hm(d.switch.time)} jälkeen)` : ""}.`;
    }
    const sumObs = x => {
      if (!x.obs.length) return `ei tunnistettua kuviota (trendi ${x.trend}, ${x.trend_move > 0 ? "+" : ""}${x.trend_move})`;
      return x.obs.map(o => o.signal ? `<b>${esc(o.name)}: SIGNAALI ${o.side === "long" ? "LONG" : "SHORT"}</b>`
        : `${esc(o.name)}: <span class="kc-muted">${esc(o.why.join("; "))}</span>`).join("<br>");
    };
    const last = ex[ex.length - 1];
    const lastTxt = last ? `<b>Viimeisin suljettu kynttilä ${hm(last.t)}:</b> ${sumObs(last)}` : "";
    const rows = ex.slice().reverse().map(x => `<tr><td>${hm(x.t)}</td><td class="${x.c > x.o ? "pos" : x.c < x.o ? "neg" : ""}">${pct2(x.o, x.c)}</td>
      <td>${x.rel}×</td><td>${x.vol}×</td><td class="l">${x.trend} (${x.trend_move > 0 ? "+" : ""}${x.trend_move})</td>
      <td class="l kc-wrap">${sumObs(x)}${x.near.length ? `<br><span class="kc-muted">lähellä: ${x.near.map(n => `${esc(n.name)} (${n.side}) – puuttui ${esc(n.missing.join("; "))}`).join(" · ")}</span>` : ""}</td></tr>`).join("");
    return `<div>${top}</div><div>${lastTxt}</div>
      <details data-sym="${sym}" ${openWhy[sym] ? "open" : ""}><summary>Viimeiset ${ex.length} kynttilää: havainnot ja hylkäyssyyt</summary>
      <div class="tbl"><table><thead><tr><th>Aika</th><th>Muutos</th><th>Koko</th><th>Volyymi</th><th class="l">Trendi (10 min)</th><th class="l">Havainto ja syy</th></tr></thead><tbody>${rows}</tbody></table></div>
      <div class="kc-note">Laskettu seurannassa botin omalla T2-tunnistus- ja signaalikoodilla samoista Krakenin kynttilöistä. Signaaliehdot: kaupankäyntikuvio (vasara, käänteinen vasara, nouseva/laskeva peittävä, tähdenlento, hirttäytyjä), kuvion vaatima edeltävä trendi, pisteet ≥ 2 ja volyymi ≥ 1,2× 20 min keskiarvo. Kulusuodatin ja tappiorajat tarkistetaan vasta signaalin jälkeen, ja niiden tulos näkyy botin signaalirivillä.</div></details>`;
  }

  let busy = false;
  async function load(reset) {
    if (busy) return;
    busy = true;
    try {
      const r = await fetch(`/api/kaaviot?token=${encodeURIComponent(TOKEN)}&tunnit=${hours}`, {cache: "no-store"});
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      DATA = await r.json();
      lastOk = Date.now();
      renderAll(!reset);
    } catch (e) {
      document.getElementById("kc-alert").innerHTML = `<div class="alert">Kaaviodatan haku epäonnistui: ${esc(e.message)}</div>`;
    } finally {
      busy = false;
      status();
    }
  }
  load(true);
  setInterval(load, 10000);
  setInterval(status, 5000);
})();
