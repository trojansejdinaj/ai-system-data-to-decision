# ruff: noqa: E501

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard-ui"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    # dead-simple, but usable and “stranger-readable” fast
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Dashboard v1</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; max-width: 1100px; }
    h1 { margin-bottom: 6px; }
    .muted { color: #555; margin-top: 0; }
    .row { display: flex; gap: 18px; flex-wrap: wrap; margin: 16px 0; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 14px 16px; min-width: 240px; }
    label { font-size: 12px; color: #444; display: block; margin-bottom: 4px; }
    input, select { padding: 8px; border-radius: 8px; border: 1px solid #ccc; width: 220px; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border-bottom: 1px solid #eee; padding: 8px; text-align: left; font-size: 14px; }
    .kpi { font-size: 26px; font-weight: 700; }
    .small { font-size: 12px; color: #666; }
    .bar { height: 10px; background: #eee; border-radius: 99px; overflow: hidden; }
    .bar > div { height: 100%; background: #111; }
    .nav { margin-top: 8px; }
    .nav a {
      display: inline-block;
      margin-right: 12px;
      color: #1b56b3;
      text-decoration: none;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="nav">
    <a href="/dashboard/decisions">Decision View</a>
  </div>
  <h1>Dashboard v1</h1>
  <p class="muted">Monthly snapshot + trend. If you can’t read this in 60 seconds, we failed.</p>

  <div class="row">
    <div class="card">
      <label>Trend start (inclusive)</label>
      <input id="start" type="date"/>
      <label style="margin-top:10px;">Trend end (exclusive)</label>
      <input id="end" type="date"/>
    </div>

    <div class="card">
      <label>Trend granularity</label>
      <select id="granularity">
        <option value="day">day</option>
        <option value="week">week</option>
        <option value="month">month</option>
      </select>

      <label style="margin-top:10px;">Trend metric</label>
      <select id="metric">
        <option value="total_records">total_records</option>
        <option value="distinct_records">distinct_records</option>
        <option value="distinct_source_ids">distinct_source_ids</option>
        <option value="distinct_sources">distinct_sources</option>
        <option value="distinct_categories">distinct_categories</option>
      </select>
    </div>

    <div class="card" style="flex:1;">
      <div class="small">Latest month</div>
      <div id="latestMonth" class="kpi">—</div>
      <div id="latestKpis" class="small">—</div>
      <div style="margin-top:10px;" class="small">Interpretation: “Are we up or down? What changed?”</div>
    </div>
  </div>

  <h2>Monthly Summary</h2>
  <div id="monthlyWrap">Loading…</div>

  <h2 style="margin-top:24px;">Trend</h2>
  <div id="trendWrap">Loading…</div>

<script>
  const $ = (id) => document.getElementById(id);

  function iso(d){ return d.toISOString().slice(0,10); }

  async function getJSON(url){
    const r = await fetch(url);
    if(!r.ok){ throw new Error(await r.text()); }
    return await r.json();
  }

  function setDefaults(){
    const now = new Date();
    const start = new Date(now);
    start.setDate(start.getDate() - 30);
    $("start").value = iso(start);
    $("end").value = iso(now);
  }

  function renderMonthly(rows){
    if(!rows.length){
      $("monthlyWrap").innerHTML = "<div class='small'>No monthly data found.</div>";
      return;
    }

    const latest = rows[rows.length - 1];
    $("latestMonth").textContent = latest.month_start;
    $("latestKpis").textContent =
      `total=${latest.total_records}, distinct_records=${latest.distinct_records}, sources=${latest.distinct_sources}, categories=${latest.distinct_categories}`;

    let html = "<table><thead><tr>" +
      "<th>month_start</th><th>total</th><th>distinct_records</th><th>source_ids</th><th>sources</th><th>categories</th>" +
      "</tr></thead><tbody>";
    for(const r of rows){
      html += `<tr>
        <td>${r.month_start}</td>
        <td>${r.total_records}</td>
        <td>${r.distinct_records}</td>
        <td>${r.distinct_source_ids}</td>
        <td>${r.distinct_sources}</td>
        <td>${r.distinct_categories}</td>
      </tr>`;
    }
    html += "</tbody></table>";
    $("monthlyWrap").innerHTML = html;
  }

  function renderTrend(resp){
    const pts = resp.points || [];
    if(!pts.length){
      $("trendWrap").innerHTML = "<div class='small'>No trend points for the selected range.</div>";
      return;
    }

    const max = Math.max(...pts.map(p => p.value));
    let html = "<table><thead><tr><th>bucket_start</th><th>value</th><th style='width:45%'>visual</th></tr></thead><tbody>";
    for(const p of pts){
      const w = max ? Math.round((p.value / max) * 100) : 0;
      html += `<tr>
        <td>${p.bucket_start}</td>
        <td>${p.value}</td>
        <td><div class="bar"><div style="width:${w}%"></div></div></td>
      </tr>`;
    }
    html += "</tbody></table>";
    $("trendWrap").innerHTML = html;
  }

  async function refresh(){
    try {
      const monthly = await getJSON("/dashboard/monthly");
      renderMonthly(monthly);

      const start = $("start").value;
      const end = $("end").value;
      const granularity = $("granularity").value;
      const metric = $("metric").value;

      const trend = await getJSON(`/dashboard/trend?start=${start}&end=${end}&granularity=${granularity}&metric=${metric}`);
      renderTrend(trend);
    } catch (e){
      $("monthlyWrap").innerHTML = `<pre>${e}</pre>`;
      $("trendWrap").innerHTML = `<pre>${e}</pre>`;
    }
  }

  setDefaults();
  ["start","end","granularity","metric"].forEach(id => $(id).addEventListener("change", refresh));
  refresh();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@router.get("/dashboard/decisions", response_class=HTMLResponse)
def dashboard_decisions_page():
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Decision Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; max-width: 1100px; }
    h1 { margin-bottom: 6px; }
    .muted { color: #555; margin-top: 0; }
    .row { display: flex; gap: 18px; flex-wrap: wrap; margin: 16px 0; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 14px 16px; min-width: 240px; }
    .small { font-size: 12px; color: #666; }
    .top-nav { display: flex; gap: 12px; margin-bottom: 16px; }
    .top-nav a { color: #1b56b3; text-decoration: none; font-size: 14px; }
    .top-nav a:hover { text-decoration: underline; }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: #111;
      color: #fff;
      font-size: 14px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .kpi { font-size: 26px; font-weight: 700; }
    .reason-list { margin: 8px 0 0; padding-left: 18px; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border-bottom: 1px solid #eee; padding: 8px; text-align: left; font-size: 14px; }
  .bar { height: 10px; background: #eee; border-radius: 99px; overflow: hidden; }
  .bar > div { height: 100%; background: #111; }
  .empty { color: #666; padding: 8px 0; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
  label { font-size: 12px; color: #444; display: block; margin-bottom: 4px; }
  select { padding: 8px; border-radius: 8px; border: 1px solid #ccc; min-width: 220px; }
  .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
  </style>
</head>
<body>
  <div class="top-nav">
    <a href="/dashboard">Dashboard v1</a>
    <a href="/dashboard/decisions">Decision View</a>
  </div>
  <div class="toolbar">
    <h1>Decision View</h1>
  </div>
  <p class="muted">Latest decision + recent runs + trend.</p>

  <h2>Latest decision</h2>
  <div class="row">
    <div class="card" style="min-width: 320px; flex:1;">
      <div id="latestNotice" class="empty">Loading latest decision…</div>
      <div id="latestDecisionCard" style="display:none;">
        <div id="latestDecisionBadge" class="badge">—</div>
        <div id="latestScore" class="kpi">—</div>
        <div class="small" style="margin-top: 8px;">Top reasons</div>
        <div id="latestReasons" class="small">—</div>
        <div class="small" style="margin-top: 10px;">policy_version: <span id="latestPolicy">—</span></div>
        <div class="small">decided_at: <span id="latestDecidedAt">—</span> • status: <span id="latestStatus">—</span></div>
      </div>
    </div>

    <div class="card" style="flex:1; min-width: 340px;">
      <div class="small">Trend (score over time)</div>
      <div id="trendWrap" class="small" style="margin-top: 10px;">Loading trend…</div>
    </div>
  </div>

  <h2>Recent runs</h2>
  <div id="recentRunsWrap" class="small">Loading recent runs…</div>

<script>
  const $ = (id) => document.getElementById(id);

  function formatDate(ts){
    const dt = new Date(ts);
    if (Number.isNaN(dt.getTime())) { return ts || "—"; }
    return dt.toLocaleString();
  }

  function shortRunId(id){
    if (!id || id.length <= 8) { return id || "—"; }
    return id.slice(0, 8);
  }

  function formatScore(raw){
    const score = Number(raw);
    if (Number.isNaN(score)) {
      return "—";
    }
    return Number.isInteger(score) ? String(score) : score.toFixed(2);
  }

  function escapeHtml(v){
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  async function getJSON(url){
    const r = await fetch(url);
    if (!r.ok) {
      const err = new Error(await r.text());
      err.status = r.status;
      throw err;
    }
    return await r.json();
  }

  function renderLatest(payload){
    $("latestNotice").style.display = "none";
    const card = $("latestDecisionCard");
    const decision = payload?.decision || {};
    const runMeta = payload?.run_meta || {};
    const reasons = Array.isArray(decision.reasons) ? decision.reasons : [];
    const topReasons = reasons.slice(0, 3);
    const reasonsToRender = topReasons.length ? topReasons : ["—"];
    const decisionText = decision.decision || "—";

    card.style.display = "block";
    $("latestDecisionBadge").textContent = decisionText;
    $("latestScore").textContent = formatScore(decision.score);
    $("latestPolicy").textContent = decision.policy_version || "—";
    $("latestDecidedAt").textContent = formatDate(decision.decided_at);
    $("latestStatus").textContent = runMeta.status || "—";
    $("latestReasons").innerHTML =
      `<ul class="reason-list">${reasonsToRender.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul>`;
  }

  function renderLatestMissing(){
    $("latestNotice").textContent = "No decisions yet. Run the decision pipeline.";
    $("latestNotice").style.display = "block";
    $("latestDecisionCard").style.display = "none";
  }

  async function fetchLatest(){
    try {
      const latestResp = await fetch("/decisions/latest");
      if (latestResp.status === 404){
        renderLatestMissing();
        return;
      }
      if (!latestResp.ok) {
        const msg = await latestResp.text();
        throw new Error(msg || "Failed to load latest decision.");
      }
      const latestPayload = await latestResp.json();
      renderLatest(latestPayload);
    } catch (e){
      $("latestNotice").style.display = "block";
      $("latestNotice").textContent = e.message || "Failed to load latest decision.";
      $("latestDecisionCard").style.display = "none";
    }
  }

  function renderRecentRuns(data){
    const items = (data && data.items) || [];
    if (!items.length){
      $("recentRunsWrap").innerHTML = "<div class='empty'>No decisions found.</div>";
      return;
    }

    const getRowTs = (row) => {
      const decision = row?.decision || {};
      const runMeta = row?.run_meta || {};
      return decision.created_at || decision.decided_at || runMeta.started_at || runMeta.run_started_at || "";
    };

    const sorted = [...items].sort((a, b) => {
      const ta = Date.parse(getRowTs(a));
      const tb = Date.parse(getRowTs(b));
      const va = Number.isNaN(ta) ? 0 : ta;
      const vb = Number.isNaN(tb) ? 0 : tb;
      return vb - va;
    });

    let html = "<table><thead><tr><th>run_id</th><th>time</th><th>decision</th><th>score</th><th>status</th></tr></thead><tbody>";
    for (const row of sorted.slice(0, 20)){
      const decision = row.decision || {};
      const runMeta = row.run_meta || {};
      const id = decision.run_id || "";
      const ts = decision.created_at || decision.decided_at || runMeta.started_at || runMeta.run_started_at;
      const badge = decision.decision || "—";
      const score = formatScore(decision.score);
      const status = runMeta.status || "—";
      html += `<tr>
        <td><span class="mono" title="${escapeHtml(id)}">${escapeHtml(shortRunId(id))}</span></td>
        <td>${escapeHtml(formatDate(ts))}</td>
        <td>${escapeHtml(badge)}</td>
        <td>${escapeHtml(score)}</td>
        <td>${escapeHtml(status)}</td>
      </tr>`;
    }
    html += "</tbody></table>";
    $("recentRunsWrap").innerHTML = html;
  }

  function renderScoreTrend(rows){
    const points = (rows || [])
      .map((item) => {
        const decision = item?.decision || {};
        const date = String(decision.decided_at || "").slice(0, 10);
        const score = Number(decision.score);
        if (!date || Number.isNaN(score)) {
          return null;
        }
        return { date, score };
      })
      .filter(Boolean);

    if (!points.length){
      $("trendWrap").innerHTML = "<div class='empty'>No decisions found for trend.</div>";
      return;
    }

    const ordered = points.sort((a, b) => new Date(a.date) - new Date(b.date));
    const lastPoints = ordered.slice(-20);
    const max = Math.max(...lastPoints.map(p => p.score));
    const absMax = Math.max(max, 1);

    let html = "<table><thead><tr><th>date</th><th>score</th><th style='width:45%'>bar</th></tr></thead><tbody>";
    for (const p of lastPoints){
      const w = absMax ? Math.round((p.score / absMax) * 100) : 0;
      html += `<tr>
        <td>${escapeHtml(p.date)}</td>
        <td>${escapeHtml(formatScore(p.score))}</td>
        <td><div class=\"bar\"><div style=\"width:${w}%\"></div></div></td>
      </tr>`;
    }
    html += "</tbody></table>";
    $("trendWrap").innerHTML = html;
  }

  async function load(){
    await fetchLatest();

    try {
      const listPayload = await getJSON("/decisions?limit=50&offset=0");
      const items = listPayload.items || [];
      renderRecentRuns({ items });
      renderScoreTrend(items);
    } catch (e){
      $("recentRunsWrap").innerHTML = `<div class=\"empty\">${escapeHtml(e.message || "Failed to load recent runs.")}</div>`;
      $("trendWrap").innerHTML = `<div class=\"empty\">${escapeHtml(e.message || "Failed to load trend.")}</div>`;
    }
  }

  load();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html)
