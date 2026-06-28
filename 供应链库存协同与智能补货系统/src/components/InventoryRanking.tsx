/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { Layers3, Inbox } from "lucide-react";
import { InventoryItem } from "../types";

interface InventoryRankingProps {
  items: InventoryItem[];
  isEmpty: boolean;
}

export default function InventoryRanking({ items, isEmpty }: InventoryRankingProps) {
  // Find maximum stock value for scale calculations
  const maxStock = items.length > 0 ? Math.max(...items.map((i) => i.stock)) : 1;

  return (
    <div id="inventory-ranking-card" className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Layers3 className="h-4.5 w-4.5 text-gray-500" />
          <h4 className="font-bold text-gray-800 text-sm">库存结构分布排行 (Top 5)</h4>
        </div>
        <span className="text-2xs text-gray-400">基于实时库存量测算</span>
      </div>

      {isEmpty || items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 text-center">
          <Inbox className="h-10 w-10 text-gray-300 stroke-1 mb-2" />
          <p className="text-xs text-gray-400 font-medium">暂无高库存商品分布数据</p>
        </div>
      ) : (
        <div className="flex-1 space-y-4">
          {items.map((item, index) => {
            const pct = Math.min(100, Math.round((item.stock / maxStock) * 100));
            return (
              <div key={item.id} id={`inv-rank-item-${item.id}`} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-mono font-bold text-gray-400 w-4 inline-block">
                      0{index + 1}
                    </span>
                    <span className="font-medium text-gray-700 truncate">{item.name}</span>
                    <span className="bg-slate-100 text-slate-500 text-2xs px-1.5 py-0.5 rounded-sm flex-shrink-0">
                      {item.category}
                    </span>
                  </div>
                  <span className="font-semibold text-gray-900 font-mono">
                    {item.stock.toLocaleString()} <span className="text-2xs text-gray-400 font-sans">件</span>
                  </span>
                </div>
                {/* Horizontal Bar Chart Gauge */}
                <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-slate-800 h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-2xs text-gray-400 font-mono">
                  <span>安全库存: {item.safetyStock} 件</span>
                  <span>比安全水位: +{Math.round((item.stock / item.safetyStock) * 100)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
