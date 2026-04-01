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
}

async function boot() {
  try {
    setStatus("Initializing enterprise portal...");
    await loadMeta();
    attachEvents();
    await loadDashboard();
  } catch (error) {
    console.error(error);
    setStatus(`Startup failed: ${error.message}`, true);
  }
}

boot();
