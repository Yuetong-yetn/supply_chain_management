/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import { Zap, ShieldAlert, CheckCircle2, ChevronRight, Inbox, RefreshCw, Send } from "lucide-react";
import { ReplenishmentSuggestion, RiskLevel } from "../types";

interface ReplenishmentSuggestionsProps {
  items: ReplenishmentSuggestion[];
  isEmpty: boolean;
  onExecuteProcurement: (id: string) => void;
  executedIds: string[];
}

export default function ReplenishmentSuggestions({
  items,
  isEmpty,
  onExecuteProcurement,
  executedIds,
}: ReplenishmentSuggestionsProps) {
  const [filterRisk, setFilterRisk] = useState<string>("ALL");

  const filteredItems = items.filter((item) => {
    if (filterRisk === "ALL") return true;
    return item.riskLevel === filterRisk;
  });

  const getRiskBadge = (level: RiskLevel) => {
    switch (level) {
      case RiskLevel.HIGH:
        return { label: "紧急缺货", bg: "bg-rose-50 text-rose-700 border-rose-200" };
      case RiskLevel.MEDIUM:
        return { label: "中度偏离", bg: "bg-amber-50 text-amber-700 border-amber-200" };
      case RiskLevel.LOW:
        return { label: "常态维持", bg: "bg-blue-50 text-blue-700 border-blue-200" };
    }
  };

  return (
    <div id="replenishment-suggestions-section" className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex flex-col h-full">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-gray-500" />
            <h4 className="font-bold text-gray-900 text-sm">智能采购补货推演建议 (AI)</h4>
          </div>
          <p className="text-2xs text-gray-400 mt-0.5">算法每日滚算周转需求量，科学指引“买多少、向谁买、为何买”</p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-2xs font-bold text-gray-400 uppercase tracking-wider hidden md:inline mr-1">风险度:</span>
          {[
            { id: "ALL", label: "全部建议" },
            { id: RiskLevel.HIGH, label: "紧急缺货" },
            { id: RiskLevel.MEDIUM, label: "中度偏离" },
            { id: RiskLevel.LOW, label: "常态维持" },
          ].map((btn) => (
            <button
              key={btn.id}
              onClick={() => setFilterRisk(btn.id)}
              className={`text-2xs py-1 px-2.5 rounded font-medium border transition ${
                filterRisk === btn.id
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
          <h5 className="text-sm font-semibold text-gray-700">暂无补货建议建议项</h5>
          <p className="text-xs text-gray-400 max-w-xs mt-1">
            {filterRisk === "ALL"
              ? "系统暂未生成补货建议，可以点击右上角“生成补货建议”主动触发滚算。"
              : "没有对应风险等级的补货计划。"}
          </p>
        </div>
      ) : (
        <div className="flex-1 space-y-4">
          {filteredItems.map((item) => {
            const risk = getRiskBadge(item.riskLevel);
            const isExecuted = executedIds.includes(item.id);

            return (
              <div
                key={item.id}
                id={`rep-card-${item.id}`}
                className={`border rounded-xl p-4.5 transition-all flex flex-col md:flex-row md:items-stretch gap-4 ${
                  isExecuted
                    ? "bg-emerald-50/10 border-emerald-100 opacity-90"
                    : "bg-white border-gray-100 hover:border-gray-300 hover:shadow-xs"
                }`}
              >
                {/* Visual Status Indicator column */}
                <div className="flex-1 flex flex-col justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-2xs px-2 py-0.5 rounded-full border font-semibold ${risk.bg}`}>
                        {risk.label}
                      </span>
                      <span className="text-xs font-semibold text-gray-500 font-mono">
                        {item.location}
                      </span>
                    </div>
                    <h5 className="font-bold text-gray-900 text-sm">{item.itemName}</h5>
                  </div>

                  {/* Why to buy section */}
                  <div className="bg-gray-50/70 rounded-lg p-3 border border-gray-100/50">
                    <p className="text-2xs font-bold text-gray-400 mb-0.5">补货决策原由说明</p>
                    <p className="text-xs text-gray-600 leading-normal font-sans">{item.reason}</p>
                  </div>

                  {/* Stock parameters summary */}
                  <div className="flex items-center gap-6 text-2xs text-gray-400 font-mono">
                    <div>
                      <span>在库余量:</span>
                      <span className="text-gray-700 font-bold ml-1">{item.currentStock} 件</span>
                    </div>
                    <div>
                      <span>安全基准:</span>
                      <span className="text-gray-500 ml-1">{item.safetyStock} 件</span>
                    </div>
                    <div>
                      <span>时效估算:</span>
                      <span className={`ml-1 font-semibold ${item.riskLevel === RiskLevel.HIGH ? "text-rose-500" : "text-amber-500"}`}>
                        {item.estimatedOutOfStockTime}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Logistics Proposal Section (Right Column on desktop) */}
                <div className="flex-shrink-0 md:w-80 md:border-l md:border-gray-100 md:pl-5 flex flex-col justify-between gap-4">
                  <div className="space-y-2.5">
                    <div>
                      <span className="text-2xs text-gray-400 block font-semibold leading-none mb-1">
                        AI 算得推荐供应商
                      </span>
                      <span className="text-xs font-bold text-gray-800 leading-tight">
                        {item.recommendedSupplier}
                      </span>
                    </div>

                    <div className="flex items-center justify-between py-2 border-t border-b border-gray-100/50">
                      <div>
                        <span className="text-2xs text-gray-400 block leading-none mb-1">
                          系统推荐采购额
                        </span>
                        <span className="text-lg font-bold text-slate-900 font-mono">
                          {item.suggestedQty.toLocaleString()}
                          <span className="text-xs font-sans font-medium text-gray-400 ml-1">件</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Form Action Button */}
                  <div>
                    {isExecuted ? (
                      <div className="w-full py-2 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-lg border border-emerald-200 flex items-center justify-center gap-1.5 select-none">
                        <CheckCircle2 className="h-4 w-4" />
                        已下达至供应商协同网
                      </div>
                    ) : (
                      <button
                        onClick={() => onExecuteProcurement(item.id)}
                        className="w-full py-2 bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm cursor-pointer"
                      >
                        <Send className="h-3.5 w-3.5" />
                        一键派发采购计划单
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
