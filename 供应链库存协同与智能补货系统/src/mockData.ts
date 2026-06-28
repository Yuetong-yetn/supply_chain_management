/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  WarningType,
  RiskLevel,
  InventoryItem,
  WarningItem,
  ReplenishmentSuggestion,
  StoreDemand,
  SupplierRanking,
  ProductTurnover,
  SystemMetrics
} from "./types";

// Normal / Default Data
export const mockMetrics: SystemMetrics = {
  totalProducts: 480,
  totalSuppliers: 24,
  warningCount: 18,
  replenishmentCount: 12,
};

export const mockInventoryTopN: InventoryItem[] = [
  { id: "1", name: "智能平板 Pro Max", stock: 1250, safetyStock: 200, category: "数码电子" },
  { id: "2", name: "降噪无线蓝牙耳机", stock: 980, safetyStock: 150, category: "数码电子" },
  { id: "3", name: "扫地机器人 S10", stock: 750, safetyStock: 100, category: "智能家电" },
  { id: "4", name: "智能腕表 Fit 3", stock: 680, safetyStock: 120, category: "数码电子" },
  { id: "5", name: "空气净化器 Lite", stock: 540, safetyStock: 80, category: "智能家电" },
];

export const mockWarnings: WarningItem[] = [
  {
    id: "w1",
    itemName: "4K 激光投影仪 X2",
    location: "华北主一仓",
    currentStock: 5,
    safetyStock: 30,
    warningType: WarningType.OUT_OF_STOCK,
  },
  {
    id: "w2",
    itemName: "智能平板 Pro Max",
    location: "华东配送中心",
    currentStock: 18,
    safetyStock: 120,
    warningType: WarningType.LOW_STOCK,
  },
  {
    id: "w3",
    itemName: "折叠屏智能手机 V5",
    location: "深圳一号仓",
    currentStock: 12,
    safetyStock: 80,
    warningType: WarningType.LOW_STOCK,
  },
  {
    id: "w4",
    itemName: "降噪无线蓝牙耳机",
    location: "西部物流基地",
    currentStock: 1200,
    safetyStock: 300,
    warningType: WarningType.OVERSTOCK,
  },
  {
    id: "w5",
    itemName: "智能手写笔 Pen 2",
    location: "华中分拨仓",
    currentStock: 0,
    safetyStock: 50,
    warningType: WarningType.OUT_OF_STOCK,
  },
  {
    id: "w6",
    itemName: "恒温养生壶 Mini",
    location: "华东配送中心",
    currentStock: 8,
    safetyStock: 40,
    warningType: WarningType.LOW_STOCK,
  }
];

export const mockReplenishments: ReplenishmentSuggestion[] = [
  {
    id: "r1",
    location: "华北主一仓",
    itemName: "4K 激光投影仪 X2",
    currentStock: 5,
    safetyStock: 30,
    estimatedOutOfStockTime: "已缺货 (超期 2 天)",
    suggestedQty: 150,
    recommendedSupplier: "光科投影技术有限公司",
    riskLevel: RiskLevel.HIGH,
    reason: "最近14天日均销量飙升，当前库存极度短缺，需紧急启动采买流程。",
  },
  {
    id: "r2",
    location: "华东配送中心",
    itemName: "智能平板 Pro Max",
    currentStock: 18,
    safetyStock: 120,
    estimatedOutOfStockTime: "预计 3 天内缺货",
    suggestedQty: 500,
    recommendedSupplier: "立讯精工智能设备制造厂",
    riskLevel: RiskLevel.HIGH,
    reason: "大促周期即将来临，且上一批次物流存在延误，建议提前备货应对订单高峰。",
  },
  {
    id: "r3",
    location: "深圳一号仓",
    itemName: "折叠屏智能手机 V5",
    currentStock: 12,
    safetyStock: 80,
    estimatedOutOfStockTime: "预计 5 天内缺货",
    suggestedQty: 200,
    recommendedSupplier: "深科技精密器件制造部",
    riskLevel: RiskLevel.MEDIUM,
    reason: "核心元器件周转率提升，该供应商具备快速交付通道，补货可缩短提货周期。",
  },
  {
    id: "r4",
    location: "华中分拨仓",
    itemName: "智能手写笔 Pen 2",
    currentStock: 0,
    safetyStock: 50,
    estimatedOutOfStockTime: "已断货 12 小时",
    suggestedQty: 300,
    recommendedSupplier: "万向精密传导元件厂",
    riskLevel: RiskLevel.HIGH,
    reason: "由于协同供应商物流瓶颈导致阶段性断货，建议本次追加30%安全冗余量。",
  },
  {
    id: "r5",
    location: "华东配送中心",
    itemName: "恒温养生壶 Mini",
    currentStock: 8,
    safetyStock: 40,
    estimatedOutOfStockTime: "预计 4 天内缺货",
    suggestedQty: 100,
    recommendedSupplier: "美家生活电器销售处",
    riskLevel: RiskLevel.LOW,
    reason: "常态化耗尽趋势，按照周度自动补货标准计划推算本次合理补货基数。",
  }
];

export const mockStoreDemands: StoreDemand[] = [
  { id: "s1", storeName: "上海南京东路旗舰店", demandValue: 980, status: "HOT" },
  { id: "s2", storeName: "北京国贸精品店", demandValue: 840, status: "HOT" },
  { id: "s3", storeName: "深圳万象城店", demandValue: 720, status: "HOT" },
  { id: "s4", storeName: "成都太古里商圈店", demandValue: 510, status: "NORMAL" },
  { id: "s5", storeName: "杭州湖滨步行街店", demandValue: 430, status: "NORMAL" },
  { id: "s6", storeName: "武汉楚河汉街店", demandValue: 390, status: "NORMAL" },
  { id: "s7", storeName: "广州天河城仓储店", demandValue: 210, status: "COLD" },
  { id: "s8", storeName: "西安钟楼体验店", demandValue: 180, status: "COLD" },
  { id: "s9", storeName: "南京夫子庙特许店", demandValue: 120, status: "COLD" },
];

export const mockSuppliers: SupplierRanking[] = [
  { id: "sp1", supplierName: "立讯精工智能设备制造厂", purchaseAmount: 4820000, sharePercentage: 35 },
  { id: "sp2", supplierName: "深科技精密器件制造部", purchaseAmount: 3100000, sharePercentage: 22 },
  { id: "sp3", supplierName: "光科投影技术有限公司", purchaseAmount: 2450000, sharePercentage: 18 },
  { id: "sp4", supplierName: "美家生活电器销售处", purchaseAmount: 1800000, sharePercentage: 13 },
  { id: "sp5", supplierName: "万向精密传导元件厂", purchaseAmount: 1250000, sharePercentage: 9 },
];

export const mockTurnovers: ProductTurnover[] = [
  { id: "t1", itemName: "智能腕表 Fit 3", monthlySales: 1850, turnoverRate: 9.2 },
  { id: "t2", itemName: "降噪无线蓝牙耳机", monthlySales: 2400, turnoverRate: 8.5 },
  { id: "t3", itemName: "智能平板 Pro Max", monthlySales: 1620, turnoverRate: 7.8 },
  { id: "t4", itemName: "空气净化器 Lite", monthlySales: 720, turnoverRate: 5.4 },
  { id: "t5", itemName: "扫地机器人 S10", monthlySales: 580, turnoverRate: 4.9 },
];
