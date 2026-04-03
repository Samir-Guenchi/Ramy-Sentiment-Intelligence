let currentPage = 1;
let totalPages = 1;

const state = {
  sentiment: "",
  product: "",
  category: "",
  subcategory: "",
  search: "",
};

function setStatus(text, isError = false) {
  const status = document.getElementById("status");
  status.textContent = text;
  status.style.color = isError ? "#fca5a5" : "#ced7e3";
}

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch (_) {
      // Ignore JSON parse error and keep default message.
    }
    throw new Error(msg);
  }
  return res.json();
}

function buildQuery(params) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v).trim() !== "") {
      sp.set(k, String(v));
    }
  });
  const q = sp.toString();
  return q ? `?${q}` : "";
}

function pct(value, total) {
  if (!total) return "0%";
  return `${((value / total) * 100).toFixed(1)}%`;
}

function renderCatalog(catalog) {
  const root = document.getElementById("catalog-list");
  root.innerHTML = "";
  Object.entries(catalog).forEach(([name, subs]) => {
    const item = document.createElement("div");
    item.className = "catalog-item";
    item.innerHTML = `<strong>${name}</strong><small>${subs.join(" | ")}</small>`;
    root.appendChild(item);
  });
}

function renderDistribution(dist) {
  Plotly.newPlot("dist-chart", [{
    labels: Object.keys(dist),
    values: Object.values(dist),
    type: "pie",
    hole: 0.45,
    marker: { colors: ["#15803d", "#b91c1c", "#a16207", "#0f766e", "#7c3aed"] },
  }], {
    margin: { t: 0, l: 0, r: 0, b: 0 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  }, { displayModeBar: false, responsive: true });
}

function renderCategoryShare(categories) {
  Plotly.newPlot("category-chart", [{
    x: Object.keys(categories),
    y: Object.values(categories),
    type: "bar",
    marker: { color: "#ea580c" },
  }], {
    margin: { t: 10, l: 34, r: 10, b: 80 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  }, { displayModeBar: false, responsive: true });
}

function renderProducts(products) {
  Plotly.newPlot("product-chart", [{
    x: Object.keys(products),
    y: Object.values(products),
    type: "bar",
    marker: { color: "#0f766e" },
  }], {
    margin: { t: 10, l: 34, r: 10, b: 90 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  }, { displayModeBar: false, responsive: true });
}

function renderTrend(series) {
  const labels = ["positive", "negative", "neutral", "improvement", "question"];
  const colors = {
    positive: "#15803d",
    negative: "#b91c1c",
    neutral: "#a16207",
    improvement: "#0f766e",
    question: "#7c3aed",
  };

  const traces = labels.map((label) => ({
    x: series.map((r) => r.month),
    y: series.map((r) => r[label] || 0),
    mode: "lines+markers",
    name: label,
    line: { color: colors[label], width: 3 },
  }));

  Plotly.newPlot("trend-chart", traces, {
    margin: { t: 10, l: 34, r: 10, b: 40 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  }, { displayModeBar: false, responsive: true });
}

function renderAspects(rows) {
  Plotly.newPlot("aspect-chart", [{
    x: rows.map((r) => r.aspect),
    y: rows.map((r) => r.score),
    type: "bar",
    marker: { color: "#111827" },
  }], {
    margin: { t: 10, l: 34, r: 10, b: 80 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  }, { displayModeBar: false, responsive: true });
}

function renderPredictDistribution(dist) {
  const keys = Object.keys(dist || {});
  const values = keys.map((k) => dist[k]);
  if (!keys.length) {
    Plotly.purge("predict-dist-chart");
    return;
  }
  Plotly.newPlot("predict-dist-chart", [{
    x: keys,
    y: values,
    type: "bar",
    marker: { color: "#2563eb" },
  }], {
    margin: { t: 10, l: 34, r: 10, b: 60 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  }, { displayModeBar: false, responsive: true });
}

function renderPredictRows(rows) {
  const body = document.getElementById("predict-body");
  body.innerHTML = "";

  (rows || []).forEach((r, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td>${r.text}</td>
      <td><span class="sentiment-pill sentiment-${r.predicted_class}">${r.predicted_class}</span></td>
      <td>${(Number(r.confidence || 0) * 100).toFixed(2)}%</td>
    `;
    body.appendChild(tr);
  });
}

function toCsv(rows) {
  const header = ["index", "text", "predicted_class", "confidence"];
  const lines = [header.join(",")];
  (rows || []).forEach((r, idx) => {
    const cells = [
      String(idx + 1),
      `"${String(r.text || "").replace(/"/g, '""')}"`,
      String(r.predicted_class || ""),
      String((Number(r.confidence || 0) * 100).toFixed(2)),
    ];
    lines.push(cells.join(","));
  });
  return lines.join("\n");
}

function countPredictedClasses(rows) {
  const counts = {};
  (rows || []).forEach((r) => {
    const key = r.predicted_class || "unknown";
    counts[key] = (counts[key] || 0) + 1;
  });
  return counts;
}

function buildPredictionSummary(rows) {
  const counts = countPredictedClasses(rows);
  const total = (rows || []).length;
  const parts = Object.keys(counts)
    .sort()
    .map((k) => `${k}: ${counts[k]}`);
  return `Ramy prediction summary | total=${total} | ${parts.join(" | ")}`;
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function loadModelStatus() {
  try {
    const status = await fetchJson("/api/model/status");
    const el = document.getElementById("model-status");
    const badge = document.getElementById("model-badge");
    if (status.ready) {
      el.textContent = `Model status: ready (${status.model_dir})`;
      el.style.color = "#86efac";
      if (badge) badge.textContent = "Model: ready";
    } else {
      el.textContent = `Model status: unavailable (${status.error || "unknown error"})`;
      el.style.color = "#fca5a5";
      if (badge) badge.textContent = "Model: unavailable";
    }
  } catch (error) {
    const el = document.getElementById("model-status");
    const badge = document.getElementById("model-badge");
    el.textContent = `Model status: error (${error.message})`;
    el.style.color = "#fca5a5";
    if (badge) badge.textContent = "Model: error";
  }
}

async function runPredictions() {
  const input = document.getElementById("predict-input").value || "";
  const comments = input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!comments.length) {
    setStatus("Add at least one comment before prediction.", true);
    return;
  }

  setStatus(`Predicting ${comments.length} comment(s)...`);
  const payload = await postJson("/api/model/predict", { comments });

  const rows = payload.rows || [];
  renderPredictRows(rows);
  renderPredictDistribution(payload.distribution || {});
  document.getElementById("predict-summary").textContent =
    `Predicted ${payload.total || 0} comment(s)`;
  window.lastPredictionRows = rows;
  setStatus("Prediction completed.");
}

function renderTable(payload) {
  const tbody = document.getElementById("reviews-body");
  tbody.innerHTML = "";

  (payload.rows || []).forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.text}</td>
      <td>${r.product}</td>
      <td>${r.category || "-"}</td>
      <td>${r.subcategory || "-"}</td>
      <td><span class="sentiment-pill sentiment-${r.sentiment}">${r.sentiment}</span></td>
    `;
    tbody.appendChild(tr);
  });

  currentPage = payload.page || 1;
  totalPages = payload.pages || 1;
  document.getElementById("page-info").textContent = `Page ${currentPage} of ${totalPages}`;
}

function fillSelect(id, values) {
  const el = document.getElementById(id);
  el.innerHTML = `<option value="">All</option>`;
  values.forEach((v) => {
    const op = document.createElement("option");
    op.value = v;
    op.textContent = v;
    el.appendChild(op);
  });
}

function readFilters() {
  state.category = document.getElementById("filter-category").value;
  state.subcategory = document.getElementById("filter-subcategory").value;
  state.product = document.getElementById("filter-product").value;
  state.sentiment = document.getElementById("filter-sentiment").value;
  state.search = document.getElementById("filter-search").value;
}

async function loadMeta() {
  const [catalog, options] = await Promise.all([
    fetchJson("/api/catalog"),
    fetchJson("/api/options"),
  ]);

  renderCatalog(catalog);
  fillSelect("filter-category", options.categories || []);
  fillSelect("filter-subcategory", options.subcategories || []);
  fillSelect("filter-product", options.products || []);
  fillSelect("filter-sentiment", options.sentiments || []);
}

async function loadDashboard() {
  readFilters();
  setStatus("Loading enterprise analytics...");

  const query = buildQuery(state);
  const reviewsQuery = buildQuery({ ...state, page: currentPage, page_size: 20 });

  const [overview, trends, aspects, reviews] = await Promise.all([
    fetchJson(`/api/overview${query}`),
    fetchJson(`/api/trends${query}`),
    fetchJson(`/api/aspects${query}`),
    fetchJson(`/api/reviews${reviewsQuery}`),
  ]);

  const total = overview.total || 0;
  const positive = overview.distribution?.positive || 0;
  const negative = overview.distribution?.negative || 0;
  const categoryCount = Object.keys(overview.categories || {}).length;

  document.getElementById("kpi-total").textContent = total.toLocaleString();
  document.getElementById("kpi-pos").textContent = pct(positive, total);
  document.getElementById("kpi-neg").textContent = pct(negative, total);
  document.getElementById("kpi-categories").textContent = `${categoryCount} Categories`;

  renderDistribution(overview.distribution || {});
  renderCategoryShare(overview.categories || {});
  renderProducts(overview.products || {});
  renderTrend(trends.series || []);
  renderAspects((aspects.rows || []).slice(0, 12));
  renderTable(reviews);

  setStatus(`Loaded ${total.toLocaleString()} reviews from enterprise dataset.`);
}

function attachEvents() {
  document.getElementById("btn-apply").addEventListener("click", async () => {
    currentPage = 1;
    try {
      await loadDashboard();
    } catch (error) {
      setStatus(`Error: ${error.message}`, true);
    }
  });

  document.getElementById("btn-reset").addEventListener("click", async () => {
    ["filter-category", "filter-subcategory", "filter-product", "filter-sentiment", "filter-search"].forEach((id) => {
      const node = document.getElementById(id);
      if (node) node.value = "";
    });
    currentPage = 1;
    try {
      await loadDashboard();
    } catch (error) {
      setStatus(`Error: ${error.message}`, true);
    }
  });

  document.getElementById("btn-export").addEventListener("click", () => {
    readFilters();
    window.open(`/api/export/reviews.csv${buildQuery(state)}`, "_blank");
  });

  document.getElementById("btn-prev").addEventListener("click", async () => {
    if (currentPage <= 1) return;
    currentPage -= 1;
    try {
      await loadDashboard();
    } catch (error) {
      setStatus(`Error: ${error.message}`, true);
    }
  });

  document.getElementById("btn-next").addEventListener("click", async () => {
    if (currentPage >= totalPages) return;
    currentPage += 1;
    try {
      await loadDashboard();
    } catch (error) {
      setStatus(`Error: ${error.message}`, true);
    }
  });

  document.getElementById("btn-predict").addEventListener("click", async () => {
    try {
      await runPredictions();
    } catch (error) {
      setStatus(`Prediction error: ${error.message}`, true);
    }
  });

  document.getElementById("btn-clear-predict").addEventListener("click", () => {
    document.getElementById("predict-input").value = "";
    document.getElementById("predict-body").innerHTML = "";
    document.getElementById("predict-summary").textContent = "No predictions yet";
    window.lastPredictionRows = [];
    Plotly.purge("predict-dist-chart");
  });

  document.querySelectorAll(".sample-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.dataset.text || "";
      const input = document.getElementById("predict-input");
      const current = input.value.trim();
      input.value = current ? `${current}\n${text}` : text;
      input.focus();
    });
  });

  document.getElementById("btn-export-predict").addEventListener("click", () => {
    const rows = window.lastPredictionRows || [];
    if (!rows.length) {
      setStatus("No predictions available to export.", true);
      return;
    }
    downloadTextFile("ramy_predictions.csv", toCsv(rows));
    setStatus("Prediction CSV exported.");
  });

  document.getElementById("btn-copy-predict").addEventListener("click", async () => {
    const rows = window.lastPredictionRows || [];
    if (!rows.length) {
      setStatus("No predictions available to summarize.", true);
      return;
    }
    const summary = buildPredictionSummary(rows);
    try {
      await navigator.clipboard.writeText(summary);
      setStatus("Prediction summary copied to clipboard.");
    } catch (_) {
      setStatus(summary);
    }
  });

  document.getElementById("predict-file").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const normalized = text
        .split(/\r?\n/)
        .map((line) => line.split(";")[0].trim())
        .filter(Boolean)
        .join("\n");
      document.getElementById("predict-input").value = normalized;
      setStatus(`Loaded ${file.name} into prediction box.`);
    } catch (error) {
      setStatus(`Could not read file: ${error.message}`, true);
    }
  });
}

async function boot() {
  try {
    setStatus("Initializing enterprise portal...");
    window.lastPredictionRows = [];
    await loadMeta();
    attachEvents();
    await loadDashboard();
    await loadModelStatus();
  } catch (error) {
    console.error(error);
    setStatus(`Startup failed: ${error.message}`, true);
  }
}

boot();
