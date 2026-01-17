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
  </style>
</head>
<body>
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
