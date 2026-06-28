/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { Handshake, Inbox } from "lucide-react";
import { SupplierRanking as SupplierRankingType } from "../types";

interface SupplierRankingProps {
  items: SupplierRankingType[];
  isEmpty: boolean;
}

export default function SupplierRanking({ items, isEmpty }: SupplierRankingProps) {
  return (
    <div id="supplier-ranking-card" className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Handshake className="h-4.5 w-4.5 text-gray-500" />
          <h4 className="font-bold text-gray-800 text-sm">供应商采购资金流排行 (Top 5)</h4>
        </div>
        <span className="text-2xs text-gray-400">核算资金流配比度</span>
      </div>

      {isEmpty || items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 text-center">
          <Inbox className="h-10 w-10 text-gray-300 stroke-1 mb-2" />
          <p className="text-xs text-gray-400 font-medium">暂无合作采购及交易资金占比数据</p>
        </div>
      ) : (
        <div className="flex-1 space-y-4">
          {items.map((item, index) => (
            <div key={item.id} id={`sup-rank-item-${item.id}`} className="space-y-1.5">
              <div className="flex items-start justify-between text-xs gap-3">
                <div className="flex items-start gap-2 truncate">
                  <span className="font-mono font-bold text-gray-400 mt-0.5">
                    {index + 1}
                  </span>
                  <span className="font-medium text-gray-700 truncate block">
                    {item.supplierName}
                  </span>
                </div>
                <div className="text-right flex-shrink-0 font-mono">
                  <div className="font-bold text-gray-900">
                    ¥{(item.purchaseAmount / 10000).toLocaleString()}万
                  </div>
                  <div className="text-2xs text-gray-400 font-sans">份额: {item.sharePercentage}%</div>
                </div>
              </div>
              {/* Relative allocation bar */}
              <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-slate-700 h-full rounded-full"
                  style={{ width: `${item.sharePercentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
