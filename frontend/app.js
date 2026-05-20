const state = {
  products: new Map(),
  stores: new Map(),
  suppliers: new Map(),
};

const $ = (id) => document.getElementById(id);

function unwrap(payload) {
  if (!payload.success) {
    throw new Error(payload.message || "接口请求失败");
  }
  return payload.data;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return unwrap(await response.json());
}

function fmt(value) {
  const numeric = Number(value || 0);
  return numeric.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

function clampText(value, fallback) {
  if (!value) return fallback;
  return String(value).replace(/\s+/g, " ").trim();
}

function productName(id) {
  const item = state.products.get(id);
  return item ? clampText(item.name, `商品 ${id}`) : `商品 ${id}`;
}

function storeName(id) {
  const item = state.stores.get(id);
  return item ? clampText(item.name, `门店 ${id}`) : `门店 ${id}`;
}

function supplierName(id) {
  const item = state.suppliers.get(id);
  return item ? clampText(item.name, `供应商 ${id}`) : id ? `供应商 ${id}` : "待分配";
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2400);
}

function renderBars(targetId, rows, labelKey, valueKey, limit = 10) {
  const target = $(targetId);
  const visible = rows.slice(0, limit);
  const max = Math.max(...visible.map((item) => Number(item[valueKey] || 0)), 1);
  if (!visible.length) {
    target.innerHTML = '<div class="empty-state">暂无可展示数据</div>';
    return;
  }
  target.innerHTML = visible
    .map((item) => {
      const value = Number(item[valueKey] || 0);
      const width = Math.max(4, Math.round((value / max) * 100));
      return `
        <div class="bar-row">
          <span class="bar-label" title="${clampText(item[labelKey], "未命名")}">${clampText(item[labelKey], "未命名")}</span>
          <span class="bar-track"><span class="bar-fill" style="width:${width}%"></span></span>
          <span class="bar-value">${fmt(value)}</span>
        </div>
      `;
    })
    .join("");
}

function renderWarnings(rows) {
  const target = $("warningList");
  $("warningBadge").textContent = `${rows.length} 条`;
  const visible = rows.slice(0, 7);
  if (!visible.length) {
    target.innerHTML = '<div class="empty-state">当前没有库存预警</div>';
    return;
  }
  target.innerHTML = visible
    .map((item) => {
      const product = productName(item.product_id);
      const location = item.store_id ? storeName(item.store_id) : `仓库 ${item.warehouse_id || "-"}`;
      const warningType = item.warning_type || "low";
      const current = item.current_quantity ?? item.current_stock ?? 0;
      const safety = item.safety_stock ?? 0;
      return `
        <div class="warning-item">
          <span class="risk-dot ${warningType}"></span>
          <div>
            <span class="item-title">${product}</span>
            <span class="item-meta">${location} 当前 ${fmt(current)} / 安全库存 ${fmt(safety)}</span>
          </div>
          <span class="pill ${warningType.includes("stockout") ? "danger" : ""}">${warningType}</span>
        </div>
      `;
    })
    .join("");
}

function renderRecommendations(rows) {
  const target = $("recommendationList");
  const priority = { high: 0, medium: 1, low: 2 };
  const visible = [...rows]
    .sort((a, b) => (priority[a.risk_level] ?? 3) - (priority[b.risk_level] ?? 3))
    .slice(0, 6);
  if (!visible.length) {
    target.innerHTML = '<div class="empty-state">暂无补货建议，点击右上角生成</div>';
    return;
  }
  target.innerHTML = visible
    .map((item) => {
      const reason = clampText(item.reason_enhanced || item.reason, "根据库存与销量生成补货建议");
      return `
        <div class="recommendation-item">
          <div class="recommendation-top">
            <div>
              <span class="item-title">${storeName(item.store_id)} · ${productName(item.product_id)}</span>
              <span class="item-meta">当前 ${fmt(item.current_stock)}，安全库存 ${fmt(item.safety_stock)}，预计 ${Number(item.days_until_stockout || 0).toFixed(1)} 天后缺货</span>
            </div>
            <span class="recommendation-qty">${fmt(item.recommended_quantity)}</span>
          </div>
          <span class="item-meta">推荐供应商：${supplierName(item.recommended_supplier_id)} · 风险等级：${item.risk_level}</span>
          <span class="item-meta">${reason}</span>
        </div>
      `;
    })
    .join("");
}

