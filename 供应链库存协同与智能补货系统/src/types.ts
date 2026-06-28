/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export enum ConnectionStatus {
  CONNECTED = "CONNECTED",
  CONNECTING = "CONNECTING",
  DISCONNECTED = "DISCONNECTED",
  ERROR = "ERROR",
}

export enum WarningType {
  LOW_STOCK = "LOW_STOCK",    // 低库存
  OUT_OF_STOCK = "OUT_OF_STOCK", // 缺货
  OVERSTOCK = "OVERSTOCK",    // 积压
}

export enum RiskLevel {
  HIGH = "HIGH",     // 高风险
  MEDIUM = "MEDIUM", // 中风险
  LOW = "LOW",       // 低风险
}

export interface InventoryItem {
  id: string;
  name: string;
  stock: number;
  safetyStock: number;
  category: string;
}

export interface WarningItem {
  id: string;
  itemName: string;
  location: string;
  currentStock: number;
  safetyStock: number;
  warningType: WarningType;
}

export interface ReplenishmentSuggestion {
  id: string;
  location: string;
  itemName: string;
  currentStock: number;
  safetyStock: number;
  estimatedOutOfStockTime: string;
  suggestedQty: number;
  recommendedSupplier: string;
  riskLevel: RiskLevel;
  reason: string;
}

export interface StoreDemand {
  id: string;
  storeName: string;
  demandValue: number; // 需求值 / 销量值
  status: "HOT" | "NORMAL" | "COLD";
}

export interface SupplierRanking {
  id: string;
  supplierName: string;
  purchaseAmount: number;
  sharePercentage: number;
}

export interface ProductTurnover {
  id: string;
  itemName: string;
  monthlySales: number;
  turnoverRate: number; // 周转率
}

export interface SystemMetrics {
  totalProducts: number;
  totalSuppliers: number;
  warningCount: number;
  replenishmentCount: number;
}
