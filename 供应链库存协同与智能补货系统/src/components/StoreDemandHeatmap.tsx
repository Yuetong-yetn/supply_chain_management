/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import { Grid, Inbox, SortAsc, SortDesc } from "lucide-react";
import { StoreDemand } from "../types";

interface StoreDemandHeatmapProps {
  items: StoreDemand[];
  isEmpty: boolean;
}

export default function StoreDemandHeatmap({ items, isEmpty }: StoreDemandHeatmapProps) {
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  const sortedItems = [...items].sort((a, b) => {
    return sortOrder === "desc" ? b.demandValue - a.demandValue : a.demandValue - b.demandValue;
  });

  const getHeatIntensityStyle = (status: "HOT" | "NORMAL" | "COLD") => {
    switch (status) {
      case "HOT":
        return {
          bg: "bg-rose-50 border-rose-100",
          accentText: "text-rose-700",
          indicator: "bg-rose-500",
          description: "高吞吐热点门店",
        };
      case "NORMAL":
        return {
          bg: "bg-blue-50 border-blue-100",
          accentText: "text-blue-700",
          indicator: "bg-blue-500",
          description: "常态销售门店",
        };
      case "COLD":
        return {
          bg: "bg-gray-50 border-gray-100",
          accentText: "text-gray-500",
          indicator: "bg-gray-400",
          description: "周转偏缓节点",
        };
    }
  };

  return (
    <div id="store-demand-section" className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs flex flex-col h-full">
      {/* Module Header and Sorting Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Grid className="h-5 w-5 text-gray-500" />
            <h4 className="font-bold text-gray-900 text-sm">区域门店需求热度分布网格</h4>
          </div>
          <p className="text-2xs text-gray-400 mt-0.5">多门店日销量加权指数分布，直观识别出货吞吐中心</p>
        </div>

        {/* Sorting controls */}
        <button
          onClick={() => setSortOrder(sortOrder === "desc" ? "asc" : "desc")}
          className="self-start sm:self-center inline-flex items-center gap-1.5 text-2xs font-bold text-gray-600 border border-gray-200 hover:border-gray-300 py-1.5 px-3 rounded-lg bg-gray-50/50 hover:bg-gray-150 transition cursor-pointer"
        >
          {sortOrder === "desc" ? (
            <>
              <SortDesc className="h-3 w-3" />
              热度降序 (高 → 低)
            </>
          ) : (
            <>
              <SortAsc className="h-3 w-3" />
              热度升序 (低 → 高)
            </>
          )}
        </button>
      </div>

      {isEmpty || items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-16 text-center">
          <Inbox className="h-12 w-12 text-gray-300 stroke-1 mb-3" />
          <h5 className="text-sm font-semibold text-gray-700">暂无门店需求热力数据</h5>
          <p className="text-xs text-gray-400 max-w-xs mt-1">
            未侦测到门店销售上报，无法渲染需求分布热力矩阵。
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {sortedItems.map((item) => {
            const style = getHeatIntensityStyle(item.status);
            return (
              <div
                key={item.id}
                id={`store-card-${item.id}`}
                className={`border rounded-lg p-3.5 flex flex-col justify-between gap-2.5 transition-all ${style.bg}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-bold text-gray-800 text-xs truncate">{item.storeName}</span>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span className={`h-1.5 w-1.5 rounded-full ${style.indicator}`} />
                    <span className={`text-2xs font-bold ${style.accentText}`}>
                      {item.status === "HOT" ? "高热" : item.status === "NORMAL" ? "平稳" : "低平"}
                    </span>
                  </div>
                </div>

                <div className="flex items-end justify-between border-t border-gray-900/5 pt-2">
                  <span className="text-2xs text-gray-400">{style.description}</span>
                  <div className="text-right">
                    <span className="text-lg font-bold font-mono text-gray-900 leading-none">
                      {item.demandValue}
                    </span>
                    <span className="text-2xs text-gray-400 ml-0.5">指数</span>
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
