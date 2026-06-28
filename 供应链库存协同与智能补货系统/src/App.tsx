/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from "react";
import {
  ConnectionStatus,
  WarningItem,
  ReplenishmentSuggestion,
  WarningType,
  RiskLevel
} from "./types";
import {
  mockMetrics,
  mockInventoryTopN,
  mockWarnings,
  mockReplenishments,
  mockStoreDemands,
  mockSuppliers,
  mockTurnovers
} from "./mockData";

import Sidebar from "./components/Sidebar";
import Metrics from "./components/Metrics";
import InventoryRanking from "./components/InventoryRanking";
import SupplierRanking from "./components/SupplierRanking";
import ProductTurnover from "./components/ProductTurnover";
import WarningList from "./components/WarningList";
import ReplenishmentSuggestions from "./components/ReplenishmentSuggestions";
import StoreDemandHeatmap from "./components/StoreDemandHeatmap";
import ToastContainer, { ToastMessage } from "./components/Toast";

import {
  RefreshCw,
  Zap,
  WifiOff,
  AlertTriangle,
  Loader2,
  Settings,
  HelpCircle,
  Database
} from "lucide-react";

export default function App() {
  // Navigation State
  const [currentTab, setCurrentTab] = useState<string>("overview");

  // Core Connection & Sandboxing States
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.CONNECTED);
  const [isEmptyState, setIsEmptyState] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>("09:30:00");

  // Dynamic Data States
  const [warnings, setWarnings] = useState<WarningItem[]>(mockWarnings);
  const [replenishments, setReplenishments] = useState<ReplenishmentSuggestion[]>(mockReplenishments);
  const [executedProcurementIds, setExecutedProcurementIds] = useState<string[]>([]);

  // Loading Feedback States
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [warningProcessingId, setWarningProcessingId] = useState<string | null>(null);

  // Notification Toast State
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Toast Helper
  const addToast = (type: "success" | "error" | "info" | "loading", message: string) => {
    const id = Date.now().toString();
    const newToast: ToastMessage = { id, type, message };
    setToasts((prev) => [...prev, newToast]);

    // Auto dismiss after 4 seconds (unless loading)
    if (type !== "loading") {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    }
    return id;
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // 1. Refresh Data Workflow
  const handleRefreshData = () => {
    if (connectionStatus === ConnectionStatus.ERROR) {
      addToast("error", "数据刷新失败：无法同云端仓储协同服务器建立安全握手。");
      return;
    }

    setIsRefreshing(true);
    addToast("info", "正在重新同步全渠道库存节点数据...");

    setTimeout(() => {
      setIsRefreshing(false);
      // Reset variables
      setWarnings(mockWarnings);
      setReplenishments(mockReplenishments);
      setExecutedProcurementIds([]);
      const timeString = new Date().toLocaleTimeString("zh-CN", { hour12: false });
      setLastSyncTime(timeString);
      addToast("success", `全库数据同步成功！最后同步时间: ${timeString}`);
    }, 1000);
  };

  // 2. Generate Replenishment Suggestions Workflow
  const handleGenerateSuggestions = () => {
    if (connectionStatus === ConnectionStatus.ERROR) {
      addToast("error", "决策生成失败：协同链路异常。");
      return;
    }

    setIsGenerating(true);
    const toastId = addToast("loading", "智能分析引擎正在滚算安全水位与历史销量变动...");

    setTimeout(() => {
      setIsGenerating(false);
      removeToast(toastId);

      // Verify if some missing recommendations can be expanded/restored
      if (replenishments.length === 0) {
        setReplenishments(mockReplenishments);
      }

      addToast("success", "AI 补货推演计算完成！已生成最新的安全采买建议。");
    }, 1200);
  };

  // 3. Warning Row Item -> Custom Replenish push Workflow
  const handleInitiateReplenish = (warning: WarningItem) => {
    if (connectionStatus === ConnectionStatus.ERROR) {
      addToast("error", "操作失败：连接已断开，无法回传控制层。");
      return;
    }

    setWarningProcessingId(warning.id);
    addToast("info", `正在推算商品 [${warning.itemName}] 的最佳补货方案...`);

    setTimeout(() => {
      setWarningProcessingId(null);

      // Check if already exists in recommendations, otherwise add it
      const exists = replenishments.some((r) => r.itemName === warning.itemName);
      if (!exists) {
        const newRep: ReplenishmentSuggestion = {
          id: `rep-custom-${Date.now()}`,
          itemName: warning.itemName,
          location: warning.location,
          currentStock: warning.currentStock,
          safetyStock: warning.safetyStock,
          estimatedOutOfStockTime: "严重偏离安全底线 (紧急)",
          suggestedQty: Math.max(100, warning.safetyStock * 3 - warning.currentStock),
          recommendedSupplier: "立讯精工智能设备制造厂",
          riskLevel: RiskLevel.HIGH,
          reason: `用户根据实时警报主动触发的补货推演。当前库存为 ${warning.currentStock} 件，远低于 ${warning.safetyStock} 件安全水平。`,
        };
        setReplenishments((prev) => [newRep, ...prev]);
      }

      addToast("success", `已成功为 [${warning.itemName}] 匹配供应商并生成补货建议！`);
      // Scroll or switch tab
      setCurrentTab("replenishment");
    }, 850);
  };

  // 4. Execute Procurement Action Workflow
  const handleExecuteProcurement = (id: string) => {
    addToast("info", "采购订单协同网配给中...");

    setTimeout(() => {
      setExecutedProcurementIds((prev) => [...prev, id]);
      addToast("success", "采购意向单已成功派发至供应商协同网络！");
    }, 600);
  };

  // Sandbox State triggers
  const handleSimulateError = () => {
    setConnectionStatus(ConnectionStatus.ERROR);
    addToast("error", "已成功注入 [连接异常] 状态。系统切入脱机监控模式。");
  };

  const handleRecoverConnection = () => {
    setConnectionStatus(ConnectionStatus.CONNECTED);
    addToast("success", "网络链路恢复！已同云端仓储数据库重新同步。");
  };

  // Dynamic values based on Empty Sandboxing
  const currentWarnings = isEmptyState ? [] : warnings;
  const currentReplenishments = isEmptyState ? [] : replenishments;
  const currentStoreDemands = isEmptyState ? [] : mockStoreDemands;
  const currentInventoryTopN = isEmptyState ? [] : mockInventoryTopN;
  const currentSuppliers = isEmptyState ? [] : mockSuppliers;
  const currentTurnovers = isEmptyState ? [] : mockTurnovers;

  const currentMetrics = {
    totalProducts: isEmptyState ? 0 : mockMetrics.totalProducts,
    totalSuppliers: isEmptyState ? 0 : mockMetrics.totalSuppliers,
    warningCount: currentWarnings.length,
    replenishmentCount: currentReplenishments.filter(r => !executedProcurementIds.includes(r.id)).length,
  };

  return (
    <div id="app-root" className="min-h-screen bg-gray-50 flex flex-col lg:flex-row font-sans text-gray-800 antialiased">
      {/* 1. Left Sidebar Navigation & Status (Fulfills navigational and connectivity feedback requirements) */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        connectionStatus={connectionStatus}
        setConnectionStatus={setConnectionStatus}
        isEmptyState={isEmptyState}
        setIsEmptyState={setIsEmptyState}
        onSimulateError={handleSimulateError}
        onRecoverConnection={handleRecoverConnection}
        lastSyncTime={lastSyncTime}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 pb-12">
        {/* Global Connection Warning Banner */}
        {connectionStatus === ConnectionStatus.ERROR && (
          <div id="offline-alert-banner" className="bg-rose-50 border-b border-rose-100 px-6 py-3 flex items-center justify-between gap-4 animate-slide-in">
            <div className="flex items-center gap-2 text-rose-800 text-xs font-semibold">
              <WifiOff className="h-4 w-4 animate-pulse flex-shrink-0" />
              <span>注意：协同系统网络断开，正在使用脱机缓存数据。无法发送协同采购指令。</span>
            </div>
            <button
              onClick={handleRecoverConnection}
              className="text-rose-800 hover:text-rose-950 font-bold text-xs underline cursor-pointer"
            >
              一键重连
            </button>
          </div>
        )}

        {/* 2. Top Header Action Bar */}
        <header id="top-bar" className="bg-white border-b border-gray-200 px-6 py-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4 sticky top-0 z-10 shadow-2xs">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-bold text-xs px-2 py-0.5 bg-slate-100 rounded">智能供应链</span>
              <span className="text-xs text-gray-400 font-medium">·</span>
              <span className="text-xs text-gray-400 font-medium">实时智能协同驾驶舱</span>
            </div>
            <h2 id="page-title" className="text-xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
              供应链库存协同与智能补货管理系统
            </h2>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              id="btn-refresh"
              onClick={handleRefreshData}
              disabled={isRefreshing}
              className="inline-flex items-center gap-2 bg-white hover:bg-gray-50 active:bg-gray-100 text-gray-700 text-xs font-semibold px-4 py-2.5 rounded-lg border border-gray-200 shadow-xs transition disabled:opacity-60 cursor-pointer"
            >
              {isRefreshing ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-gray-500" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5 text-gray-500" />
              )}
              {isRefreshing ? "同步中..." : "刷新数据"}
            </button>

            <button
              id="btn-generate"
              onClick={handleGenerateSuggestions}
              disabled={isGenerating}
              className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow-sm transition disabled:opacity-60 cursor-pointer"
            >
              {isGenerating ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Zap className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
              )}
              {isGenerating ? "正在计算生成..." : "生成补货建议"}
            </button>
          </div>
        </header>

        {/* Dashboard Area */}
        <div className="p-6 space-y-6">
          {/* Active Navigation Header / Quick Switch Overview Tab Alert */}
          <div className="flex items-center justify-between border-b border-gray-200 pb-2">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">
              {currentTab === "overview" && "核心库存与业务指标总览"}
              {currentTab === "warnings" && "实时库存预警异常监控板"}
              {currentTab === "replenishment" && "AI 采买协同补货方案推荐"}
              {currentTab === "analysis" && "门店需求与供应链资金表现分析"}
            </h3>
            <span className="text-2xs font-mono text-gray-400">
              工作流: 实时监控 → 风险发现 → 自动生成建议 → 业务一键协同
            </span>
          </div>

          {/* 3. Core Metrics Section (Always visible at the top of tabs for constant snapshot visibility) */}
          <Metrics
            metrics={currentMetrics}
            connectionStatus={connectionStatus}
            isEmptyState={isEmptyState}
          />

          {/* TAB 1: Unified General Cockpit View */}
          {currentTab === "overview" && (
            <div id="tab-overview-pane" className="space-y-6">
              {/* Primary Warnings & Replenishments split screen */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Warnings preview */}
                <div className="space-y-3">
                  <div className="flex justify-between items-center px-1">
                    <span className="text-xs font-bold text-slate-500 uppercase">当前库存异常警告</span>
                    <button
                      onClick={() => setCurrentTab("warnings")}
                      className="text-xs text-slate-700 hover:text-slate-900 font-bold hover:underline"
                    >
                      查看完整预警清单 &rarr;
                    </button>
                  </div>
                  <WarningList
                    items={currentWarnings.slice(0, 3)}
                    isEmpty={isEmptyState}
                    onInitiateReplenish={handleInitiateReplenish}
                    processingId={warningProcessingId}
                  />
                </div>

                {/* AI Suggestions Preview */}
                <div className="space-y-3">
                  <div className="flex justify-between items-center px-1">
                    <span className="text-xs font-bold text-slate-500 uppercase">核心补货协同建议</span>
                    <button
                      onClick={() => setCurrentTab("replenishment")}
                      className="text-xs text-slate-700 hover:text-slate-900 font-bold hover:underline"
                    >
                      进入智能补货中心 &rarr;
                    </button>
                  </div>
                  <ReplenishmentSuggestions
                    items={currentReplenishments.slice(0, 2)}
                    isEmpty={isEmptyState}
                    onExecuteProcurement={handleExecuteProcurement}
                    executedIds={executedProcurementIds}
                  />
                </div>
              </div>

              {/* Three-Column Analysis ranking deck */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <InventoryRanking items={currentInventoryTopN} isEmpty={isEmptyState} />
                <ProductTurnover items={currentTurnovers} isEmpty={isEmptyState} />
                <SupplierRanking items={currentSuppliers} isEmpty={isEmptyState} />
              </div>

              {/* Heatmap module preview */}
              <div className="space-y-3">
                <div className="flex justify-between items-center px-1">
                  <span className="text-xs font-bold text-slate-500 uppercase">全网门店需求波动分布</span>
                  <button
                    onClick={() => setCurrentTab("analysis")}
                    className="text-xs text-slate-700 hover:text-slate-900 font-bold hover:underline"
                  >
                    查看详情与排序 &rarr;
                  </button>
                </div>
                <StoreDemandHeatmap items={currentStoreDemands} isEmpty={isEmptyState} />
              </div>
            </div>
          )}

          {/* TAB 2: Dedicated Warnings Tracker */}
          {currentTab === "warnings" && (
            <div id="tab-warnings-pane" className="space-y-4">
              <div className="p-4 bg-amber-50/50 rounded-xl border border-amber-100 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="font-bold text-amber-900 text-xs">异常库存风险管控指南</h5>
                  <p className="text-xs text-amber-700/80 leading-normal mt-0.5">
                    请优先处理“严重缺货”类预警，其在库水位低于安全保障天数，将直接引发渠道失销。
                    直接点击“启动补货推演”按钮即可通过 AI 引擎测算最优配给供应商与进货批次。
                  </p>
                </div>
              </div>
              <WarningList
                items={currentWarnings}
                isEmpty={isEmptyState}
                onInitiateReplenish={handleInitiateReplenish}
                processingId={warningProcessingId}
              />
            </div>
          )}

          {/* TAB 3: Dedicated Replenishment Suggestions Pane */}
          {currentTab === "replenishment" && (
            <div id="tab-replenishment-pane" className="space-y-4">
              <ReplenishmentSuggestions
                items={currentReplenishments}
                isEmpty={isEmptyState}
                onExecuteProcurement={handleExecuteProcurement}
                executedIds={executedProcurementIds}
              />
            </div>
          )}

          {/* TAB 4: Dedicated Operations and Performance Analysis */}
          {currentTab === "analysis" && (
            <div id="tab-analysis-pane" className="space-y-6">
              {/* Store demand distribution map */}
              <StoreDemandHeatmap items={currentStoreDemands} isEmpty={isEmptyState} />

              {/* Ranking dashboards side-by-side */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <ProductTurnover items={currentTurnovers} isEmpty={isEmptyState} />
                <SupplierRanking items={currentSuppliers} isEmpty={isEmptyState} />
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Dynamic Toast Feedback Mechanism (Fulfills the requirements for notices & loaders) */}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </div>
  );
}
