/*
 * Warehouse Performance Agent — executive dashboard (read-only results view;
 * there is nothing to configure).
 *
 * Used in two places:
 *   - the Workspace Manager sidebar (config.py): showWarehousePerfAgent('<ws>')
 *     renders into #contentArea;
 *   - the standalone page /warehouse-performance?workspace_id=<ws>.
 * Every dynamic value is HTML-escaped before insertion.
 */
(function () {
  "use strict";
  var API = "/api/v0/warehouse_perf";
  var CLS = {
    significant_deterioration: ["Significant deterioration", "#c53030", "#fff5f5"],
    deterioration: ["Deterioration", "#c05621", "#fffaf0"],
    normal_variation: ["Normal variation", "#4a5568", "#f7fafc"],
    improvement: ["Improvement", "#2f855a", "#f0fff4"],
    insufficient_data: ["Insufficient data", "#718096", "#edf2f7"],
    above_normal: ["Above normal", "#2b6cb0", "#ebf8ff"],
    below_normal: ["Below normal", "#2b6cb0", "#ebf8ff"]
  };
  var DELIVERY = {
    sent: "Sent",
    not_required: "Not sent — no significant deterioration",
    not_sent_no_recipients: "Not sent — no saved recipients",
    suppressed_kill_switch: "Not sent — email is switched off globally",
    duplicate_skipped: "Already emailed earlier for this problem (see Last email sent)",
    failed: "Sending failed",
    not_sent_daily_cap: "Not sent — daily automatic email limit reached",
    not_sent_auto_email_off: "Not sent — automatic email is off for this deployment"
  };

  function esc(v) {
    return String(v === null || v === undefined ? "" : v)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function num(v, unit) {
    if (v === null || v === undefined) return "n/a";
    var n = Number(v);
    var s = Math.abs(n) >= 100 || n === Math.round(n) ? Math.round(n).toLocaleString() : n.toFixed(1);
    return s + (unit ? " " + unit : "");
  }
  function pct(p) {
    if (p === null || p === undefined) return "n/a";
    return (p > 0 ? "+" : p < 0 ? "−" : "") + Math.abs(p).toFixed(1) + "%";
  }
  function when(iso) {
    if (!iso) return "—";
    var d = new Date(iso);
    return isNaN(d.getTime()) ? esc(iso) : esc(d.toLocaleString());
  }
  function badge(c) {
    var x = CLS[c] || [c || "—", "#4a5568", "#f7fafc"];
    return '<span class="wpa-badge" style="color:' + x[1] + ';background:' + x[2] + ';border-color:' + x[1] + '33">' +
      esc(x[0]) + "</span>";
  }
  function api(method, path, payload) {
    var opts = { method: method, headers: { "Content-Type": "application/json" }, credentials: "same-origin" };
    if (payload !== undefined) opts.body = JSON.stringify(payload);
    return fetch(API + path, opts).then(function (r) {
      return r.json().catch(function () { return { type: "error", error: "HTTP " + r.status }; });
    });
  }

  var CSS = "" +
    ".wpa{font-family:Segoe UI,Arial,sans-serif;color:#1a202c}" +
    ".wpa h3{margin:0;font-size:22px}.wpa h4{margin:0 0 10px;font-size:15px;color:#2d3748}" +
    ".wpa-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:14px}" +
    ".wpa-meta{color:#718096;font-size:13px;margin-top:4px}.wpa-meta b{color:#2d3748;font-weight:600}" +
    ".wpa-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}" +
    ".wpa-btns{display:flex;gap:8px;flex-wrap:wrap;align-items:center}" +
    /* scoped + !important: the host page's global button/link styles must not leak in */
    ".wpa .wpa-btns .wpa-btn{display:inline-flex !important;align-items:center;gap:7px;box-sizing:border-box;" +
    "height:36px;padding:0 14px !important;margin:0 !important;border:1px solid #2b6cb0 !important;" +
    "border-radius:6px !important;background:#fff !important;color:#2b6cb0 !important;font:600 13px/1 Segoe UI,Arial,sans-serif !important;" +
    "text-decoration:none !important;cursor:pointer;white-space:nowrap;box-shadow:none !important;width:auto !important;" +
    "transition:background .15s,color .15s}" +
    ".wpa .wpa-btns .wpa-btn:hover{background:#ebf4ff !important}" +
    ".wpa .wpa-btns .wpa-btn.primary{background:#2b6cb0 !important;color:#fff !important}" +
    ".wpa .wpa-btns .wpa-btn.primary:hover{background:#245a92 !important}" +
    ".wpa .wpa-btns .wpa-btn:disabled{opacity:.55;cursor:default}" +
    ".wpa .wpa-btns .wpa-btn i{font-size:13px;color:inherit !important;margin:0 !important}" +
    ".wpa .wpa-chk{display:flex !important;align-items:center;gap:8px;margin:6px 0;font-size:13px;cursor:pointer}" +
    ".wpa .wpa-chk input{width:auto !important;height:auto !important;margin:0 !important;accent-color:#2b6cb0}" +
    ".wpa .wpa-field{height:36px !important;padding:0 10px !important;border:1px solid #cbd5e0 !important;" +
    "border-radius:6px !important;font-size:13px !important;width:230px !important;box-sizing:border-box;margin:0 !important}" +
    ".wpa .wpa-sub{font-size:13px;font-weight:600;color:#2d3748;margin:12px 0 4px}" +
    ".wpa-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:14px}" +
    ".wpa-card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px}" +
    ".wpa-kpi-label{font-size:12px;color:#718096;text-transform:uppercase;letter-spacing:.04em}" +
    ".wpa-kpi-value{font-size:26px;font-weight:600;margin:6px 0 2px}.wpa-kpi-sub{font-size:12px;color:#4a5568}" +
    ".wpa-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px;margin-bottom:14px}" +
    ".wpa table{width:100%;border-collapse:collapse;font-size:13px}.wpa th{text-align:left;color:#718096;font-weight:600;" +
    "border-bottom:1px solid #e2e8f0;padding:6px 4px}.wpa td{border-bottom:1px solid #f1f5f9;padding:6px 4px}" +
    ".wpa-badge{display:inline-block;border:1px solid;border-radius:999px;padding:1px 8px;font-size:11px;white-space:nowrap}" +
    ".wpa-up{color:#2f855a}.wpa-down{color:#c53030}.wpa-muted{color:#718096;font-size:12px}" +
    ".wpa-warn{background:#fffaf0;border:1px solid #f6ad55;border-radius:8px;padding:8px 12px;margin-bottom:12px;font-size:13px}" +
    ".wpa-finding{font-size:15px;line-height:1.55}.wpa ul{margin:6px 0 0 18px;padding:0}.wpa li{margin:3px 0;font-size:13px}" +
    ".wpa-bar{height:6px;background:#edf2f7;border-radius:3px;overflow:hidden;margin-top:3px}" +
    ".wpa-bar span{display:block;height:100%;background:#e53e3e}" +
    ".wpa-agents{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin:0 0 12px}" +
    ".wpa-agent{border:1px solid #e2e8f0;border-radius:8px;padding:8px 10px;background:#f8fafc}" +
    ".wpa-agent b{font-size:13px}.wpa-agent .wpa-muted{display:block;margin-top:3px;line-height:1.4}" +
    ".wpa-step{display:inline-block;width:20px;height:20px;border-radius:50%;background:#2b6cb0;color:#fff;" +
    "font-size:11px;font-weight:700;text-align:center;line-height:20px;margin-right:6px}" +
    ".wpa-cause{border:1px solid #e2e8f0;border-left:5px solid #a0aec0;border-radius:8px;padding:10px 12px;margin:8px 0}" +
    ".wpa-cause-title{font-size:14px;font-weight:600;margin:2px 0 4px}" +
    ".wpa-tag{font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:.04em}" +
    ".wpa-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}" +
    /* charts: validated reference palette on the white card surface; text always in ink tokens */
    ".wpa-svg{display:block;width:100%;height:auto;overflow:visible}" +
    ".wpa-svg .wpa-hit{fill:transparent;cursor:default;outline:none}" +
    ".wpa-svg .wpa-hit:hover,.wpa-svg .wpa-hit:focus{fill:rgba(11,11,11,.05)}" +
    ".wpa-legend{display:flex;flex-wrap:wrap;gap:4px 14px;margin:4px 0 6px;font-size:12px;color:#52514e}" +
    ".wpa-key{display:inline-flex;align-items:center;gap:6px}" +
    ".wpa-sw{display:inline-block;width:10px;height:10px;border-radius:2px}.wpa-sw.line{width:14px;height:2px;border-radius:1px}" +
    ".wpa-ans{font-size:17px;font-weight:600;color:#1a202c;line-height:1.4;margin:0 0 2px}" +
    ".wpa-ans-sub{font-size:13px;color:#4a5568;margin:0 0 10px;line-height:1.45}" +
    ".wpa-help{margin:8px 0 2px;font-size:12.5px;color:#4a5568}.wpa-help summary{cursor:pointer;color:#2b6cb0;font-weight:600}" +
    ".wpa-help p{margin:6px 0;line-height:1.5}.wpa-help li{font-size:12.5px}" +
    ".wpa-dv-row{display:grid;grid-template-columns:minmax(80px,30%) 1fr 165px;align-items:center;gap:10px;padding:5px 4px;border-radius:4px;outline:none}" +
    ".wpa-dv-row:hover,.wpa-dv-row:focus,.wpa-ev-row:hover,.wpa-ev-row:focus{background:#f4f6f8}" +
    ".wpa-dv-name{font-size:14px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wpa-dv-track{position:relative;height:18px}" +
    ".wpa-dv-zero{position:absolute;top:-4px;bottom:-4px;width:1px;background:#898781}" +
    ".wpa-dv-bar{position:absolute;top:0;height:18px;border-radius:4px}" +
    ".wpa-dv-val{text-align:right;font-variant-numeric:tabular-nums;line-height:1.2}" +
    ".wpa-dv-val b{display:block;font-size:15px;color:#1a202c}.wpa-dv-val b.wpa-down{color:#c53030}.wpa-dv-val b.wpa-up{color:#2b6cb0}" +
    ".wpa-dv-val span{display:block;font-size:11px;color:#718096;white-space:nowrap}" +
    ".wpa-share{display:flex;gap:2px;height:24px;margin:6px 0 2px}" +
    ".wpa-seg{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;min-width:3px;outline:none}" +
    ".wpa-share .wpa-seg:first-child{border-radius:4px 0 0 4px}.wpa-share .wpa-seg:last-child{border-radius:0 4px 4px 0}" +
    ".wpa-ev-row{display:grid;grid-template-columns:minmax(160px,44%) 1fr;gap:12px;align-items:center;padding:6px 4px;" +
    "border-bottom:1px solid #f1f5f9;border-radius:4px;outline:none}" +
    ".wpa-ev-name{font-size:13px;line-height:1.35}" +
    ".wpa-ev-bar{display:grid;grid-template-columns:1fr 46px;align-items:center;gap:6px;margin:2px 0}" +
    ".wpa-ev-track{height:10px}.wpa-ev-track span{display:block;height:10px;border-radius:0 4px 4px 0}" +
    ".wpa-ev-bar em{font-style:normal;font-size:11px;color:#4a5568;font-variant-numeric:tabular-nums}" +
    ".wpa-pill{display:inline-block;font-size:11px;border-radius:999px;padding:0 7px;border:1px solid;margin-right:4px;white-space:nowrap}" +
    ".wpa-pill.found{color:#9b2c2c;background:#fff5f5;border-color:#feb2b2}.wpa-pill.ok{color:#276749;background:#f0fff4;border-color:#9ae6b4}" +
    ".wpa-table{margin-top:6px;font-size:12px}.wpa-table summary{cursor:pointer;color:#2b6cb0}" +
    ".wpa-tip{position:fixed;z-index:10000;display:none;pointer-events:none;background:#fff;color:#0b0b0b;" +
    "border:1px solid rgba(11,11,11,.12);box-shadow:0 6px 18px rgba(0,0,0,.14);border-radius:6px;padding:6px 9px;" +
    "font-size:12px;max-width:340px;line-height:1.4}.wpa-tip strong{display:block;font-size:13px}.wpa-tip div{color:#52514e}";

  function kpiCard(k, key) {
    if (!k) return "";
    if (key !== "overall" && k.status && k.status !== "ok" && k.status !== "insufficient_data") return "";
    var value = key === "overall" ? (k.value === null || k.value === undefined ? "n/a" : pct(k.value)) : num(k.value);
    var sub = key === "overall" ? "vs historical baseline" :
      (k.baseline !== null && k.baseline !== undefined ? "baseline " + num(k.baseline) + " · " + pct(k.pct_diff) :
        (k.reason || "no baseline yet"));
    return '<div class="wpa-card"><div class="wpa-kpi-label">' + esc(k.label) + "</div>" +
      '<div class="wpa-kpi-value">' + esc(value) + "</div>" +
      '<div class="wpa-kpi-sub">' + esc(sub) + "</div><div style='margin-top:6px'>" + badge(k.classification) +
      (k.freshness_warning ? ' <span class="wpa-muted">⚠ recent data missing</span>' : "") + "</div></div>";
  }

  function changesTable(changes) {
    if (!changes || !changes.length) return '<p class="wpa-muted">No metric could be compared with history yet.</p>';
    var rows = changes.slice(0, 8).map(function (c) {
      var arrow = c.direction === "up" ? "▲" : c.direction === "down" ? "▼" : "■";
      var tone = c.favourable === true ? "wpa-up" : c.favourable === false && c.classification !== "normal_variation" ? "wpa-down" : "";
      return "<tr><td>" + esc(c.label) + "</td><td>" + esc(num(c.actual, c.unit)) + "</td><td>" + esc(num(c.baseline, c.unit)) +
        '</td><td class="' + tone + '">' + arrow + " " + esc(pct(c.pct_diff)) + "</td><td>" + badge(c.classification) + "</td></tr>";
    }).join("");
    return "<table><thead><tr><th>Metric</th><th>Current</th><th>Baseline</th><th>Change</th><th></th></tr></thead><tbody>" +
      rows + "</tbody></table>";
  }

  // ---------------------------------------------------------------- charts
  // Colours: today = blue (series 1); normal = grey; worse = red, better = blue, normal range = grey
  // (diverging blue/red with a grey midpoint); causes = categorical slots 1-3. Values and labels use ink.
  var C = { today: "#2a78d6", worse: "#e34948", better: "#2a78d6", normal: "#c3c2b7", line: "#52514e",
    grid: "#e1e0d9", axis: "#c3c2b7", muted: "#898781", surface: "#ffffff", rest: "#e1e0d9",
    cause: ["#2a78d6", "#eb6834", "#1baf7a"], causeInk: ["#ffffff", "#0b0b0b", "#0b0b0b"] };

  function tipAttrs(value, label) {
    return ' tabindex="0" data-tip-v="' + esc(value) + '" data-tip="' + esc(label || "") + '"';
  }
  function legend(items) {
    return '<div class="wpa-legend">' + items.map(function (it) {
      return '<span class="wpa-key"><span class="wpa-sw' + (it.kind ? " " + it.kind : "") + '" style="background:' +
        it.color + '"></span>' + esc(it.text) + "</span>";
    }).join("") + "</div>";
  }
  function hh(h) { return (h < 10 ? "0" : "") + h + ":00"; }
  function niceStep(v, ticks) {        // round steps (1, 2, 5 x 10^k) with ~8% headroom: 0/5/10/15/20, never 3.8/11
    var raw = Math.max(v || 0, 1e-9) * 1.08 / ticks, p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
    return [1, 2, 5, 10].map(function (m) { return m * p; }).filter(function (x) { return x >= raw; })[0];
  }
  function colPath(x, y, w, h) {          // column: 4px rounded data end, square at the baseline
    if (h <= 0.5) return "";
    var r = Math.min(4, w / 2, h);
    return "M" + x + "," + (y + h) + "V" + (y + r) + "Q" + x + "," + y + " " + (x + r) + "," + y + "H" + (x + w - r) +
      "Q" + (x + w) + "," + y + " " + (x + w) + "," + (y + r) + "V" + (y + h) + "Z";
  }
  function stateOf(cls) {
    return cls === "significant_deterioration" || cls === "deterioration" ? "worse" : cls === "improvement" ? "better" : "normal";
  }

  function hourlyChart(c) {
    var pts = (c && c.points) || [], first = 0;
    while (first < pts.length - 1 && !pts[first].actual && !pts[first].baseline) first++;
    pts = pts.slice(first);
    if (pts.length < 2) return '<p class="wpa-muted">Not enough hours yet to draw the day.</p>';
    var W = 600, H = 250, L = 56, R = 8, T = 24, B = 44, pw = W - L - R, ph = H - T - B;
    var step = niceStep(Math.max.apply(null, pts.map(function (p) { return Math.max(p.actual || 0, p.baseline || 0); })), 4);
    var max = step * 4;
    var band = pw / pts.length, bw = Math.min(24, band * 0.6), base = T + ph;
    function y(v) { return base - (v || 0) / max * ph; }
    function xc(i) { return L + band * i + band / 2; }
    var s = ['<svg class="wpa-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(c.title) + '">'];
    var startIdx = -1, sh = c.start ? parseInt(c.start, 10) : null;
    if (sh !== null) pts.forEach(function (p, i) { if (startIdx < 0 && p.hour >= sh) startIdx = i; });
    if (startIdx >= 0) {
      var sx = L + band * startIdx;
      s.push('<rect x="' + sx + '" y="' + T + '" width="' + (L + pw - sx) + '" height="' + ph + '" fill="' + C.worse + '" fill-opacity="0.08"/>');
      s.push('<text x="' + (sx + 4) + '" y="' + (T - 8) + '" font-size="12" font-weight="600" fill="#52514e">Problem from ' + esc(c.start) + "</text>");
    }
    for (var k = 0; k <= 4; k++) {
      var yy = y(step * k);
      s.push('<line x1="' + L + '" x2="' + (L + pw) + '" y1="' + yy + '" y2="' + yy + '" stroke="' + (k ? C.grid : C.axis) + '" stroke-width="1"/>');
      s.push('<text x="' + (L - 6) + '" y="' + (yy + 4) + '" font-size="11" text-anchor="end" fill="' + C.muted + '">' + esc(num(step * k)) + "</text>");
    }
    // axis titles: across = hour of the day, up = what is counted
    s.push('<text x="' + (L + pw / 2) + '" y="' + (H - 6) + '" font-size="12" font-weight="600" text-anchor="middle" fill="#52514e">Hour of the day →</text>');
    s.push('<text transform="rotate(-90)" x="' + (-(T + ph / 2)) + '" y="14" font-size="12" font-weight="600" text-anchor="middle" fill="#52514e">' +
      esc((c.y_title || "Per hour") + " →") + "</text>");
    var every = pts.length > 14 ? 2 : 1;
    pts.forEach(function (p, i) {
      s.push('<path d="' + colPath(xc(i) - bw / 2, y(p.actual), bw, base - y(p.actual)) + '" fill="' + C.today + '"/>');
      if (i % every === 0) s.push('<text x="' + xc(i) + '" y="' + (base + 16) + '" font-size="11" text-anchor="middle" fill="' + C.muted + '">' + hh(p.hour) + "</text>");
    });
    s.push('<path d="' + pts.map(function (p, i) { return (i ? "L" : "M") + xc(i) + "," + y(p.baseline); }).join("") +
      '" fill="none" stroke="' + C.line + '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>');
    pts.forEach(function (p, i) {
      s.push('<circle cx="' + xc(i) + '" cy="' + y(p.baseline) + '" r="4" fill="' + C.line + '" stroke="' + C.surface + '" stroke-width="2"/>');
    });
    pts.forEach(function (p, i) {        // hover/focus target: the whole hour, not the 2px line
      s.push('<rect class="wpa-hit" x="' + (L + band * i) + '" y="' + T + '" width="' + band + '" height="' + ph + '"' +
        tipAttrs("Today " + num(p.actual) + " · normal " + num(p.baseline), hh(p.hour) + "–" + hh(p.hour + 1)) + "/>");
    });
    s.push("</svg>");
    return legend([{ color: C.today, text: "Today" }, { kind: "line", color: C.line, text: "Normal for this weekday and hour" }]) +
      s.join("") + '<details class="wpa-table"><summary>Show as table</summary><table><thead><tr><th>Hour</th><th>Today</th>' +
      "<th>Normal</th></tr></thead><tbody>" + pts.map(function (p) {
        return "<tr><td>" + hh(p.hour) + "</td><td>" + esc(num(p.actual)) + "</td><td>" + esc(num(p.baseline)) + "</td></tr>";
      }).join("") + "</tbody></table></details>";
  }

  // Bars for management: plain colours (red = problem, grey = normal ups and downs, blue = better), whole
  // percentages, and "today X · normally Y" beside every bar. How red is decided sits in a fold-out, read off
  // each row's usual range (how far it moves on normal days); only where that rule decided the colour.
  function bandOf(x) {
    var ok = ["significant_deterioration", "deterioration", "improvement", "normal_variation"].indexOf(x.classification) >= 0;
    return ok && !x.demand_adjusted && x.usual_range_pct ? x.usual_range_pct : null;
  }
  function pct0(p) {
    if (p === null || p === undefined) return "n/a";
    var r = Math.round(p);
    return (r > 0 ? "+" : r < 0 ? "−" : "") + Math.abs(r) + "%";
  }
  function cleanName(n) {                 // "Picking (pick) (301)" -> "Picking": codes mean nothing to a reader
    n = String(n || "").replace(/\s*\(\d+\)\s*$/, "");
    var m = n.match(/^(\S+)\s*\(([^)]+)\)$/);
    if (m && m[1].toLowerCase().indexOf(m[2].toLowerCase()) === 0) n = m[1];
    return n.charAt(0).toUpperCase() + n.slice(1);
  }
  function answer(text, sub) {
    return '<div class="wpa-ans">' + esc(text) + "</div>" + (sub ? '<div class="wpa-ans-sub">' + esc(sub) + "</div>" : "");
  }
  function colourHelp(rows) {
    var notes = rows.filter(function (r) { return r.band; }).slice(0, 6).map(function (r) {
      return "<li><b>" + esc(r.name) + "</b>: today " + esc(pct0(r.pct)) + " — normal days range from " +
        esc(pct0(r.band[0])) + " to " + esc(pct0(r.band[1])) + (r.state === "worse" ? " → <b>red</b>" :
          r.state === "better" ? " → blue" : " → grey") + "</li>";
    });
    return '<details class="wpa-help"><summary>How do we decide what is red?</summary><p>Every number goes up and down a ' +
      "little from day to day. We compare today with the same weekday over the last five weeks, at the same time of day. " +
      "A bar is <b>red</b> only when today is clearly outside the range those normal days usually stay in (and at least 5% worse). " +
      "Smaller changes stay <b>grey</b> — normal ups and downs, nothing to act on.</p>" +
      (notes.length ? "<ul>" + notes.join("") + "</ul>" : "") + "</details>";
  }
  function divBars(rows) {
    rows = (rows || []).filter(function (r) { return r.pct !== null && r.pct !== undefined; });
    if (!rows.length) return '<p class="wpa-muted">No comparison with normal yet.</p>';
    var neg = Math.max.apply(null, rows.map(function (r) { return r.pct < 0 ? -r.pct : 0; }));
    var pos = Math.max.apply(null, rows.map(function (r) { return r.pct > 0 ? r.pct : 0; }));
    var span = (neg + pos) || 1, zero = neg / span * 100;   // only the sides that are used
    var states = {};
    var html = '<div class="wpa-dv">' + rows.map(function (r) {
      states[r.state] = true;
      var w = Math.abs(r.pct) / span * 100;
      var pos_ = r.pct < 0 ? "right:" + (100 - zero).toFixed(1) + "%" : "left:" + zero.toFixed(1) + "%";
      var tip = "Today " + r.today + " · normally " + r.normal + (r.band ? " · normal days range " + pct0(r.band[0]) + " to " + pct0(r.band[1]) : "");
      return '<div class="wpa-dv-row"' + tipAttrs(tip, r.tip || r.name) + ">" +
        '<div class="wpa-dv-name" title="' + esc(r.full || r.name) + '">' + esc(r.name) + "</div>" +
        '<div class="wpa-dv-track"><span class="wpa-dv-zero" style="left:' + zero.toFixed(1) + '%"></span>' +
        '<span class="wpa-dv-bar" style="' + pos_ + ";width:" + w.toFixed(1) + "%;background:" + C[r.state] + '"></span></div>' +
        '<div class="wpa-dv-val"><b class="' + (r.state === "worse" ? "wpa-down" : r.state === "better" ? "wpa-up" : "") + '">' +
        esc(pct0(r.pct)) + "</b><span>today " + esc(r.today) + " · normally " + esc(r.normal) + "</span></div></div>";
    }).join("") + "</div>";
    var keys = [];
    if (states.worse) keys.push({ color: C.worse, text: "Problem — worse than on normal days" });
    if (states.normal) keys.push({ color: C.normal, text: "Normal ups and downs" });
    if (states.better) keys.push({ color: C.better, text: "Better than normal" });
    return html + legend(keys) + (rows.some(function (r) { return r.band; }) ? colourHelp(rows) : "");
  }
  function barRow(x, name, unit) {
    return { name: name, full: x.name || x.label, pct: x.pct_diff, state: stateOf(x.classification), band: bandOf(x),
      today: num(x.actual, unit === "minutes" ? "min" : ""), normal: num(x.baseline, unit === "minutes" ? "min" : ""), tip: name };
  }

  function warehouseChart(w) {
    return divBars(((w && w.comparison) || []).map(function (x) { return barRow(x, x.name); }));
  }

  function stepChart(p) {
    return divBars((p.comparison || []).map(function (x) { return barRow(x, cleanName(x.name)); }));
  }

  function changesChart(changes) {
    var rows = (changes || []).slice(0, 8).map(function (c) { return barRow(c, c.label, c.unit); });
    return divBars(rows) + '<details class="wpa-table"><summary>Show as table</summary>' + changesTable(changes) + "</details>";
  }

  // ---- one-sentence answers, written for someone reading only the first line of each card
  function whenAnswer(c, tw) {
    if (!c || !c.start) return null;
    var sh = parseInt(c.start, 10), a = 0, b = 0;
    (c.points || []).forEach(function (p) { if (p.hour >= sh) { a += p.actual || 0; b += p.baseline || 0; } });
    var ongoing = !tw || tw.ongoing;
    var head = "It started around " + c.start + (ongoing ? " and is still going on." : " and lasted until " + tw.end + ".");
    var what = (c.y_title || "").replace(/ per hour$/, "").replace(/ \(minutes\)$/, "").toLowerCase() || "activity";
    if (c.unit === "minutes") {               // an average time: compare the averages, never add them up
      var after = (c.points || []).filter(function (p) { return p.hour >= sh && p.baseline; });
      if (!after.length) return answer(head, null);
      a = after.reduce(function (t, p) { return t + (p.actual || 0); }, 0) / after.length;
      b = after.reduce(function (t, p) { return t + p.baseline; }, 0) / after.length;
      return answer(head, "Since " + c.start + ": " + what + " " + num(a, "min") + " on average, against about " + num(b, "min") +
        " on a normal day (" + pct0((a - b) / b * 100) + ").");
    }
    var sub = !b ? null : a === 0 ? "Since " + c.start + " nothing has been recorded — normally about " + num(b) + " " + what + " by now." :
      "Since " + c.start + ": " + num(a) + " " + what + ", against about " + num(b) + " on a normal day (" + pct0((a - b) / b * 100) + ").";
    return answer(head, sub);
  }
  function whereAnswer(w) {
    var wh = w.warehouse || {}, rows = wh.comparison || [];
    var bad = rows.filter(function (x) { return stateOf(x.classification) === "worse"; });
    var share = wh.share_of_shortfall_pct !== null && wh.share_of_shortfall_pct !== undefined ? Math.round(wh.share_of_shortfall_pct) : null;
    var head;
    if (!wh.name) head = "The drop is spread across the warehouse — no single site stands out.";
    else if (bad.length > 1 && bad.length === rows.length) head = "All warehouses are affected; " + wh.name + " has the biggest part" +
      (share !== null ? " (" + share + "% of the problem)." : ".");
    else if (bad.length > 1) head = bad.length + " warehouses are affected, mostly " + wh.name + (share !== null ? " (" + share + "% of the problem)." : ".");
    else head = "Mainly in warehouse " + wh.name + (share !== null ? " — " + share + "% of the problem." : ".");
    return answer(head, w.headline.label + (/time$/i.test(w.headline.label) ? " is " : " are ") + pct0(Math.abs(w.headline.pct_diff || 0)).replace(/^[+−]/, "") +
      (w.headline.pct_diff < 0 ? " below" : " above") + " normal overall.");
  }
  function stepAnswer(p) {
    var rows = p.comparison || [], worst = rows.filter(function (x) { return stateOf(x.classification) === "worse"; });
    var where = p.scope ? " in " + p.scope : "";
    if (worst.length) {
      var names = worst.slice(0, 2).map(function (x) { return cleanName(x.name) + " (" + pct0(x.pct_diff) + ")"; });
      return answer((worst.length > 1 ? "Steps hit hardest" + where + ": " + names.join(" and ") : "The " + cleanName(worst[0].name) +
        " step is hit hardest" + where + " (" + pct0(worst[0].pct_diff) + ")") + ".", "Each bar is one step of the work, compared with a normal day.");
    }
    var top = rows[0];
    return answer("No step is clearly worse than normal" + where + ".", top ? "The biggest change is " + cleanName(top.name) + " (" +
      pct0(top.pct_diff) + "), which is within normal ups and downs." : null);
  }
  function changesAnswer(changes) {
    var rows = (changes || []).slice(0, 8).filter(function (c) { return c.pct_diff !== null && c.pct_diff !== undefined; });
    var bad = rows.filter(function (c) { return stateOf(c.classification) === "worse"; }).length;
    var good = rows.filter(function (c) { return stateOf(c.classification) === "better"; }).length;
    if (!rows.length) return "";
    return answer(bad ? bad + " of " + rows.length + " measures are worse than normal." : "All " + rows.length + " measures are within normal ups and downs.",
      good ? good + " " + (good > 1 ? "are" : "is") + " better than normal." : "Each bar compares today with a normal day at this time.");
  }

  function shareBar(causes) {
    var list = (causes || []).filter(function (c) { return c.explains_pct > 0; });
    if (!list.length) return "";
    var total = list.reduce(function (a, c) { return a + c.explains_pct; }, 0), scale = total > 100 ? 100 / total : 1, used = 0;
    var segs = list.map(function (c, i) {
      var w = c.explains_pct * scale;
      used += w;
      return '<span class="wpa-seg" style="flex:0 0 ' + w.toFixed(2) + "%;background:" + C.cause[i] + '"' +
        tipAttrs("About " + Math.round(w) + "% of the drop", "#" + c.rank + " " + c.title) + ">" +
        (w >= 14 ? '<span style="color:' + C.causeInk[i] + '">' + Math.round(w) + "%</span>" : "") + "</span>";
    });
    var rest = 100 - used;
    if (rest >= 0.5) segs.push('<span class="wpa-seg" style="flex:1 1 auto;background:' + C.rest + '"' +
      tipAttrs("About " + Math.round(rest) + "% of the drop", "Not explained by the warehouse records") + "></span>");
    return '<div class="wpa-sub">How much of the drop each cause explains</div><div class="wpa-share">' + segs.join("") + "</div>" +
      legend(list.map(function (c, i) {
        return { color: C.cause[i], text: "#" + c.rank + " " + c.title + " — about " + Math.round(c.explains_pct * scale) + "%" };
      }).concat(rest >= 0.5 ? [{ color: C.rest, text: "Not explained by the records — about " + Math.round(rest) + "%" }] : []));
  }

  function evidenceChart(checks) {
    var rows = (checks || []).filter(function (c) {
      return c.status !== "not_checked" && c.actual !== null && c.actual !== undefined && c.baseline !== null && c.baseline !== undefined;
    });
    if (!rows.length) return "";
    rows.sort(function (a, b) { return (a.status === "supported" ? 0 : 1) - (b.status === "supported" ? 0 : 1); });
    return '<div class="wpa-sub">Every check: the problem hours today vs the same hours on normal days</div>' +
      legend([{ color: C.today, text: "Today" }, { color: C.normal, text: "Normal" }]) + rows.slice(0, 12).map(function (c) {
        var max = Math.max(c.actual, c.baseline) || 1, found = c.status === "supported";
        function bar(v, color) {
          return '<div class="wpa-ev-bar"><div class="wpa-ev-track"><span style="width:' + (v / max * 100).toFixed(1) +
            "%;background:" + color + '"></span></div><em>' + esc(num(v)) + "</em></div>";
        }
        return '<div class="wpa-ev-row"' + tipAttrs("Today " + num(c.actual) + " · normal " + num(c.baseline) +
          (c.pct_diff !== null && c.pct_diff !== undefined ? " (" + pct(c.pct_diff) + ")" : ""), c.statement) + ">" +
          '<div class="wpa-ev-name"><span class="wpa-pill ' + (found ? "found" : "ok") + '">' + (found ? "⚠ Found" : "✓ Normal") +
          "</span>" + esc(c.label) + '<span class="wpa-muted"> · ' + esc(c.unit || "") + "</span></div>" +
          "<div>" + bar(c.actual, C.today) + bar(c.baseline, C.normal) + "</div></div>";
      }).join("");
  }

  function setupTips(root) {
    var host = root.querySelector(".wpa");
    if (!host) return;
    var tip = document.createElement("div");
    tip.className = "wpa-tip";
    tip.setAttribute("role", "tooltip");
    host.appendChild(tip);
    root._wpaTip = tip;
    if (root._wpaTipsBound) return;
    root._wpaTipsBound = true;
    function show(el, x, y) {
      var t = root._wpaTip;
      if (!t) return;
      t.textContent = "";
      var v = document.createElement("strong");
      v.textContent = el.getAttribute("data-tip-v");
      t.appendChild(v);
      if (el.getAttribute("data-tip")) {
        var l = document.createElement("div");
        l.textContent = el.getAttribute("data-tip");
        t.appendChild(l);
      }
      t.style.display = "block";
      var b = t.getBoundingClientRect();
      t.style.left = Math.max(8, Math.min(window.innerWidth - b.width - 8, x + 14)) + "px";
      t.style.top = (y - b.height - 12 < 8 ? y + 18 : y - b.height - 12) + "px";
    }
    function hide() { if (root._wpaTip) root._wpaTip.style.display = "none"; }
    root.addEventListener("mousemove", function (e) {
      var el = e.target && e.target.closest ? e.target.closest("[data-tip-v]") : null;
      if (el) show(el, e.clientX, e.clientY); else hide();
    });
    root.addEventListener("mouseleave", hide);
    root.addEventListener("focusin", function (e) {
      var el = e.target && e.target.closest ? e.target.closest("[data-tip-v]") : null;
      if (!el) return;
      var b = el.getBoundingClientRect();
      show(el, b.left + b.width / 2, b.top);
    });
    root.addEventListener("focusout", hide);
  }

  function whereBlock(w) {
    if (!w || !w.headline) {
      return '<p class="wpa-finding">' + esc((w && w.conclusion) || "No deterioration beyond normal variation was detected.") + "</p>";
    }
    var h = [whereAnswer(w)];
    var whs = (w.warehouse && w.warehouse.comparison) || [];
    if (whs.length) h.push(warehouseChart(w.warehouse));
    var facts = [];
    (w.dimensions || []).forEach(function (d) {
      if (d.top && d.top.length) {
        facts.push("<li>" + esc(d.dimension[0].toUpperCase() + d.dimension.slice(1)) + ": <b>" + esc(d.top[0].name) +
          "</b> — " + esc(Math.round(d.top[0].share_of_shortfall_pct || 0)) + "% of the drop</li>");
      }
    });
    if (facts.length) h.push('<div class="wpa-sub">Also worth knowing</div><ul>' + facts.join("") + "</ul>");
    return h.join("");
  }

  var CONF = { High: ["Likely — strong evidence", "#c53030"], Medium: ["Likely", "#c05621"], Low: ["Possible", "#718096"] };

  function agentStrip(agents) {
    if (!agents || !agents.length) return "";
    return '<div class="wpa-agents">' + agents.map(function (a, i) {
      var ok = a.status === "ok" || a.status === "done";
      var tone = ok ? "#2f855a" : a.status === "not_needed" ? "#718096" : "#c05621";
      return '<div class="wpa-agent"><span class="wpa-step">' + (i + 1) + "</span><b>" + esc(a.name) + "</b> " +
        '<span style="color:' + tone + ';font-size:12px">● ' + esc(String(a.status).replace(/_/g, " ")) + "</span>" +
        '<span class="wpa-muted">' + esc(a.job) + "</span></div>";
    }).join("") + "</div>";
  }

  function whyCard(r) {
    var dg = r.diagnosis;
    if (!dg || !dg.status || dg.status === "not_needed") return "";
    var h = ['<div class="wpa-card" style="margin-bottom:14px"><h4>Why it happened — and what to do</h4>', agentStrip(r.agents)];
    if (dg.summary) h.push('<p class="wpa-finding" style="margin:0 0 6px">' + esc(dg.summary) + "</p>");
    h.push(shareBar(dg.likely_causes));
    var left = [], right = [];
    (dg.likely_causes || []).forEach(function (c, i) {
      var cf = CONF[c.confidence] || [c.confidence, "#718096"];
      left.push('<div class="wpa-cause" style="border-left-color:' + C.cause[i] + '"><div class="wpa-tag">#' + c.rank + " · " +
        esc(cf[0]) + " · about " + esc(c.explains_pct) + "% of the drop</div>" +
        '<div class="wpa-cause-title">' + esc(c.title) + "</div><ul>" +
        (c.evidence || []).slice(0, 4).map(function (e) { return "<li>" + esc(e) + "</li>"; }).join("") + "</ul>" +
        (c.note ? '<div class="wpa-muted" style="margin-top:4px">' + esc(c.note) + "</div>" : "") + "</div>");
    });
    if (dg.actions && dg.actions.length) {
      right.push("<div class='wpa-sub'>What to do now</div><ol style='margin:4px 0 0 18px;padding:0'>" +
        dg.actions.map(function (a) { return "<li style='margin:4px 0;font-size:13px'>" + esc(a) + "</li>"; }).join("") + "</ol>");
    }
    var evidence = evidenceChart((r.investigation || {}).checks);
    if (!evidence && dg.ruled_out && dg.ruled_out.length) {
      right.push("<div class='wpa-sub'>Checked and ruled out</div><ul>" + dg.ruled_out.slice(0, 8).map(function (x) {
        return "<li class='wpa-muted'>" + esc(x.statement) + "</li>";
      }).join("") + "</ul>");
    }
    if (dg.not_checked && dg.not_checked.length) {
      right.push("<div class='wpa-sub'>Could not be checked</div><ul>" + dg.not_checked.map(function (x) {
        return "<li class='wpa-muted'>" + esc(x.statement) + "</li>";
      }).join("") + "</ul>");
    }
    h.push('<div class="wpa-cols"><div>' + (left.join("") || "") + "</div><div>" + right.join("") + "</div></div>");
    if (evidence) h.push('<div style="margin-top:14px">' + evidence + "</div>");
    h.push('<div class="wpa-muted" style="margin-top:8px">Likely causes are strong patterns in the warehouse records for the same hours, compared with normal days — please confirm them with the team.</div></div>');
    return h.join("");
  }

  function deliveryText(d) {
    if (!d || !d.status) return "—";
    var t = DELIVERY[d.status] || d.status.replace(/_/g, " ");
    if (d.status === "sent" && d.sent_to && d.sent_to.length) {
      t += " to " + d.sent_to.map(function (s) { return s.label; }).join(", ");
    }
    if (d.reason && d.status !== "not_required") t += " (" + d.reason + ")";
    return esc(t);
  }

  function statusDot(m) {
    var map = { active: ["#38a169", "Monitoring automatically"], manual_only: ["#d69e2e", "Automatic scheduling unavailable"],
      not_configured: ["#a0aec0", "Workspace database not configured"] };
    var x = map[m.status] || ["#a0aec0", m.status];
    return '<span class="wpa-dot" style="background:' + x[0] + '"></span>' + esc(x[1]);
  }

  function render(root, ws, data, opts) {
    var d = data, r = d.report, m = d.monitoring, admin = d.viewer && d.viewer.is_admin;
    var h = ['<style>' + CSS + "</style><div class='wpa'>"];
    h.push('<div class="wpa-head"><div><h3>Warehouse Performance Agent</h3><div class="wpa-meta">' +
      esc(d.workspace.display_name || d.workspace.name || ws) + " · " + statusDot(m) +
      " · Last analysis <b>" + when(m.last_analysis_at) + "</b> · Next analysis <b>" + when(m.next_analysis_at) + "</b>" +
      (r && r.period ? " · Period <b>" + esc(r.period.label) + "</b>" : "") + "</div></div>" +
      '<div class="wpa-btns"><button type="button" class="wpa-btn primary" id="wpa-run"' + (m.run_queued ? " disabled" : "") + '>' +
      '<i class="fas fa-play"></i>' + (m.run_queued ? "Analysis running…" : "Run analysis now") + "</button>" +
      (r ? '<button type="button" class="wpa-btn" id="wpa-open"><i class="fas fa-file-alt"></i>Full report</button>' +
        '<a class="wpa-btn" href="' + API + "/report?format=csv&workspace_id=" + encodeURIComponent(ws) + "&report_id=" +
        encodeURIComponent(r.report_id) + '"><i class="fas fa-file-csv"></i>Download CSV</a>' +
        '<a class="wpa-btn" href="' + API + "/report?format=docx&workspace_id=" + encodeURIComponent(ws) + "&report_id=" +
        encodeURIComponent(r.report_id) + '"><i class="fas fa-file-word"></i>Download Word</a>' : "") +
      (admin ? '<button type="button" class="wpa-btn" id="wpa-rescan" title="Re-read the database schema">' +
        '<i class="fas fa-sync-alt"></i>Re-scan database</button>' : "") +
      "</div></div>");
    h.push('<div id="wpa-msg"></div>');
    if (m.clock_pinned_to) {
      h.push('<div class="wpa-warn">Test mode: analysis clock pinned to <b>' + esc(m.clock_pinned_to) +
        "</b> (WPA_ANALYSIS_AS_OF). Results describe that moment, not now.</div>");
    }

    if (m.status === "not_configured") {
      h.push('<div class="wpa-card">This workspace has no database connection yet. Once DB Config is saved, the agent starts analysing automatically.</div></div>');
      root.innerHTML = h.join("");
      bind(root, ws, d, opts);
      autoRefresh(root, ws, opts, m.last_run ? m.last_run.started_at : null);
      return;
    }
    if (!r) {
      h.push('<div class="wpa-card">No analysis has completed yet. The agent runs automatically' +
        (m.next_analysis_at ? " (next run " + when(m.next_analysis_at) + ")" : "") + " — or use <b>Run analysis now</b>." +
        (m.last_run && m.last_run.failure_reason ? '<div class="wpa-muted" style="margin-top:6px">Last attempt: ' +
          esc(m.last_run.failure_reason) + "</div>" : "") + "</div>" + emailCard(d) + "</div>");
      root.innerHTML = h.join("");
      bind(root, ws, d, opts);
      autoRefresh(root, ws, opts, m.last_run ? m.last_run.started_at : null);
      return;
    }
    (r.freshness_warnings || []).forEach(function (w) { h.push('<div class="wpa-warn">⚠ ' + esc(w.message) + "</div>"); });
    if (r.status !== "ok") h.push('<div class="wpa-warn">' + esc(r.message || r.status) + "</div>");

    var k = r.kpis || {};
    h.push('<div class="wpa-grid">' + kpiCard(k.units_moved, "units") + kpiCard(k.orders_dispatched, "orders") +
      kpiCard(k.pending_orders, "pending") + kpiCard(k.overall, "overall") + "</div>");

    if (r.status === "ok") {
      var hourly = (r.charts || {}).hourly, problem = !!(r.where && r.where.headline);
      var proc = problem && r.where.process && (r.where.process.comparison || []).length ? r.where.process : null;
      h.push('<div class="wpa-two">' + (hourly ? '<div class="wpa-card"><h4>' + (problem ? "When did it start?" : "Today, hour by hour") +
        "</h4>" + (problem && whenAnswer(hourly, r.where.time_window) || "") + '<div class="wpa-muted">' + esc(hourly.title) + "</div>" +
        hourlyChart(hourly) + "</div>" : "") +
        '<div class="wpa-card"><h4>Where is the problem?</h4>' + whereBlock(r.where) + "</div></div>");
      h.push('<div class="wpa-two">' + (proc ? '<div class="wpa-card"><h4>Which step is affected?</h4>' + stepAnswer(proc) +
        stepChart(proc) + "</div>" : "") +
        '<div class="wpa-card"><h4>What changed?</h4>' + changesAnswer(r.changes) + changesChart(r.changes) + "</div></div>");
    } else {
      h.push('<div class="wpa-card" style="margin-bottom:14px"><h4>What changed?</h4>' + changesTable(r.changes) +
        '<p class="wpa-muted">Nothing could be analysed for this period — see the message above.</p></div>');
    }

    h.push(whyCard(r));
    var hasWhy = r.diagnosis && r.diagnosis.status && r.diagnosis.status !== "not_needed";
    h.push('<div class="wpa-card" style="margin-bottom:14px"><h4>Generated executive finding</h4><p class="wpa-finding">' +
      esc(r.executive_summary) + '</p><div class="wpa-muted">' +
      (r.summary_source === "llm_validated" ? "Written by the workspace LLM from the calculated findings and checked against them." :
        "Generated from the calculated findings.") + "</div>" +
      (!hasWhy && r.recommendations && r.recommendations.length ? "<h4 style='margin-top:12px'>Recommended areas for investigation</h4><ul>" +
        r.recommendations.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") + "</div>");

    var status = ['<div class="wpa-card"><h4>Automatic reporting status</h4><table><tbody>',
      "<tr><td>Last analysis</td><td>" + when(r.generated_at) + " (" + esc(m.last_run ? m.last_run.trigger : "") + ")</td></tr>",
      "<tr><td>Report</td><td>Generated · " + esc(r.report_id) + "</td></tr>",
      "<tr><td>This analysis</td><td>" + deliveryText(r.delivery) + "</td></tr>",
      "<tr><td>Last email sent</td><td>" + (d.last_email ? when(d.last_email.at) + " to " +
        esc((d.last_email.sent_to || []).join(", ") || "recipients") + " <span class='wpa-muted'>(" +
        (d.last_email.automatic ? "automatic" : "manual") + ")</span>" : "<span class='wpa-muted'>No email sent yet</span>") +
        "</td></tr>"];
    (r.manual_deliveries || []).slice(-2).forEach(function (md) {
      status.push("<tr><td>Manual email</td><td>" + deliveryText(md) + " · " + when(md.at) + "</td></tr>");
    });
    if (admin && d.recipients) {
      var rc = d.recipients.recipients || [];
      status.push("<tr><td>Report recipients</td><td>" + (rc.length ? rc.map(function (x) {
        return esc(x.label) + " <span class='wpa-muted'>" + esc(x.address_masked) + "</span>";
      }).join(", ") : "<span class='wpa-down'>None selected — reports are generated but not emailed. Choose recipients in Email settings below.</span>") +
        ((d.recipients.problems || []).filter(function (p) { return p.label; }).map(function (p) {
          return "<div class='wpa-muted'>" + esc(p.label) + ": " + esc(p.reason) + "</div>";
        }).join("")) + "</td></tr>");
    }
    if (m.last_run && m.last_run.status !== "ok" && m.last_run.failure_reason) {
      status.push("<tr><td>Last run</td><td class='wpa-down'>" + esc(m.last_run.status) + ": " + esc(m.last_run.failure_reason) + "</td></tr>");
    }
    status.push("</tbody></table></div>");

    var disc = d.discovery;
    var found = ['<div class="wpa-card"><h4>Data the agent found</h4>'];
    if (disc) {
      found.push('<div class="wpa-muted">Scanned ' + esc(disc.tables_scanned) + " tables · " + when(disc.discovered_at) + "</div><ul>");
      Object.keys(disc.sources || {}).forEach(function (s) {
        if (disc.sources[s]) found.push("<li>" + esc(s === "activity" ? "Activity/transactions" : "Orders") + ": " + esc(disc.sources[s]) + "</li>");
      });
      Object.keys(disc.evidence_sources || {}).forEach(function (s) {
        if (disc.evidence_sources[s]) found.push("<li>Exception log (cause checks): " + esc(disc.evidence_sources[s]) + "</li>");
      });
      found.push("</ul>");
      if ((r.unavailable || []).length) {
        found.push("<div style='margin-top:8px' class='wpa-muted'>Not available from this database:</div><ul>" +
          r.unavailable.map(function (u) { return "<li class='wpa-muted'>" + esc(u.reason) + "</li>"; }).join("") + "</ul>");
      }
    } else {
      found.push('<p class="wpa-muted">The schema has not been scanned yet.</p>');
    }
    found.push("</div>");
    h.push('<div class="wpa-two">' + status.join("") + found.join("") + "</div>" + emailCard(d) + "</div>");
    root.innerHTML = h.join("");
    bind(root, ws, d, opts);
    setupTips(root);
    autoRefresh(root, ws, opts, m.last_run ? m.last_run.started_at : null);
  }

  function emailCard(d) {
    var es = d.email_settings;
    if (!es) return "";
    var boxes = (es.saved || []).map(function (r) {
      return '<label class="wpa-chk"><input type="checkbox" class="wpa-rcpt" value="' + esc(r.label) + '"' +
        (r.selected ? " checked" : "") + "> " + esc(r.label) + ' <span class="wpa-muted">' + esc(r.address_masked) + "</span></label>";
    }).join("");
    function radio(value, label) {
      return '<label class="wpa-chk"><input type="radio" name="wpa-mode" value="' + value + '"' +
        (es.mode === value ? " checked" : "") + "> " + esc(label) + "</label>";
    }
    return '<div class="wpa-card" style="margin-top:14px"><h4>Email settings</h4>' +
      '<div class="wpa-muted">The report is emailed automatically, with no button to press, to the recipients ticked below.</div>' +
      '<div class="wpa-sub">When to send</div>' +
      radio("significant", "Only when a significant problem is found (recommended — hourly runs email once per problem, max 3 a day)") +
      radio("every_run", "After every analysis (about every hour, problems included, even when everything is normal)") +
      '<div class="wpa-muted" style="margin-top:4px">Run analysis now always emails the report when it finds a significant problem.</div>' +
      '<div class="wpa-sub">Send the report to</div>' +
      (boxes || '<div class="wpa-muted">No recipients saved yet — add one below.</div>') +
      '<div class="wpa-sub">Add a recipient</div>' +
      '<div class="wpa-btns"><input class="wpa-field" id="wpa-new-name" placeholder="Name, e.g. Operations Head" maxlength="60">' +
      '<input class="wpa-field" id="wpa-new-email" type="email" placeholder="name@company.com" maxlength="120">' +
      '<button type="button" class="wpa-btn" id="wpa-add-rcpt"><i class="fas fa-user-plus"></i>Add recipient</button></div>' +
      '<div class="wpa-btns" style="margin-top:14px"><button type="button" class="wpa-btn primary" id="wpa-save-email">' +
      '<i class="fas fa-save"></i>Save email settings</button></div>' +
      (es.updated_by ? '<div class="wpa-muted" style="margin-top:8px">Last changed by ' + esc(es.updated_by) + " · " +
        when(es.updated_at) + "</div>" : "") + "</div>";
  }

  function rawApi(method, url, payload) {
    var opts = { method: method, headers: { "Content-Type": "application/json" }, credentials: "same-origin" };
    if (payload !== undefined) opts.body = JSON.stringify(payload);
    return fetch(url, opts).then(function (r) {
      return r.json().catch(function () { return { type: "error", error: "HTTP " + r.status }; });
    });
  }

  function checkedLabels(root) {
    return Array.prototype.slice.call(root.querySelectorAll(".wpa-rcpt")).filter(function (c) { return c.checked; })
      .map(function (c) { return c.value; });
  }

  function chosenMode(root) {
    var m = root.querySelector('input[name="wpa-mode"]:checked');
    return m ? m.value : "significant";
  }

  function saveEmailSettings(root, ws, opts, labels, mode) {
    return api("POST", "/email_settings", { workspace_id: ws, mode: mode, recipients: labels }).then(function (res) {
      if (res.type !== "success") { msg(root, res.error || "Could not save the email settings.", true); return false; }
      load(root, ws, opts);
      return true;
    });
  }

  function msg(root, text, bad) {
    var el = root.querySelector("#wpa-msg");
    if (el) el.innerHTML = text ? '<div class="wpa-warn" style="' + (bad ? "border-color:#fc8181;background:#fff5f5" : "") + '">' + esc(text) + "</div>" : "";
  }

  function bind(root, ws, d, opts) {
    var run = root.querySelector("#wpa-run");
    if (run) run.onclick = function () {
      run.disabled = true; run.innerHTML = '<i class="fas fa-spinner fa-spin"></i>Analysis running…';
      var before = d.monitoring.last_run ? d.monitoring.last_run.started_at : null;
      api("POST", "/run", { workspace_id: ws }).then(function (res) {
        if (res.type !== "success") { msg(root, res.error || "Could not start the analysis.", true); run.disabled = false; return; }
        if (!res.queued) { load(root, ws, opts, res.message); return; }
        poll(root, ws, opts, before, 0);
      });
    };
    var open = root.querySelector("#wpa-open");
    if (open) open.onclick = function () {
      window.open(API + "/report?format=html&workspace_id=" + encodeURIComponent(ws) + "&report_id=" +
        encodeURIComponent(d.report.report_id), "_blank", "noopener");
    };
    var save = root.querySelector("#wpa-save-email");
    if (save) save.onclick = function () {
      var labels = checkedLabels(root);
      if (!labels.length && !window.confirm("No recipients are ticked, so reports will not be emailed. Save anyway?")) return;
      save.disabled = true;
      saveEmailSettings(root, ws, opts, labels, chosenMode(root)).then(function () { save.disabled = false; });
    };
    var add = root.querySelector("#wpa-add-rcpt");
    if (add) add.onclick = function () {
      var name = (root.querySelector("#wpa-new-name").value || "").trim();
      var email = (root.querySelector("#wpa-new-email").value || "").trim();
      if (!name || !email) { msg(root, "Enter both a name and an email address.", true); return; }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { msg(root, "That doesn't look like a valid email address.", true); return; }
      add.disabled = true;
      // Recipients live in the workspace's existing Email Config; the agent only stores which ones it uses.
      rawApi("GET", "/api/v0/get_workspace_email_config?workspace_id=" + encodeURIComponent(ws)).then(function (res) {
        if (res.type !== "success") throw new Error(res.error || "Could not read the Email Config.");
        var list = (res.emails || []).map(function (e) { return { label: e.label, address: e.address }; });
        if (list.some(function (e) { return String(e.label).trim().toLowerCase() === name.toLowerCase(); })) {
          throw new Error("A recipient named \"" + name + "\" already exists — tick it above instead.");
        }
        list.push({ label: name, address: email });
        return rawApi("POST", "/api/v0/save_workspace_email_config", { workspace_id: ws, emails: list });
      }).then(function (res) {
        if (res.type !== "success") throw new Error(res.error || "Could not save the recipient.");
        var labels = checkedLabels(root);
        labels.push(name);
        return saveEmailSettings(root, ws, opts, labels, chosenMode(root));
      }).catch(function (e) {
        msg(root, e.message || String(e), true);
      }).then(function () { add.disabled = false; });
    };
    var rescan = root.querySelector("#wpa-rescan");
    if (rescan) rescan.onclick = function () {
      rescan.disabled = true;
      var before = d.monitoring.last_run ? d.monitoring.last_run.started_at : null;
      api("POST", "/rediscover", { workspace_id: ws }).then(function (res) {
        if (res.type !== "success") { msg(root, res.error || "Re-scan failed.", true); rescan.disabled = false; return; }
        if (res.queued) poll(root, ws, opts, before, 0); else load(root, ws, opts);
      });
    };
  }

  function poll(root, ws, opts, before, n) {
    if (n > 60) { load(root, ws, opts); return; }
    setTimeout(function () {
      api("GET", "/dashboard?workspace_id=" + encodeURIComponent(ws)).then(function (res) {
        var lr = res.dashboard && res.dashboard.monitoring.last_run;
        if (res.type === "success" && lr && lr.started_at !== before && !res.dashboard.monitoring.run_queued) {
          render(root, ws, res.dashboard, opts);
        } else {
          poll(root, ws, opts, before, n + 1);
        }
      });
    }, 3000);
  }

  // Auto-refresh: a scheduled run can finish while the page is open. Check every minute and
  // re-render when a newer analysis exists (never while someone is editing Email settings).
  function autoRefresh(root, ws, opts, seen) {
    if (root._wpaTimer) clearInterval(root._wpaTimer);
    root._wpaTimer = setInterval(function () {
      if (!root.querySelector(".wpa-head")) { clearInterval(root._wpaTimer); return; }   // user left the panel
      var busy = root.querySelector(".wpa-field:focus, .wpa-rcpt:focus") ||
        Array.prototype.some.call(root.querySelectorAll(".wpa-field"), function (f) { return f.value; });
      if (busy) return;
      api("GET", "/dashboard?workspace_id=" + encodeURIComponent(ws)).then(function (res) {
        if (res.type !== "success") return;
        var lr = res.dashboard.monitoring.last_run;
        var started = lr ? lr.started_at : null;
        if (started && started !== seen && !res.dashboard.monitoring.run_queued) {
          render(root, ws, res.dashboard, opts || {});
          msg(root, "Updated with the latest analysis (" + when(res.dashboard.monitoring.last_analysis_at) + ").", false);
        }
      });
    }, 60000);
  }

  function load(root, ws, opts, flash) {
    if (!ws) { root.innerHTML = "<p>No workspace selected.</p>"; return; }
    root.innerHTML = '<div class="wpa" style="color:#718096;padding:12px">Loading warehouse performance…</div>';
    api("GET", "/dashboard?workspace_id=" + encodeURIComponent(ws)).then(function (res) {
      if (res.type !== "success") { root.innerHTML = "<p>" + esc(res.error || "Could not load the dashboard.") + "</p>"; return; }
      render(root, ws, res.dashboard, opts || {});
      if (flash) msg(root, flash, false);
    }).catch(function () { root.innerHTML = "<p>Could not load the dashboard.</p>"; });
  }

  window.renderWarehousePerfDashboard = function (root, ws, opts) { load(root, ws, opts); };
  window.showWarehousePerfAgent = function (ws) {
    var area = document.getElementById("contentArea");
    if (!area) return;
    // The Workspace Manager starts with #contentArea hidden; every panel must show it
    // (the other sidebar panels do the same). Without this the first click after a
    // page load rendered into a hidden area.
    area.style.display = "block";
    load(area, ws, {});
  };
})();
