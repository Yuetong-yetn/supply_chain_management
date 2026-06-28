/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import { AlertCircle, ArrowUpRight, Check, Filter, Inbox, SlidersHorizontal } from "lucide-react";
import { WarningItem, WarningType } from "../types";

interface WarningListProps {
  items: WarningItem[];
  isEmpty: boolean;
  onInitiateReplenish: (item: WarningItem) => void;
  processingId: string | null;
}

export default function WarningList({ items, isEmpty, onInitiateReplenish, processingId }: WarningListProps) {
  const [filterType, setFilterType] = useState<string>("ALL");

  const filteredItems = items.filter((item) => {
    if (filterType === "ALL") return true;
    if (filterType === "OUT_OF_STOCK") return item.warningType === WarningType.OUT_OF_STOCK;
    if (filterType === "LOW_STOCK") return item.warningType === WarningType.LOW_STOCK;
    if (filterType === "OVERSTOCK") return item.warningType === WarningType.OVERSTOCK;
    return true;
  });

  const getWarningTypeLabel = (type: WarningType) => {
    switch (type) {
      case WarningType.OUT_OF_STOCK:
        return { label: "严重缺货", bg: "bg-rose-50 text-rose-700 border-rose-200" };
      case WarningType.LOW_STOCK:
        return { label: "低库存预警", bg: "bg-amber-50 text-amber-700 border-amber-200" };
      case WarningType.OVERSTOCK:
        return { label: "库存积压", bg: "bg-blue-50 text-blue-700 border-blue-200" };
    }
  };

  return (
    <div id="warning-list-section" className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex flex-col h-full">
      {/* Module Header and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-gray-500" />
            <h4 className="font-bold text-gray-900 text-sm">库存异常实时监控预警列表</h4>
          </div>
          <p className="text-2xs text-gray-400 mt-0.5">自动探测在库量与安全线偏离率，标红严重缺货项目</p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-2xs font-bold text-gray-400 uppercase tracking-wider hidden md:inline mr-1">类型过滤:</span>
          {[
            { id: "ALL", label: "全部预警" },
            { id: "OUT_OF_STOCK", label: "严重缺货" },
            { id: "LOW_STOCK", label: "低库存" },
            { id: "OVERSTOCK", label: "库存积压" },
          ].map((btn) => (
            <button
              key={btn.id}
              onClick={() => setFilterType(btn.id)}
              className={`text-2xs py-1 px-2.5 rounded font-medium border transition ${
                filterType === btn.id
                  ? "bg-slate-900 border-slate-900 text-white font-semibold"
                  : "bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {isEmpty || filteredItems.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-16 text-center">
          <Inbox className="h-12 w-12 text-gray-300 stroke-1 mb-3" />
          <h5 className="text-sm font-semibold text-gray-700">暂无异常预警项</h5>
          <p className="text-xs text-gray-400 max-w-xs mt-1">
            {filterType === "ALL" ? "当前所有在库商品均稳定在安全水位，暂无库存风险。" : "当前筛选条件下的警报项为空。"}
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto -mx-5 px-5">
          {/* Desktop Table View */}
          <table className="min-w-full text-left border-collapse hidden md:table">
            <thead>
              <tr className="border-b border-gray-100 text-2xs font-semibold text-gray-400 uppercase tracking-wider">
                <th className="py-2.5">商品名称</th>
                <th className="py-2.5">存储节点 (仓/店)</th>
                <th className="py-2.5 text-right">当前库存</th>
                <th className="py-2.5 text-right">安全库存</th>
                <th className="py-2.5 text-center px-4">预警类型</th>
                <th className="py-2.5 text-right">协同操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 text-xs">
              {filteredItems.map((item) => {
                const style = getWarningTypeLabel(item.warningType);
                const isProcessing = processingId === item.id;
                return (
                  <tr key={item.id} className="hover:bg-gray-50/60 transition-colors">
                    <td className="py-3 font-semibold text-gray-800">{item.itemName}</td>
                    <td className="py-3 text-gray-500 font-medium">{item.location}</td>
                    <td className="py-3 text-right font-mono font-bold text-gray-800">{item.currentStock}</td>
                    <td className="py-3 text-right font-mono text-gray-400">{item.safetyStock}</td>
                    <td className="py-3 text-center px-4">
                      <span className={`inline-block text-2xs px-2 py-0.5 rounded-full border font-semibold ${style.bg}`}>
                        {style.label}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      {item.warningType === WarningType.OVERSTOCK ? (
                        <span className="text-2xs text-gray-400 font-medium">无需补货</span>
                      ) : (
                        <button
                          onClick={() => onInitiateReplenish(item)}
                          disabled={isProcessing}
                          className="inline-flex items-center gap-1 text-2xs font-bold text-slate-800 hover:text-slate-900 border border-slate-200 hover:border-slate-300 py-1 px-2.5 rounded bg-white shadow-xs transition cursor-pointer disabled:opacity-50"
                        >
                          {isProcessing ? "生成中..." : "启动补货推演"}
                          <ArrowUpRight className="h-3 w-3" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Mobile Stacked List View */}
          <div className="md:hidden space-y-3 pb-2">
            {filteredItems.map((item) => {
              const style = getWarningTypeLabel(item.warningType);
              const isProcessing = processingId === item.id;
              return (
                <div key={item.id} className="border border-gray-100 rounded-lg p-3 bg-gray-50/30 space-y-2">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h5 className="font-semibold text-gray-800 text-xs">{item.itemName}</h5>
                      <span className="text-2xs text-gray-400 font-medium">{item.location}</span>
                    </div>
                    <span className={`text-2xs px-2 py-0.5 rounded-full border font-semibold ${style.bg}`}>
                      {style.label}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 py-1.5 border-t border-b border-gray-100/50 text-2xs font-mono">
                    <div>
                      <span className="text-gray-400 font-sans block">当前库存</span>
                      <span className="font-bold text-gray-800 text-sm">{item.currentStock}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 font-sans block">安全水位</span>
                      <span className="text-gray-600 text-sm">{item.safetyStock}</span>
                    </div>
                  </div>

                  {item.warningType !== WarningType.OVERSTOCK && (
                    <div className="flex justify-end pt-1">
                      <button
                        onClick={() => onInitiateReplenish(item)}
                        disabled={isProcessing}
                        className="w-full flex items-center justify-center gap-1.5 text-2xs font-bold text-slate-800 border border-slate-200 bg-white py-1.5 rounded-md hover:bg-gray-50 active:bg-gray-100 transition"
                      >
                        {isProcessing ? "建议推演中..." : "转为AI补货建议"}
                        <ArrowUpRight className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
