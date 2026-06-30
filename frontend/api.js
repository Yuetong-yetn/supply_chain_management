(function () {
  "use strict";

  const API_BASE = "/api";
  const REQUEST_TIMEOUT = 15000;

  async function request(path, options = {}) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    try {
      const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        signal: options.signal || controller.signal,
      });
      const json = await response.json().catch(() => null);

      if (!response.ok || !json?.success) {
        throw new Error(json?.message || `请求失败（HTTP ${response.status}）`);
      }
      return json.data;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new Error("请求超时，请检查后端服务");
      }
      if (error instanceof TypeError) {
        throw new Error("无法连接后端，请确认服务已启动");
      }
      throw error;
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  function get(path) {
    return request(path);
  }

  function post(path, body) {
    return request(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  }

  const api = {
    request,
    getHealth: () => get("/health"),
    getDatabaseHealth: () => get("/health/db"),
    getExampleStatus: () => get("/example/status"),
    getDashboard: () => get("/analytics/dashboard"),
    getInventoryRanking: () => get("/analytics/inventory-ranking"),
    getWarehouseFlowTrend: () => get("/analytics/warehouse-flow-trend"),
    getWarnings: () => get("/inventory/warnings"),
    getInventory: () => get("/inventory?page=1&page_size=100"),
    getInboundOrders: () => get("/inbound-orders?page=1&page_size=100"),
    completeInbound: (orderId) => post(`/inbound-orders/${orderId}/complete`),
    getReplenishmentRequests: () => get("/replenishment-requests?page=1&page_size=100"),
    approveReplenishment: (requestId) =>
      post(`/replenishment-requests/${requestId}/approve?audited_by=1`),
    rejectReplenishment: (requestId) =>
      post(`/replenishment-requests/${requestId}/reject?audited_by=1`),
    convertReplenishment: (requestId) =>
      post(
        `/replenishment-requests/${requestId}/convert-to-outbound?source_warehouse_id=1&handled_by=1`,
      ),
    getOutboundOrders: () => get("/outbound-orders?page=1&page_size=100"),
    shipOutbound: (orderId) => post(`/outbound-orders/${orderId}/ship`),
    signOutbound: (orderId) => post(`/outbound-orders/${orderId}/sign`),
    getTransactions: () => get("/transactions?page=1&page_size=100"),
    generateRecommendations: () => post("/recommendations/generate"),
    getRecommendations: () => get("/recommendations"),
    getSupplierRanking: () => get("/suppliers/ranking"),
    getProducts: () => get("/products?page=1&page_size=200"),
    createProduct: (payload) => post("/products", payload),
    getSuppliers: () => get("/suppliers?page=1&page_size=200"),
    createSupplier: (payload) => post("/suppliers", payload),
    getWarehouses: () => get("/warehouses?page=1&page_size=100"),
    createWarehouse: (payload) => post("/warehouses", payload),
    getStores: () => get("/stores?page=1&page_size=200"),
    createStore: (payload) => post("/stores", payload),
    createInboundOrder: (payload) => post("/inbound-orders", payload),
    createReplenishmentRequest: (payload) => post("/replenishment-requests", payload),
  };

  window.SupplyAPI = Object.freeze(api);
})();
