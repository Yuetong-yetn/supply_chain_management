/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { Package, Users, AlertTriangle, Lightbulb } from "lucide-react";
import { ConnectionStatus, SystemMetrics } from "../types";

interface MetricsProps {
  metrics: SystemMetrics;
  connectionStatus: ConnectionStatus;
  isEmptyState: boolean;
}

export default function Metrics({ metrics, connectionStatus, isEmptyState }: MetricsProps) {
  const isOffline = connectionStatus === ConnectionStatus.ERROR || connectionStatus === ConnectionStatus.DISCONNECTED;

  const cards = [
    {
      id: "metric-products",
      label: "在库商品总数 (SKUs)",
      value: isEmptyState ? "0" : isOffline ? "480" : metrics.totalProducts.toLocaleString(),
      description: "本期在册全渠道在库商品",
      icon: Package,
      iconClass: "bg-blue-50 text-blue-600",
    },
    {
      id: "metric-suppliers",
      label: "合作供应商规模 (家)",
      value: isEmptyState ? "0" : isOffline ? "24" : metrics.totalSuppliers.toLocaleString(),
      description: "已入驻协同采购网络的供应商",
      icon: Users,
      iconClass: "bg-purple-50 text-purple-600",
    },
    {
      id: "metric-warnings",
      label: "库存异常监控预警 (项)",
      value: isEmptyState ? "0" : isOffline ? "18" : metrics.warningCount.toString(),
      description: "处于低库存 / 缺货 / 积压状态",
      icon: AlertTriangle,
      iconClass: isEmptyState ? "bg-gray-50 text-gray-400" : "bg-amber-50 text-amber-600 animate-pulse",
    },
    {
      id: "metric-replenishments",
      label: "智能采买补货建议 (项)",
      value: isEmptyState ? "0" : isOffline ? "12" : metrics.replenishmentCount.toString(),
      description: "AI算法推演待启动的补货计划",
      icon: Lightbulb,
      iconClass: isEmptyState ? "bg-gray-50 text-gray-400" : "bg-emerald-50 text-emerald-600",
    },
  ];

  return (
    <div id="metrics-grid" className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.id}
            id={card.id}
            className={`bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex items-start justify-between relative overflow-hidden transition ${
              isOffline ? "opacity-85" : "hover:border-gray-300 hover:shadow-md"
            }`}
          >
            {/* Left Column Content */}
            <div className="space-y-1">
              <span className="text-xs font-semibold text-gray-500 tracking-tight leading-none block">
                {card.label}
              </span>
              <h3 className="text-2xl font-bold font-sans text-gray-900 leading-tight">
                {card.value}
              </h3>
              <p className="text-2xs text-gray-400 leading-normal">{card.description}</p>
            </div>

            {/* Right Column Icon Container */}
            <div className={`p-2.5 rounded-lg ${card.iconClass} flex-shrink-0`}>
              <Icon className="h-5 w-5" />
            </div>

            {/* Overlay indicators for offline cache */}
            {isOffline && !isEmptyState && (
              <div className="absolute top-1.5 right-1.5 text-2xs px-1 py-0.5 bg-gray-100 text-gray-400 font-mono rounded scale-90 select-none">
                离线缓存
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