function renderHeatmap(rows) {
  const target = $("heatmapGrid");
  const visible = rows.slice(0, 8);
  const max = Math.max(...visible.map((item) => Number(item.retail_sales || 0)), 1);
  if (!visible.length) {
    target.innerHTML = '<div class="empty-state">暂无门店需求数据</div>';
    return;
  }
  target.innerHTML = visible
    .map((item) => {
      const ratio = Number(item.retail_sales || 0) / max;
      const alpha = 0.58 + ratio * 0.34;
      return `
        <div class="heat-cell" style="background: linear-gradient(135deg, rgba(29,100,167,${alpha}), rgba(23,184,198,${0.72 + ratio * 0.22}))">
          <span title="${clampText(item.store_name, "未命名门店")}">${clampText(item.store_name, "未命名门店")}</span>
          <strong>${fmt(item.retail_sales)}</strong>
          <span>需求热度</span>
        </div>
      `;
    })
    .join("");
}

function hydrateLookup(list, map) {
  map.clear();
  for (const item of list) {
    map.set(item.id, item);
  }
}

async function loadLookups() {
  const [products, stores, suppliers] = await Promise.all([
    api("/api/products?page=1&page_size=200"),
    api("/api/stores?page=1&page_size=100"),
    api("/api/suppliers?page=1&page_size=100"),
  ]);
  hydrateLookup(products.items || [], state.products);
  hydrateLookup(stores.items || [], state.stores);
  hydrateLookup(suppliers.items || [], state.suppliers);
}

async function loadDashboard() {
  $("systemStatus").textContent = "连接中";
  const [dashboard, ranking, warnings, recommendations, heatmap, suppliers, turnover] = await Promise.all([
    api("/api/analytics/dashboard"),
    api("/api/analytics/inventory-ranking"),
    api("/api/inventory/warnings"),
    api("/api/recommendations"),
    api("/api/analytics/store-demand-heatmap"),
    api("/api/analytics/supplier-purchase-ranking"),
    api("/api/analytics/product-turnover"),
  ]);

  $("productCount").textContent = fmt(dashboard.product_count);
  $("supplierCount").textContent = fmt(dashboard.supplier_count);
  $("stockoutCount").textContent = fmt(dashboard.stockout_count);
  $("recommendationCount").textContent = fmt(dashboard.ai_recommendation_count);
  $("systemStatus").textContent = "运行正常";
  $("statusDetail").textContent = `库存 ${fmt(dashboard.total_inventory_quantity)} 件，门店 ${fmt(dashboard.store_count)} 个`;

  renderBars("inventoryBars", ranking, "product_name", "quantity", 10);
  renderWarnings(warnings);
  renderRecommendations(recommendations);
  renderHeatmap(heatmap);
  renderBars("supplierBars", suppliers, "supplier_name", "total_purchase_amount", 8);
  renderBars("turnoverBars", turnover, "product_name", "avg_monthly_sales", 8);
}

async function refreshAll() {
  try {
    await loadLookups();
    await loadDashboard();
    showToast("数据已刷新");
  } catch (error) {
    $("systemStatus").textContent = "连接异常";
    $("statusDetail").textContent = "请确认后端服务已启动";
    showToast(error.message || "读取数据失败");
  }
}

async function generateRecommendations() {
  const button = $("generateBtn");
  button.disabled = true;
  button.textContent = "生成中...";
  try {
    const result = await api("/api/recommendations/generate", { method: "POST" });
    await loadDashboard();
    showToast(`已生成 ${fmt(result.count)} 条补货建议`);
  } catch (error) {
    showToast(error.message || "生成失败");
  } finally {
    button.disabled = false;
    button.textContent = "生成补货建议";
  }
}

$("refreshBtn").addEventListener("click", refreshAll);
$("generateBtn").addEventListener("click", generateRecommendations);

refreshAll();
