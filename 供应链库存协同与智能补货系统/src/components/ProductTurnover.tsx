/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { TrendingUp, Inbox } from "lucide-react";
import { ProductTurnover as TurnoverType } from "../types";

interface ProductTurnoverProps {
  items: TurnoverType[];
  isEmpty: boolean;
}

export default function ProductTurnover({ items, isEmpty }: ProductTurnoverProps) {
  const maxSales = items.length > 0 ? Math.max(...items.map((i) => i.monthlySales)) : 1;

  return (
    <div id="product-turnover-card" className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4.5 w-4.5 text-gray-500" />
          <h4 className="font-bold text-gray-800 text-sm">商品动销及周转表现</h4>
        </div>
        <span className="text-2xs text-gray-400">周转倍率 = 销货量 / 平均存量</span>
      </div>

      {isEmpty || items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 text-center">
          <Inbox className="h-10 w-10 text-gray-300 stroke-1 mb-2" />
          <p className="text-xs text-gray-400 font-medium">暂无商品动销表现分析数据</p>
        </div>
      ) : (
        <div className="flex-1 space-y-4">
          {items.map((item) => {
            const barPct = Math.min(100, Math.round((item.monthlySales / maxSales) * 100));
            return (
              <div key={item.id} id={`turnover-item-${item.id}`} className="space-y-1.5">
                <div className="flex justify-between items-start text-xs">
                  <span className="font-medium text-gray-700 truncate mr-3">{item.itemName}</span>
                  <div className="text-right flex-shrink-0">
                    <span className="text-2xs px-1.5 py-0.5 rounded-full font-bold bg-slate-100 text-slate-700">
                      周转率: {item.turnoverRate}x
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-gray-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-slate-600 h-full rounded-full"
                      style={{ width: `${barPct}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono font-semibold text-gray-900 w-16 text-right">
                    {item.monthlySales.toLocaleString()} <span className="text-2xs font-sans text-gray-400">件/月</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
