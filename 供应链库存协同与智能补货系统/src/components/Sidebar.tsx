/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from "react";
import {
  Layers,
  AlertTriangle,
  Zap,
  BarChart3,
  Wifi,
  WifiOff,
  Database,
  RefreshCw,
  Sliders,
  Menu,
  X,
  Radio
} from "lucide-react";
import { ConnectionStatus } from "../types";

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (status: ConnectionStatus) => void;
  isEmptyState: boolean;
  setIsEmptyState: (isEmpty: boolean) => void;
  onSimulateError: () => void;
  onRecoverConnection: () => void;
  lastSyncTime: string;
}

export default function Sidebar({
  currentTab,
  setCurrentTab,
  connectionStatus,
  setConnectionStatus,
  isEmptyState,
  setIsEmptyState,
  onSimulateError,
  onRecoverConnection,
  lastSyncTime,
}: SidebarProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navigationItems = [
    { id: "overview", label: "总览数据看板", icon: Layers },
    { id: "warnings", label: "库存预警监控", icon: AlertTriangle, badge: "18" },
    { id: "replenishment", label: "智能补货建议", icon: Zap, badge: "AI" },
    { id: "analysis", label: "经营表现分析", icon: BarChart3 },
  ];

  const getStatusText = () => {
    switch (connectionStatus) {
      case ConnectionStatus.CONNECTED:
        return "数据协同就绪";
      case ConnectionStatus.CONNECTING:
        return "正在同步中心库...";
      case ConnectionStatus.DISCONNECTED:
        return "与云端协同断开";
      case ConnectionStatus.ERROR:
        return "协同连接响应异常";
    }
  };

  const getStatusClass = () => {
    switch (connectionStatus) {
      case ConnectionStatus.CONNECTED:
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case ConnectionStatus.CONNECTING:
        return "bg-blue-50 text-blue-700 border-blue-200";
      case ConnectionStatus.DISCONNECTED:
        return "bg-gray-100 text-gray-700 border-gray-200";
      case ConnectionStatus.ERROR:
        return "bg-rose-50 text-rose-700 border-rose-200";
    }
  };

  return (
    <>
      {/* Mobile Top Header (Mobile Only) */}
      <div id="mobile-header" className="lg:hidden flex items-center justify-between p-4 bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <Database className="h-6 w-6 text-slate-800" />
          <span className="font-bold text-gray-800 text-base tracking-tight">供应链智能管理系统</span>
        </div>
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-2 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 transition"
          aria-label="切换菜单"
        >
          {isMobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar Wrapper (Static on Desktop, Overlay on Mobile) */}
      <aside
        id="sidebar"
        className={`fixed inset-y-0 left-0 z-40 w-72 bg-white border-r border-gray-200 flex flex-col justify-between transform transition-transform duration-300 lg:static lg:translate-x-0 ${
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col flex-1 overflow-y-auto">
          {/* Brand Identity / Header (Desktop Only) */}
          <div className="hidden lg:flex items-center gap-3 px-6 py-6 border-b border-gray-100">
            <div className="bg-slate-900 text-white p-2 rounded-lg">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900 text-base leading-tight">供应链协同平台</h1>
              <p className="text-xs text-gray-400 font-mono mt-0.5">V3.5.0 STABLE</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-4 py-6 space-y-1">
            <p className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">系统监控模块</p>
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-link-${item.id}`}
                  onClick={() => {
                    setCurrentTab(item.id);
                    setIsMobileOpen(false); // Close on mobile navigation click
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-slate-900 text-white"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 ${isActive ? "text-white" : "text-gray-400"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-2xs px-1.5 py-0.5 rounded font-bold ${
                        isActive ? "bg-slate-800 text-slate-100" : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* System Status Tracker Panel */}
          <div className="px-4 py-4 border-t border-gray-100 bg-gray-50/50">
            <div className="px-3 mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">系统连接状态</span>
              <Radio className={`h-3 w-3 ${connectionStatus === ConnectionStatus.CONNECTED ? "text-emerald-500 animate-pulse" : "text-rose-400"}`} />
            </div>
            <div className={`mx-3 p-3 rounded-lg border ${getStatusClass()} flex flex-col gap-2`}>
              <div className="flex items-center gap-2">
                {connectionStatus === ConnectionStatus.CONNECTED ? (
                  <Wifi className="h-4 w-4 text-emerald-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-rose-500" />
                )}
                <span className="text-xs font-bold leading-none">{getStatusText()}</span>
              </div>
              <p className="text-2xs text-gray-400 leading-normal">
                {connectionStatus === ConnectionStatus.CONNECTED
                  ? "实时数据库通信已建立，自动拉取频次正常。"
                  : "协同链路处于模拟断开状态。部分数据模块可能显示缓存快照。"}
              </p>
              {lastSyncTime && (
                <div className="text-2xs text-gray-400 font-mono mt-0.5 border-t border-gray-200/50 pt-1.5 flex items-center justify-between">
                  <span>同步时间:</span>
                  <span>{lastSyncTime}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Prototype Sandbox Interactive Controller (Fulfills the requirements for custom mock switching) */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center gap-2 px-2 mb-2">
            <Sliders className="h-3.5 w-3.5 text-gray-400" />
            <span className="text-xs font-bold text-gray-500">原型测试控制沙盒</span>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-100 space-y-3">
            <div>
              <p className="text-2xs font-bold text-gray-400 mb-1.5">模拟协同连接</p>
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  onClick={onRecoverConnection}
                  className={`text-2xs py-1 px-1.5 rounded font-medium border text-center transition ${
                    connectionStatus === ConnectionStatus.CONNECTED
                      ? "bg-white border-slate-300 text-slate-800 shadow-sm"
                      : "bg-gray-100 border-gray-200 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                  }`}
                >
                  恢复连通
                </button>
                <button
                  onClick={onSimulateError}
                  className={`text-2xs py-1 px-1.5 rounded font-medium border text-center transition ${
                    connectionStatus === ConnectionStatus.ERROR
                      ? "bg-rose-50 border-rose-300 text-rose-700 font-bold"
                      : "bg-gray-100 border-gray-200 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                  }`}
                >
                  注入断连
                </button>
              </div>
            </div>

            <div>
              <p className="text-2xs font-bold text-gray-400 mb-1.5">模拟数据载入</p>
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  onClick={() => setIsEmptyState(false)}
                  className={`text-2xs py-1 px-1.5 rounded font-medium border text-center transition ${
                    !isEmptyState
                      ? "bg-white border-slate-300 text-slate-800 shadow-sm font-semibold"
                      : "bg-gray-100 border-gray-200 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                  }`}
                >
                  载入完整
                </button>
                <button
                  onClick={() => setIsEmptyState(true)}
                  className={`text-2xs py-1 px-1.5 rounded font-medium border text-center transition ${
                    isEmptyState
                      ? "bg-amber-50 border-amber-300 text-amber-700 font-bold"
                      : "bg-gray-100 border-gray-200 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                  }`}
                >
                  清空列表
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Sidebar Overlay Backdrop */}
      {isMobileOpen && (
        <div
          id="mobile-overlay"
          onClick={() => setIsMobileOpen(false)}
          className="lg:hidden fixed inset-0 bg-black/40 z-30 transition-opacity"
        />
      )}
    </>
  );
}
