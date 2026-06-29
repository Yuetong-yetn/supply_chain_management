(function () {
  "use strict";

  const API = window.SupplyAPI;
  const state = {
    currentView: "dashboard",
    currentUser: null,
    eventsBound: false,
    products: new Map(),
    suppliers: new Map(),
    warehouses: new Map(),
    stores: new Map(),
    charts: new Map(),
  };

  const viewLoaders = {
    dashboard: loadDashboard,
    data: loadBaseData,
    warnings: loadWarnings,
    inbound: loadInbound,
    fulfillment: loadFulfillment,
    transactions: loadTransactions,
    recommendations: loadRecommendations,
    suppliers: loadSupplierAnalytics,
    system: loadSystemStatus,
  };

  const statusLabels = {
    pending: "待处理",
    confirmed: "已确认",
    partial_received: "部分到货",
    completed: "已完成",
    approved: "已通过",
    converted: "已转出库",
    rejected: "已拒绝",
    shipped: "已发货",
    signed: "已签收",
    cancelled: "已取消",
    accepted: "已采纳",
    critical_stockout: "严重缺货",
    stockout: "库存不足",
    overstock: "库存积压",
    high: "高风险",
    medium: "中风险",
    low: "低风险",
    warehouse: "仓库",
    store: "门店",
    purchase_inbound: "采购入库",
    outbound: "出库",
    store_outbound: "门店补货出库",
    adjustment: "库存调整",
    inbound_order: "入库单",
    outbound_order: "出库单",
    example_seed: "示例数据",
  };

  const roleLabels = {
    admin: "系统管理员",
    buyer: "采购专员",
    warehouse_manager: "仓库主管",
    store_staff: "门店员工",
    manager: "运营经理",
  };

  const $ = (id) => document.getElementById(id);

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function listItems(data) {
    if (Array.isArray(data)) return data;
    return Array.isArray(data?.items) ? data.items : [];
  }

  function formatNumber(value, maximumFractionDigits = 0) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "--";
    return number.toLocaleString("zh-CN", { maximumFractionDigits });
  }

  function formatTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return escapeHtml(value);
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }

  function label(value) {
    return statusLabels[value] || value || "--";
  }

  function nameFrom(map, id, fallback) {
    return map.get(Number(id))?.name || `${fallback} ${id ?? "--"}`;
  }

  function productName(id) {
    return nameFrom(state.products, id, "商品");
  }

  function supplierName(id) {
    return nameFrom(state.suppliers, id, "供应商");
  }

  function warehouseName(id) {
    return nameFrom(state.warehouses, id, "仓库");
  }

  function storeName(id) {
    return nameFrom(state.stores, id, "门店");
  }

  function statusBadge(status) {
    return `<span class="status-badge status-${escapeHtml(status || "unknown")}">${escapeHtml(label(status))}</span>`;
  }

  function emptyRow(colspan, message) {
    return `<tr><td colspan="${colspan}"><div class="table-empty">${escapeHtml(message)}</div></td></tr>`;
  }

  function setText(id, value) {
    const element = $(id);
    if (element) element.textContent = value;
  }

  function showAlert(message, type = "danger") {
    const alert = $("pageAlert");
    alert.className = `page-alert ${type}`;
    alert.textContent = message;
    alert.hidden = false;
  }

  function clearAlert() {
    $("pageAlert").hidden = true;
  }

  function showToast(message, type = "success") {
    const container = $("toastContainer");
    const toast = document.createElement("div");
    toast.className = `app-toast toast-${type}`;
    toast.setAttribute("role", "status");
    toast.innerHTML = `
      <span class="toast-mark">${type === "success" ? "✓" : "!"}</span>
      <div><strong>${type === "success" ? "操作成功" : "操作失败"}</strong><span>${escapeHtml(message)}</span></div>
      <button type="button" aria-label="关闭提示">×</button>
    `;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("show"));
    const close = () => {
      toast.classList.remove("show");
      window.setTimeout(() => toast.remove(), 220);
    };
    toast.querySelector("button").addEventListener("click", close);
    window.setTimeout(close, 3600);
  }

  function setButtonLoading(button, loading, loadingText = "处理中…") {
    if (!button) return;
    const labelElement = button.querySelector(".btn-label");
    if (loading) {
      button.dataset.originalLabel = labelElement?.textContent || button.textContent;
      button.disabled = true;
      button.classList.add("is-loading");
      if (labelElement) labelElement.textContent = loadingText;
      else button.textContent = loadingText;
    } else {
      const original = button.dataset.originalLabel;
      button.disabled = false;
      button.classList.remove("is-loading");
      if (original) {
        if (labelElement) labelElement.textContent = original;
        else button.textContent = original;
      }
      delete button.dataset.originalLabel;
    }
  }

  async function runButtonAction(button, action, options = {}) {
    setButtonLoading(button, true, options.loadingText);
    clearAlert();
    try {
      const result = await action();
      if (options.successMessage) {
        const message =
          typeof options.successMessage === "function"
            ? options.successMessage(result)
            : options.successMessage;
        showToast(message);
      }
      return result;
    } catch (error) {
      const message = error?.message || "操作失败，请稍后重试";
      showAlert(message);
      showToast(message, "error");
      return null;
    } finally {
      setButtonLoading(button, false);
    }
  }

  async function loadLookups() {
    const tasks = [
      [API.getProducts, state.products],
      [API.getSuppliers, state.suppliers],
      [API.getWarehouses, state.warehouses],
      [API.getStores, state.stores],
    ];
    const results = await Promise.allSettled(tasks.map(([loader]) => loader()));
    results.forEach((result, index) => {
      if (result.status !== "fulfilled") return;
      const map = tasks[index][1];
      map.clear();
      listItems(result.value).forEach((item) => map.set(Number(item.id), item));
    });
    populateBusinessSelects();
  }

  function populateSelect(id, items, placeholder) {
    const select = $(id);
    if (!select) return;
    const currentValue = select.value;
    select.innerHTML = items.length
      ? items
          .map(
            (item) =>
              `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`,
          )
          .join("")
      : `<option value="">${escapeHtml(placeholder)}</option>`;
    if (items.some((item) => String(item.id) === currentValue)) {
      select.value = currentValue;
    }
  }

  function populateBusinessSelects() {
    const products = [...state.products.values()];
    populateSelect("inboundSupplier", [...state.suppliers.values()], "暂无供应商");
    populateSelect("inboundWarehouse", [...state.warehouses.values()], "暂无仓库");
    populateSelect("inboundProduct", products, "暂无商品");
    populateSelect("requestStore", [...state.stores.values()], "暂无门店");
    populateSelect("requestProduct", products, "暂无商品");
  }

  async function loadBaseData() {
    await loadLookups();
    setText("dataProductCount", formatNumber(state.products.size));
    setText("dataSupplierCount", formatNumber(state.suppliers.size));
    setText("dataWarehouseCount", formatNumber(state.warehouses.size));
    setText("dataStoreCount", formatNumber(state.stores.size));
  }

  function updateChart(id, option) {
    const target = $(id);
    if (!target) return;
    if (!window.echarts) {
      target.innerHTML = '<div class="empty-block">图表组件未加载，请检查网络后刷新</div>';
      return;
    }
    let chart = state.charts.get(id);
    if (!chart) {
      target.innerHTML = "";
      chart = window.echarts.init(target);
      state.charts.set(id, chart);
    }
    chart.setOption(option, true);
  }

  function baseChartOption() {
    return {
      animationDuration: 500,
      textStyle: { fontFamily: '"Microsoft YaHei", "PingFang SC", sans-serif' },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(22, 32, 51, .94)",
        borderWidth: 0,
        textStyle: { color: "#fff" },
      },
      grid: { left: 18, right: 26, top: 20, bottom: 12, containLabel: true },
    };
  }

  async function loadDashboard() {
    const [dashboard, ranking, warnings, recommendations] = await Promise.all([
      API.getDashboard(),
      API.getInventoryRanking(),
      API.getWarnings(),
      API.getRecommendations(),
    ]);
    setText("metricProducts", formatNumber(dashboard.product_count));
    setText("metricSuppliers", formatNumber(dashboard.supplier_count));
    setText("metricWarehouses", formatNumber(dashboard.warehouse_count));
    setText("metricStores", formatNumber(dashboard.store_count));
    setText("metricInventory", formatNumber(dashboard.total_inventory_quantity));
    setText("metricStockout", formatNumber(dashboard.stockout_count));
    setText("metricOverstock", formatNumber(dashboard.overstock_count));
    setText(
      "metricWarnings",
      formatNumber(Number(dashboard.stockout_count || 0) + Number(dashboard.overstock_count || 0)),
    );
    setText("metricOutbound", formatNumber(dashboard.recent_outbound_quantity));
    setText("metricRecommendations", formatNumber(dashboard.ai_recommendation_count));
    setText("metricHighRisk", formatNumber(dashboard.high_risk_recommendation_count));
    setText("dashboardUpdatedAt", new Date().toLocaleTimeString("zh-CN", { hour12: false }));

    const rankingRows = listItems(ranking).slice(0, 10);
    updateChart("dashboardInventoryChart", {
      ...baseChartOption(),
      xAxis: {
        type: "value",
        axisLabel: { color: "#7a879c" },
        splitLine: { lineStyle: { color: "#edf1f7" } },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: rankingRows.map((item) => item.product_name),
        axisLabel: { color: "#4d5b70", width: 90, overflow: "truncate" },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          name: "库存数量",
          type: "bar",
          data: rankingRows.map((item) => Number(item.quantity || 0)),
          barWidth: 13,
          itemStyle: {
            borderRadius: [0, 7, 7, 0],
            color: new window.echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: "#5667e8" },
              { offset: 1, color: "#8b7cf6" },
            ]),
          },
        },
      ],
    });

    renderDashboardRisks(listItems(warnings));
    renderDashboardRecommendations(listItems(recommendations));
  }

  function renderDashboardRisks(rows) {
    const target = $("dashboardRiskList");
    if (!rows.length) {
      target.innerHTML = '<div class="empty-block success-empty">当前没有库存预警</div>';
      return;
    }
    target.innerHTML = rows
      .slice(0, 5)
      .map(
        (item) => `
          <div class="compact-risk">
            <span class="risk-bar ${escapeHtml(item.warning_type)}"></span>
            <div>
              <strong>${escapeHtml(item.product_name || productName(item.product_id))}</strong>
              <small>${escapeHtml(item.location_name || label(item.location_type))}</small>
            </div>
            <div class="risk-value">
              <strong>${formatNumber(item.available_quantity ?? item.current_quantity)}</strong>
              <small>安全 ${formatNumber(item.safety_stock)}</small>
            </div>
          </div>`,
      )
      .join("");
  }

  function renderDashboardRecommendations(rows) {
    const target = $("dashboardRecommendationList");
    if (!rows.length) {
      target.innerHTML = '<div class="empty-block">暂无补货建议</div>';
      return;
    }
    const riskOrder = { high: 0, medium: 1, low: 2 };
    target.innerHTML = [...rows]
      .sort((a, b) => (riskOrder[a.risk_level] ?? 3) - (riskOrder[b.risk_level] ?? 3))
      .slice(0, 4)
      .map(
        (item) => `
          <div class="dashboard-recommendation">
            <div>
              ${statusBadge(item.risk_level)}
              <strong>${escapeHtml(productName(item.product_id))}</strong>
              <small>${escapeHtml(storeName(item.store_id))}</small>
            </div>
            <div class="dashboard-recommendation-quantity">
              <span>建议补货</span>
              <strong>${formatNumber(item.recommended_quantity)}</strong>
            </div>
          </div>`,
      )
      .join("");
  }

  async function loadWarnings() {
    const rows = listItems(await API.getWarnings());
    const critical = rows.filter((item) => item.warning_type === "critical_stockout").length;
    const stockout = rows.filter((item) => item.warning_type === "stockout").length;
    const overstock = rows.filter((item) => item.warning_type === "overstock").length;
    setText("warningCriticalCount", formatNumber(critical));
    setText("warningStockoutCount", formatNumber(stockout));
    setText("warningOverstockCount", formatNumber(overstock));
    setText("warningTotalCount", formatNumber(rows.length));
    setText("warningResultBadge", `${rows.length} 条记录`);

    $("warningTableBody").innerHTML = rows.length
      ? rows
          .map(
            (item) => `
              <tr>
                <td>${statusBadge(item.warning_type)}</td>
                <td><strong>${escapeHtml(item.product_name || productName(item.product_id))}</strong><small class="cell-subtitle">ID ${escapeHtml(item.product_id)}</small></td>
                <td>${escapeHtml(item.location_name || label(item.location_type))}<small class="cell-subtitle">${escapeHtml(label(item.location_type))}</small></td>
                <td class="number-cell">${formatNumber(item.current_quantity)}</td>
                <td class="number-cell">${formatNumber(item.available_quantity ?? Number(item.current_quantity || 0) - Number(item.frozen_quantity || 0))}</td>
                <td>${formatNumber(item.safety_stock)} / ${formatNumber(item.max_stock)}</td>
                <td class="message-cell">${escapeHtml(item.warning_message || "库存达到预警阈值")}</td>
              </tr>`,
          )
          .join("")
      : emptyRow(7, "当前没有库存预警");
  }

  function itemSummary(items) {
    if (!Array.isArray(items) || !items.length) return "暂无明细";
    const total = items.reduce((sum, item) => sum + Number(item.quantity || 0), 0);
    const names = items
      .slice(0, 2)
      .map((item) => productName(item.product_id))
      .join("、");
    return `${names}${items.length > 2 ? ` 等 ${items.length} 项` : ""} · ${formatNumber(total)} 件`;
  }

  async function loadInbound() {
    const rows = listItems(await API.getInboundOrders());
    setText("inboundResultBadge", `${rows.length} 张单据`);
    $("inboundTableBody").innerHTML = rows.length
      ? rows
          .map(
            (item) => `
              <tr>
                <td><strong>${escapeHtml(item.inbound_no)}</strong><small class="cell-subtitle">ID ${escapeHtml(item.id)}</small></td>
                <td>${item.purchase_order_id ? `PO #${escapeHtml(item.purchase_order_id)}` : "--"}</td>
                <td>${escapeHtml(supplierName(item.supplier_id))}</td>
                <td>${escapeHtml(warehouseName(item.warehouse_id))}</td>
                <td>${escapeHtml(itemSummary(item.items))}</td>
                <td>${statusBadge(item.status)}</td>
                <td>${formatTime(item.inbound_time)}</td>
                <td>
                  ${
                    item.status === "pending"
                      ? `<button class="btn btn-sm btn-primary row-action" type="button" data-action="complete-inbound" data-id="${item.id}"><span class="btn-label">完成入库</span></button>`
                      : '<span class="done-text">已处理</span>'
                  }
                </td>
              </tr>`,
          )
          .join("")
      : emptyRow(8, "暂无入库单，请先导入演示数据");
  }

  async function loadFulfillment() {
    const [requests, outbounds] = await Promise.all([
      API.getReplenishmentRequests(),
      API.getOutboundOrders(),
    ]);
    renderRequests(listItems(requests));
    renderOutbounds(listItems(outbounds));
  }

  function renderRequests(rows) {
    setText("requestResultBadge", `${rows.length} 张申请`);
    $("requestTableBody").innerHTML = rows.length
      ? rows
          .map((item) => {
            let action = '<span class="done-text">无需操作</span>';
            if (item.audit_status === "pending") {
              action = `<button class="btn btn-sm btn-primary row-action" type="button" data-action="approve-request" data-id="${item.id}"><span class="btn-label">审核通过</span></button>`;
            } else if (item.audit_status === "approved" && !item.generated_outbound_order_id) {
              action = `<button class="btn btn-sm btn-primary row-action" type="button" data-action="convert-request" data-id="${item.id}"><span class="btn-label">转出库单</span></button>`;
            }
            return `
              <tr>
                <td><strong>${escapeHtml(item.request_no)}</strong><small class="cell-subtitle">ID ${escapeHtml(item.id)}</small></td>
                <td>${escapeHtml(storeName(item.store_id))}</td>
                <td>${escapeHtml(productName(item.product_id))}</td>
                <td class="number-cell">${formatNumber(item.request_quantity)}</td>
                <td class="message-cell">${escapeHtml(item.request_reason || "--")}</td>
                <td>${statusBadge(item.audit_status)}</td>
                <td>${item.generated_outbound_order_id ? `#${escapeHtml(item.generated_outbound_order_id)}` : "--"}</td>
                <td>${action}</td>
              </tr>`;
          })
          .join("")
      : emptyRow(8, "暂无补货申请，请先导入演示数据");
  }

  function renderOutbounds(rows) {
    setText("outboundResultBadge", `${rows.length} 张单据`);
    $("outboundTableBody").innerHTML = rows.length
      ? rows
          .map((item) => {
            let action = '<span class="done-text">履约完成</span>';
            if (item.status === "pending") {
              action = `<button class="btn btn-sm btn-primary row-action" type="button" data-action="ship-outbound" data-id="${item.id}"><span class="btn-label">出库发货</span></button>`;
            } else if (item.status === "shipped") {
              action = `<button class="btn btn-sm btn-primary row-action" type="button" data-action="sign-outbound" data-id="${item.id}"><span class="btn-label">门店签收</span></button>`;
            } else if (item.status === "cancelled") {
              action = '<span class="done-text">已取消</span>';
            }
            return `
              <tr>
                <td><strong>${escapeHtml(item.outbound_no)}</strong><small class="cell-subtitle">ID ${escapeHtml(item.id)}</small></td>
                <td>${escapeHtml(warehouseName(item.source_warehouse_id))}</td>
                <td>${escapeHtml(storeName(item.target_store_id))}</td>
                <td>${escapeHtml(itemSummary(item.items))}</td>
                <td>${item.source_request_id ? `RR #${escapeHtml(item.source_request_id)}` : "--"}</td>
                <td>${statusBadge(item.status)}</td>
                <td>${formatTime(item.outbound_time)}</td>
                <td>${action}</td>
              </tr>`;
          })
          .join("")
      : emptyRow(8, "暂无出库单，审核补货申请后可生成");
  }

  async function loadTransactions() {
    const rows = listItems(await API.getTransactions());
    setText("transactionResultBadge", `${rows.length} 条流水`);
    $("transactionTableBody").innerHTML = rows.length
      ? [...rows]
          .sort((a, b) => new Date(b.transaction_time) - new Date(a.transaction_time))
          .map((item) => {
            const quantity = Number(item.change_quantity || 0);
            return `
              <tr>
                <td><strong>${escapeHtml(item.transaction_no)}</strong></td>
                <td>${escapeHtml(productName(item.product_id))}<small class="cell-subtitle">ID ${escapeHtml(item.product_id)}</small></td>
                <td>${statusBadge(item.transaction_type)}</td>
                <td class="number-cell ${quantity >= 0 ? "quantity-positive" : "quantity-negative"}">${quantity > 0 ? "+" : ""}${formatNumber(quantity)}</td>
                <td class="number-cell">${formatNumber(item.before_quantity)}</td>
                <td class="number-cell">${formatNumber(item.after_quantity)}</td>
                <td>${escapeHtml(label(item.related_doc_type))} #${escapeHtml(item.related_doc_id ?? "--")}</td>
                <td>${formatTime(item.transaction_time)}</td>
              </tr>`;
          })
          .join("")
      : emptyRow(8, "暂无库存流水");
  }

  async function loadRecommendations() {
    const rows = listItems(await API.getRecommendations());
    const highRisk = rows.filter((item) => item.risk_level === "high").length;
    const totalQuantity = rows.reduce(
      (sum, item) => sum + Math.max(0, Number(item.recommended_quantity || 0)),
      0,
    );
    setText("recommendationTotal", formatNumber(rows.length));
    setText("recommendationHigh", formatNumber(highRisk));
    setText("recommendationQuantity", formatNumber(totalQuantity));

    const riskOrder = { high: 0, medium: 1, low: 2 };
    const sorted = [...rows].sort(
      (a, b) => (riskOrder[a.risk_level] ?? 3) - (riskOrder[b.risk_level] ?? 3),
    );
    $("recommendationGrid").innerHTML = sorted.length
      ? sorted
          .map(
            (item) => `
              <article class="recommendation-card risk-${escapeHtml(item.risk_level)}">
                <div class="recommendation-head">
                  <div>
                    ${statusBadge(item.risk_level)}
                    <h3>${escapeHtml(storeName(item.store_id))} · ${escapeHtml(productName(item.product_id))}</h3>
                  </div>
                  <div class="recommendation-number"><span>建议补货</span><strong>${formatNumber(item.recommended_quantity)}</strong></div>
                </div>
                <div class="recommendation-stats">
                  <div><span>当前库存</span><strong>${formatNumber(item.current_stock)}</strong></div>
                  <div><span>安全库存</span><strong>${formatNumber(item.safety_stock)}</strong></div>
                  <div><span>近 7 天出库</span><strong>${formatNumber(item.recent_7_sales, 1)}</strong></div>
                  <div><span>预计缺货</span><strong>${item.days_until_stockout == null ? "--" : `${formatNumber(item.days_until_stockout, 1)} 天`}</strong></div>
                </div>
                <p>${escapeHtml(item.reason_enhanced || item.reason || "暂无推荐理由")}</p>
                <footer>
                  <span>推荐：${escapeHtml(supplierName(item.recommended_supplier_id))}</span>
                  <span>${item.llm_used ? "LLM 增强" : "规则模型"}</span>
                </footer>
              </article>`,
          )
          .join("")
      : '<div class="empty-block large-empty">暂无补货建议，点击“生成补货建议”开始分析</div>';
  }

  async function loadSupplierAnalytics() {
    const [ranking, trend] = await Promise.all([
      API.getSupplierRanking(),
      API.getWarehouseFlowTrend(),
    ]);
    const rankingRows = listItems(ranking)
      .map((item) => ({ ...item, score: Number(item.score || 0) }))
      .sort((a, b) => b.score - a.score);
    const trendRows = listItems(trend);
    setText("supplierResultBadge", `${rankingRows.length} 家供应商`);

    $("supplierTableBody").innerHTML = rankingRows.length
      ? rankingRows
          .map(
            (item, index) => `
              <tr>
                <td><span class="rank-number rank-${index + 1}">${index + 1}</span></td>
                <td><strong>${escapeHtml(supplierName(item.supplier_id))}</strong><small class="cell-subtitle">ID ${escapeHtml(item.supplier_id)}</small></td>
                <td><strong class="score-value">${formatNumber(item.score, 1)}</strong></td>
                <td class="message-cell">${escapeHtml(item.score_source || "--")}</td>
                <td>${scoreEvaluation(item.score)}</td>
              </tr>`,
          )
          .join("")
      : emptyRow(5, "暂无供应商评分，请先计算评分");

    updateChart("supplierScoreChart", {
      ...baseChartOption(),
      xAxis: {
        type: "value",
        max: 100,
        axisLabel: { color: "#7a879c" },
        splitLine: { lineStyle: { color: "#edf1f7" } },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: rankingRows.slice(0, 8).map((item) => supplierName(item.supplier_id)),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: "#4d5b70", width: 100, overflow: "truncate" },
      },
      series: [
        {
          type: "bar",
          data: rankingRows.slice(0, 8).map((item) => item.score),
          barWidth: 13,
          itemStyle: { color: "#7567e8", borderRadius: [5, 5, 5, 5] },
        },
      ],
    });

    const xLabels = trendRows.map(
      (item) => `${item.year}-${String(item.month).padStart(2, "0")} ${item.warehouse_name}`,
    );
    updateChart("warehouseTrendChart", {
      ...baseChartOption(),
      xAxis: {
        type: "category",
        data: xLabels,
        axisLabel: { color: "#7a879c", rotate: xLabels.length > 5 ? 25 : 0 },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "#dfe5ef" } },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#7a879c" },
        splitLine: { lineStyle: { color: "#edf1f7" } },
      },
      series: [
        {
          name: "出入库量",
          type: "line",
          smooth: true,
          data: trendRows.map((item) => Number(item.warehouse_sales || 0)),
          lineStyle: { color: "#22a981", width: 3 },
          itemStyle: { color: "#5667e8" },
          areaStyle: { color: "rgba(34, 169, 129, .10)" },
        },
      ],
    });
  }

  function scoreEvaluation(score) {
    if (score >= 90) return '<span class="status-badge status-completed">优秀</span>';
    if (score >= 75) return '<span class="status-badge status-approved">良好</span>';
    if (score >= 60) return '<span class="status-badge status-pending">合格</span>';
    return '<span class="status-badge status-rejected">待改进</span>';
  }

  function setSystemCard(cardId, statusId, detailId, ok, status, detail) {
    const card = $(cardId);
    card.classList.toggle("is-ok", ok);
    card.classList.toggle("is-error", !ok);
    setText(statusId, status);
    setText(detailId, detail);
  }

  async function loadSystemStatus() {
    const [healthResult, databaseResult, exampleResult] = await Promise.allSettled([
      API.getHealth(),
      API.getDatabaseHealth(),
      API.getExampleStatus(),
    ]);

    if (healthResult.status === "fulfilled") {
      const health = healthResult.value;
      setSystemCard(
        "backendHealthCard",
        "backendHealthStatus",
        "backendHealthDetail",
        true,
        "运行正常",
        `${health.app || "Supply Chain Management"} · ${health.database || "connected"}`,
      );
      setText("systemAppName", health.app || "Supply Chain Management");
      $("globalStatusDot").className = "status-dot is-online";
      setText("globalStatusText", "系统运行正常");
      setText("globalStatusDetail", "后端服务已连接");
    } else {
      setSystemCard(
        "backendHealthCard",
        "backendHealthStatus",
        "backendHealthDetail",
        false,
        "连接失败",
        healthResult.reason?.message || "无法连接后端",
      );
      $("globalStatusDot").className = "status-dot is-offline";
      setText("globalStatusText", "系统连接异常");
      setText("globalStatusDetail", healthResult.reason?.message || "请启动后端服务");
    }

    if (databaseResult.status === "fulfilled") {
      const database = databaseResult.value;
      setSystemCard(
        "databaseHealthCard",
        "databaseHealthStatus",
        "databaseHealthDetail",
        true,
        "连接正常",
        `${database.dialect || "--"} · ${database.status || "connected"}`,
      );
      setText("systemDialect", database.dialect || "--");
      setText("systemDatabaseUrl", database.database_url_masked || "--");
    } else {
      setSystemCard(
        "databaseHealthCard",
        "databaseHealthStatus",
        "databaseHealthDetail",
        false,
        "接口暂不可用",
        databaseResult.reason?.message || "数据库状态接口尚未实现",
      );
      setText("systemDialect", "等待后端接口");
      setText("systemDatabaseUrl", "--");
    }

    if (exampleResult.status === "fulfilled") {
      const example = exampleResult.value;
      setSystemCard(
        "exampleHealthCard",
        "exampleHealthStatus",
        "exampleHealthDetail",
        true,
        "数据已就绪",
        `${formatNumber(example.products)} 商品 · ${formatNumber(example.stores)} 门店 · ${formatNumber(example.stock_transactions)} 流水`,
      );
    } else {
      setSystemCard(
        "exampleHealthCard",
        "exampleHealthStatus",
        "exampleHealthDetail",
        false,
        "状态未知",
        exampleResult.reason?.message || "无法读取演示数据状态",
      );
    }

    const allOk =
      healthResult.status === "fulfilled" &&
      databaseResult.status === "fulfilled" &&
      exampleResult.status === "fulfilled";
    const badge = $("connectionBadge");
    badge.className = `status-badge ${allOk ? "status-completed" : "status-pending"}`;
    badge.textContent = allOk ? "全部正常" : "部分功能待就绪";
  }

  function switchView(viewName) {
    if (!viewLoaders[viewName]) return;
    state.currentView = viewName;
    document.querySelectorAll(".app-view").forEach((view) => {
      view.classList.toggle("active", view.id === `view-${viewName}`);
    });
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.view === viewName);
    });
    setText("pageTitle", $(`view-${viewName}`).dataset.title);
    clearAlert();
    closeMobileMenu();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function closeMobileMenu() {
    $("appSidebar").classList.remove("is-open");
    $("mobileMenuBtn").setAttribute("aria-expanded", "false");
  }

  async function refreshView(viewName, button, successMessage = "数据已刷新") {
    await runButtonAction(button, () => viewLoaders[viewName](), {
      loadingText: "加载中…",
      successMessage,
    });
  }

  async function handleRowAction(button) {
    const id = Number(button.dataset.id);
    const action = button.dataset.action;
    const configurations = {
      "complete-inbound": {
        request: () => API.completeInbound(id),
        success: "入库完成，库存与流水已更新",
        reload: () => Promise.all([loadInbound(), loadDashboard(), loadTransactions()]),
      },
      "approve-request": {
        request: () => API.approveReplenishment(id),
        success: "补货申请审核通过",
        reload: loadFulfillment,
      },
      "convert-request": {
        request: () => API.convertReplenishment(id),
        success: (result) => `已生成出库单 ${result.outbound_no || `#${result.outbound_order_id}`}`,
        reload: loadFulfillment,
      },
      "ship-outbound": {
        request: () => API.shipOutbound(id),
        success: "出库发货成功，库存流水已更新",
        reload: () => Promise.all([loadFulfillment(), loadDashboard(), loadTransactions()]),
      },
      "sign-outbound": {
        request: () => API.signOutbound(id),
        success: "门店签收成功，履约流程完成",
        reload: () => Promise.all([loadFulfillment(), loadDashboard(), loadTransactions()]),
      },
    };
    const config = configurations[action];
    if (!config) return;
    await runButtonAction(
      button,
      async () => {
        const result = await config.request();
        await config.reload();
        return result;
      },
      { loadingText: "处理中…", successMessage: config.success },
    );
  }

  function formValues(form) {
    return Object.fromEntries(new FormData(form).entries());
  }

  function optionalValue(value) {
    const normalized = String(value || "").trim();
    return normalized || null;
  }

  async function handleBaseDataCreate(form) {
    const type = form.dataset.createForm;
    const values = formValues(form);
    const configurations = {
      product: {
        request: () =>
          API.createProduct({
            product_code: values.product_code.trim(),
            name: values.name.trim(),
            spec: optionalValue(values.spec),
            unit: values.unit.trim(),
            default_safety_stock: Number(values.default_safety_stock),
            is_active: true,
          }),
        success: "商品已新增，可在入库单中选择",
      },
      supplier: {
        request: () =>
          API.createSupplier({
            name: values.name.trim(),
            phone: values.phone.trim(),
            contact_person: optionalValue(values.contact_person),
            supplier_level: optionalValue(values.supplier_level),
            address: optionalValue(values.address),
            cooperation_status: "active",
            is_active: true,
          }),
        success: "供应商已新增",
      },
      warehouse: {
        request: () =>
          API.createWarehouse({
            warehouse_code: values.warehouse_code.trim(),
            name: values.name.trim(),
            region: optionalValue(values.region),
            manager_name: optionalValue(values.manager_name),
            address: optionalValue(values.address),
            status: "active",
            is_synthetic: false,
          }),
        success: "仓库节点已新增",
      },
      store: {
        request: () =>
          API.createStore({
            store_code: values.store_code.trim(),
            name: values.name.trim(),
            region: optionalValue(values.region),
            contact_person: optionalValue(values.contact_person),
            address: optionalValue(values.address),
            business_status: "active",
            is_synthetic: false,
          }),
        success: "门店节点已新增",
      },
    };
    const configuration = configurations[type];
    if (!configuration) return;
    const button = form.querySelector('[type="submit"]');
    const result = await runButtonAction(button, configuration.request, {
      loadingText: "保存中…",
      successMessage: configuration.success,
    });
    if (!result) return;
    form.reset();
    await Promise.all([loadBaseData(), loadDashboard()]);
  }

  async function handleInboundCreate(form) {
    const values = formValues(form);
    const button = form.querySelector('[type="submit"]');
    const result = await runButtonAction(
      button,
      () =>
        API.createInboundOrder({
          supplier_id: Number(values.supplier_id),
          warehouse_id: Number(values.warehouse_id),
          handled_by: Number(state.currentUser?.id || 1),
          status: "pending",
          remark: optionalValue(values.remark),
          items: [
            {
              product_id: Number(values.product_id),
              quantity: Number(values.quantity),
              batch_no: optionalValue(values.batch_no),
            },
          ],
        }),
      {
        loadingText: "创建中…",
        successMessage: (item) => `入库单 ${item.inbound_no} 已创建`,
      },
    );
    if (!result) return;
    window.bootstrap.Modal.getOrCreateInstance($("createInboundModal")).hide();
    form.reset();
    await loadInbound();
  }

  async function handleRequestCreate(form) {
    const values = formValues(form);
    const button = form.querySelector('[type="submit"]');
    const result = await runButtonAction(
      button,
      () =>
        API.createReplenishmentRequest({
          store_id: Number(values.store_id),
          product_id: Number(values.product_id),
          request_quantity: Number(values.request_quantity),
          request_reason: optionalValue(values.request_reason),
          created_by: Number(state.currentUser?.id || 1),
        }),
      {
        loadingText: "提交中…",
        successMessage: (item) => `补货申请 ${item.request_no} 已提交`,
      },
    );
    if (!result) return;
    window.bootstrap.Modal.getOrCreateInstance($("createRequestModal")).hide();
    form.reset();
    await loadFulfillment();
  }

  function bindEvents() {
    document.querySelectorAll(".nav-item").forEach((button) => {
      button.addEventListener("click", () => switchView(button.dataset.view));
    });
    document.querySelectorAll("[data-jump]").forEach((button) => {
      button.addEventListener("click", () => switchView(button.dataset.jump));
    });
    document.querySelectorAll(".module-refresh").forEach((button) => {
      button.addEventListener("click", () => refreshView(button.dataset.loader, button));
    });

    $("refreshCurrentBtn").addEventListener("click", (event) =>
      refreshView(state.currentView, event.currentTarget),
    );
    $("generateRecommendationBtn").addEventListener("click", async (event) => {
      await runButtonAction(
        event.currentTarget,
        async () => {
          const result = await API.generateRecommendations();
          await Promise.all([loadRecommendations(), loadDashboard()]);
          return result;
        },
        {
          loadingText: "生成中…",
          successMessage: (result) => `已生成 ${formatNumber(result.count)} 条补货建议`,
        },
      );
    });

    document.querySelectorAll("[data-create-form]").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        await handleBaseDataCreate(form);
      });
    });
    $("createInboundForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await handleInboundCreate(event.currentTarget);
    });
    $("createRequestForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await handleRequestCreate(event.currentTarget);
    });

    document.addEventListener("click", (event) => {
      const actionButton = event.target.closest(".row-action");
      if (actionButton) handleRowAction(actionButton);
    });

    $("mobileMenuBtn").addEventListener("click", () => {
      const sidebar = $("appSidebar");
      const willOpen = !sidebar.classList.contains("is-open");
      sidebar.classList.toggle("is-open", willOpen);
      $("mobileMenuBtn").setAttribute("aria-expanded", String(willOpen));
    });

    window.addEventListener("resize", () => {
      state.charts.forEach((chart) => chart.resize());
      if (window.innerWidth > 900) closeMobileMenu();
    });
  }

  function updateUserIdentity(user) {
    const displayName = user.real_name || user.username;
    setText("currentUserName", displayName);
    setText("currentUserRole", roleLabels[user.role] || user.role);
    setText("userAvatar", displayName.slice(0, 1));
  }

  async function enterWorkspace(user) {
    state.currentUser = user;
    updateUserIdentity(user);
    $("loginScreen").hidden = true;
    $("appShell").hidden = false;
    if (!state.eventsBound) {
      bindEvents();
      state.eventsBound = true;
    }
    await initialize();
  }

  function leaveWorkspace() {
    window.sessionStorage.removeItem("supplyChainUser");
    state.currentUser = null;
    $("appShell").hidden = true;
    $("loginScreen").hidden = false;
    $("loginPassword").value = "";
    $("loginError").hidden = true;
    $("loginUsername").focus();
  }

  function bindAuthEvents() {
    $("loginForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const button = form.querySelector('[type="submit"]');
      const errorElement = $("loginError");
      const values = formValues(form);
      errorElement.hidden = true;
      setButtonLoading(button, true, "正在登录…");
      try {
        const user = await API.login({
          username: values.username.trim(),
          password: values.password,
        });
        window.sessionStorage.setItem("supplyChainUser", JSON.stringify(user));
        await enterWorkspace(user);
      } catch (error) {
        errorElement.textContent = error?.message || "登录失败，请稍后重试";
        errorElement.hidden = false;
      } finally {
        setButtonLoading(button, false);
      }
    });
    $("logoutBtn").addEventListener("click", leaveWorkspace);
  }

  async function initialize() {
    clearAlert();
    const requestedView = new URLSearchParams(window.location.search).get("view");
    if (requestedView && viewLoaders[requestedView]) {
      switchView(requestedView);
    }
    await loadLookups();
    const results = await Promise.allSettled([
      loadDashboard(),
      loadBaseData(),
      loadWarnings(),
      loadInbound(),
      loadFulfillment(),
      loadTransactions(),
      loadRecommendations(),
      loadSupplierAnalytics(),
      loadSystemStatus(),
    ]);
    const failed = results.filter((result) => result.status === "rejected");
    if (failed.length) {
      showAlert(`有 ${failed.length} 个模块暂未加载成功，可进入对应模块重试。`, "warning");
    }
  }

  async function bootstrap() {
    bindAuthEvents();
    const savedUser = window.sessionStorage.getItem("supplyChainUser");
    if (!savedUser) return;
    try {
      await enterWorkspace(JSON.parse(savedUser));
    } catch (_error) {
      window.sessionStorage.removeItem("supplyChainUser");
      $("loginScreen").hidden = false;
      $("appShell").hidden = true;
    }
  }

  bootstrap();
})();
