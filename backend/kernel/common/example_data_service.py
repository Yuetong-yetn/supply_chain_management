"""示例数据生成与加载服务。

generate_example_data() 生成 JSON 文件到 example/ 目录。
load_example_data(db) 将 JSON 文件导入数据库。
"""

import calendar
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from random import Random
from typing import Any

from sqlalchemy import func, or_, select

from kernel.common.config import get_settings
from kernel.common.database import Session
from kernel.common.hash_utils import hash_password

RNG = Random(20260510)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _month_start(base_date: date, months_ago: int = 0) -> date:
    year = base_date.year
    month = base_date.month - months_ago
    while month <= 0:
        year -= 1
        month += 12
    return date(year, month, 1)


def _safe_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _parse_date(value: str | date | datetime | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _parse_datetime(value: str | date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def generate_example_data() -> dict[str, int]:
    """生成示例数据 JSON 文件到 example/ 目录。"""
    settings = get_settings()
    example_dir = settings.example_dir_path
    if example_dir.exists():
        shutil.rmtree(example_dir)
    example_dir.mkdir(parents=True, exist_ok=True)

    categories = [
        {"name": "饮料", "parent_name": None},
        {"name": "矿泉水", "parent_name": "饮料"},
        {"name": "茶饮料", "parent_name": "饮料"},
        {"name": "碳酸饮料", "parent_name": "饮料"},
        {"name": "零食", "parent_name": None},
        {"name": "日用品", "parent_name": None},
        {"name": "文具", "parent_name": None},
        {"name": "药品", "parent_name": None},
        {"name": "冷藏食品", "parent_name": None},
        {"name": "粮油调味", "parent_name": None},
        {"name": "个人护理", "parent_name": None},
    ]
    product_templates = [
        ("矿泉水 550ml", "矿泉水"),
        ("苏打水 500ml", "矿泉水"),
        ("绿茶 500ml", "茶饮料"),
        ("可乐 330ml", "碳酸饮料"),
        ("橙汁 1L", "饮料"),
        ("乌龙茶 500ml", "茶饮料"),
        ("咖啡饮料 280ml", "饮料"),
        ("能量饮料 250ml", "饮料"),
        ("薯片 原味", "零食"),
        ("薯片 番茄味", "零食"),
        ("饼干 奶香味", "零食"),
        ("方便面 红烧牛肉味", "零食"),
        ("方便面 老坛酸菜味", "零食"),
        ("巧克力棒", "零食"),
        ("坚果混合装", "零食"),
        ("海苔卷", "零食"),
        ("洗手液", "日用品"),
        ("抽纸", "日用品"),
        ("垃圾袋", "日用品"),
        ("洗洁精", "日用品"),
        ("中性笔 黑色", "文具"),
        ("中性笔 蓝色", "文具"),
        ("A4 复印纸", "文具"),
        ("笔记本 B5", "文具"),
        ("修正带", "文具"),
        ("创可贴", "药品"),
        ("感冒药", "药品"),
        ("退烧贴", "药品"),
        ("碘伏棉签", "药品"),
        ("牛奶 250ml", "冷藏食品"),
        ("酸奶 200g", "冷藏食品"),
        ("鸡蛋", "冷藏食品"),
        ("火腿肠", "冷藏食品"),
        ("食用油", "粮油调味"),
        ("酱油", "粮油调味"),
        ("醋", "粮油调味"),
        ("大米 5kg", "粮油调味"),
        ("面条 1kg", "粮油调味"),
        ("洗发水", "个人护理"),
        ("牙膏", "个人护理"),
        ("牙刷", "个人护理"),
        ("沐浴露", "个人护理"),
        ("护手霜", "个人护理"),
    ]
    while len(product_templates) < 60:
        idx = len(product_templates) + 1
        category = ["饮料", "零食", "日用品", "文具", "药品", "冷藏食品", "粮油调味", "个人护理"][idx % 8]
        product_templates.append((f"示例商品{idx:02d}", category))

    products = []
    for idx, (name, category_name) in enumerate(product_templates, start=1):
        products.append({
            "product_code": f"P{idx:04d}", "name": name, "barcode": f"6900000{idx:06d}",
            "category_name": category_name, "spec": "标准装", "unit": "piece",
            "shelf_life_days": 365 if category_name not in {"冷藏食品", "药品"} else 90,
            "default_safety_stock": 10 + idx % 20, "is_active": True,
        })

    suppliers = [
        {"name": f"供应商S{i:02d}", "contact_person": f"联系人{i:02d}", "phone": f"1380000{i:04d}",
         "email": f"supplier{i:02d}@example.com", "address": f"示例供应商地址{i:02d}",
         "supplier_level": ["A", "B", "C"][i % 3], "cooperation_status": "active", "is_active": True}
        for i in range(1, 13)
    ]

    supplier_products = []
    for idx, product in enumerate(products, start=1):
        for offset in range(1, 1 + (2 if idx % 5 == 0 else 1) + (1 if idx % 9 == 0 else 0)):
            supplier_index = ((idx + offset) % len(suppliers)) + 1
            supplier_products.append({
                "supplier_name": f"供应商S{supplier_index:02d}", "product_code": product["product_code"],
                "supply_price": round(3 + idx * 0.7 + offset * 0.5, 2),
                "lead_time_days": 1 + (idx + offset) % 5,
                "on_time_rate": round(0.85 + ((idx + offset) % 10) * 0.01, 2),
                "quality_score": round(7.5 + ((idx + offset) % 5) * 0.4, 2),
                "is_preferred": offset == 1,
            })

    warehouses = [
        {"warehouse_code": "WH-CENTRAL", "name": "中心仓", "address": "中心区一号路", "manager_name": "张仓",
         "phone": "021-1000001", "max_capacity": 30000, "status": "active", "region": "中心区", "is_synthetic": False},
        {"warehouse_code": "WH-EAST", "name": "东区仓", "address": "东区二号路", "manager_name": "李东",
         "phone": "021-1000002", "max_capacity": 20000, "status": "active", "region": "东区", "is_synthetic": False},
        {"warehouse_code": "WH-WEST", "name": "西区仓", "address": "西区三号路", "manager_name": "王西",
         "phone": "021-1000003", "max_capacity": 18000, "status": "active", "region": "西区", "is_synthetic": False},
        {"warehouse_code": "WH-COLD", "name": "冷链仓", "address": "北区冷链路", "manager_name": "赵冷",
         "phone": "021-1000004", "max_capacity": 15000, "status": "active", "region": "北区", "is_synthetic": False},
    ]

    regions = ["东区", "西区", "南区", "北区", "中心区"]
    stores = []
    for idx, code in enumerate(["STORE-A", "STORE-B", "STORE-C", "STORE-D", "STORE-E", "STORE-F", "STORE-G", "STORE-H"], start=1):
        stores.append({
            "store_code": code, "name": f"{code} 门店",
            "region": regions[(idx - 1) % len(regions)],
            "address": f"{regions[(idx - 1) % len(regions)]} 商业街 {idx} 号",
            "longitude": 121.4 + idx * 0.01, "latitude": 31.2 + idx * 0.01,
            "contact_person": f"店长{idx}", "phone": f"1391000{idx:04d}",
            "business_status": "active", "is_synthetic": False,
        })

    users = [
        {"username": "admin", "employee_no": "A1001", "password": "admin123", "verification_code": "246810",
         "real_name": "系统管理员", "role": "admin", "is_active": True, "is_verified": True,
         "location_type": None, "warehouse_code": None, "store_code": None, "phone": "13000000001"},
        {"username": "buyer", "employee_no": "P1001", "password": "buyer123", "verification_code": "135790",
         "real_name": "采购专员", "role": "buyer", "is_active": True, "is_verified": True,
         "location_type": None, "warehouse_code": None, "store_code": None, "phone": "13000000002"},
        {"username": "warehouse", "employee_no": "W1001", "password": "warehouse123", "verification_code": "975310",
         "real_name": "仓库主管", "role": "warehouse_manager", "is_active": True, "is_verified": True,
         "location_type": "warehouse", "warehouse_code": "WH-CENTRAL", "store_code": None, "phone": "13000000003"},
        {"username": "store", "employee_no": "S1001", "password": "store123", "verification_code": "864200",
         "real_name": "门店员工", "role": "store_staff", "is_active": True, "is_verified": True,
         "location_type": "store", "warehouse_code": None, "store_code": "STORE-A", "phone": "13000000004"},
        {"username": "manager", "employee_no": "M1001", "password": "manager123", "verification_code": "112233",
         "real_name": "运营经理", "role": "manager", "is_active": True, "is_verified": True,
         "location_type": None, "warehouse_code": None, "store_code": None, "phone": "13000000005"},
        {"username": "store_pending_a", "employee_no": "S2001", "password": "pending123", "verification_code": "246810",
         "real_name": "王敏", "role": "store_staff", "is_active": True, "is_verified": False,
         "location_type": "store", "warehouse_code": None, "store_code": "STORE-A", "phone": "13000002001"},
        {"username": "warehouse_pending_e", "employee_no": "W2001", "password": "pending123", "verification_code": "135790",
         "real_name": "李峰", "role": "warehouse_manager", "is_active": True, "is_verified": False,
         "location_type": "warehouse", "warehouse_code": "WH-EAST", "store_code": None, "phone": "13000002002"},
    ]

    # ---------- Inventory ----------
    inventory_seed = []
    warehouse_codes = [w["warehouse_code"] for w in warehouses]
    for idx, product in enumerate(products, start=1):
        warehouse_code = warehouse_codes[idx % len(warehouse_codes)]
        inventory_seed.append({
            "product_code": product["product_code"], "location_type": "warehouse",
            "warehouse_code": warehouse_code, "store_code": None,
            "current_quantity": 20 if idx % 11 == 0 else 500 + (idx % 7) * 80,
            "frozen_quantity": 0, "safety_stock": product["default_safety_stock"],
            "max_stock": product["default_safety_stock"] * (6 if idx % 13 == 0 else 12),
        })
        if idx % 3 == 0:
            inventory_seed.append({
                "product_code": product["product_code"], "location_type": "warehouse",
                "warehouse_code": warehouse_codes[(idx + 1) % len(warehouse_codes)], "store_code": None,
                "current_quantity": 1200 if idx % 10 == 0 else 180,
                "frozen_quantity": 0, "safety_stock": product["default_safety_stock"],
                "max_stock": product["default_safety_stock"] * 10,
            })
    for store in stores:
        for idx, product in enumerate(products[:25], start=1):
            inventory_seed.append({
                "product_code": product["product_code"], "location_type": "store",
                "warehouse_code": None, "store_code": store["store_code"],
                "current_quantity": 5 if idx % 8 == 0 else 40 + (idx % 6) * 5,
                "frozen_quantity": 0, "safety_stock": product["default_safety_stock"],
                "max_stock": product["default_safety_stock"] * 5,
            })

    # ---------- Monthly sales facts ----------
    monthly_sales_facts = []
    today = date.today()
    month_anchor = today.replace(day=1)
    for month_offset in range(12):
        current_month = _month_start(month_anchor, month_offset)
        for row_idx in range(220):
            product = products[row_idx % len(products)]
            store = stores[row_idx % len(stores)]
            warehouse = warehouses[row_idx % len(warehouses)]
            trend_base = 30 + (row_idx % 15) * 5
            trend = trend_base + (11 - month_offset) * (
                3 if row_idx % 7 == 0 else -1 if row_idx % 9 == 0 else 1
            )
            monthly_sales_facts.append({
                "year": current_month.year, "month": current_month.month,
                "supplier_name": supplier_products[row_idx % len(supplier_products)]["supplier_name"],
                "product_code": product["product_code"], "category_name": product["category_name"],
                "retail_sales": max(5, trend), "retail_transfers": max(1, trend // 5),
                "warehouse_sales": max(8, trend // 2),
                "store_code": store["store_code"], "warehouse_code": warehouse["warehouse_code"],
                "promo_flag": row_idx % 17 == 0,
            })

    # ---------- Purchase orders ----------
    purchase_orders = []
    for idx in range(1, 31):
        items = []
        for j in range(3):
            product = products[(idx * 3 + j) % len(products)]
            items.append({
                "product_code": product["product_code"],
                "purchase_quantity": 100 + idx * 5 + j * 10,
                "purchase_price": round(5 + idx * 0.4 + j, 2),
            })
        purchase_orders.append({
            "order_no": f"POEX{idx:04d}", "supplier_name": suppliers[idx % len(suppliers)]["name"],
            "created_by_username": "buyer", "created_at": str(today - timedelta(days=idx * 3)),
            "expected_arrival_date": str(today + timedelta(days=idx % 7)),
            "status": ["pending", "confirmed", "partially_arrived", "completed", "cancelled"][idx % 5],
            "remark": f"示例采购单 {idx}", "items": items,
        })

    # ---------- Inbound orders ----------
    inbound_orders = []
    for idx in range(1, 26):
        po = purchase_orders[idx - 1]
        inbound_orders.append({
            "inbound_no": f"INEX{idx:04d}", "purchase_order_no": po["order_no"],
            "supplier_name": po["supplier_name"],
            "warehouse_code": warehouses[idx % len(warehouses)]["warehouse_code"],
            "inbound_time": f"{today - timedelta(days=idx)}T10:00:00",
            "handled_by_username": "warehouse",
            "status": "completed" if idx % 4 else "pending", "remark": f"示例入库单 {idx}",
            "items": [{
                "product_code": item["product_code"],
                "quantity": int(item["purchase_quantity"] * (0.6 if idx % 3 == 0 else 1)),
                "batch_no": f"BATCH{idx:04d}",
                "production_date": str(today - timedelta(days=30 + idx)),
                "expiry_date": str(today + timedelta(days=180)),
            } for item in po["items"]],
        })

    # ---------- Outbound orders ----------
    outbound_orders = []
    for idx in range(1, 31):
        outbound_orders.append({
            "outbound_no": f"OUTEX{idx:04d}",
            "source_warehouse_code": warehouses[idx % len(warehouses)]["warehouse_code"],
            "target_store_code": stores[idx % len(stores)]["store_code"],
            "outbound_time": f"{today - timedelta(days=idx)}T15:00:00",
            "handled_by_username": "warehouse",
            "status": ["pending", "shipped", "signed"][idx % 3],
            "source_request_no": None, "remark": f"示例出库单 {idx}",
            "items": [{
                "product_code": products[(idx + j) % len(products)]["product_code"],
                "quantity": 10 + j * 3 + idx % 5, "batch_no": f"OB{idx:04d}",
            } for j in range(2)],
        })

    # ---------- Replenishment requests ----------
    replenishment_requests = []
    for idx in range(1, 41):
        replenishment_requests.append({
            "request_no": f"REQEX{idx:04d}",
            "store_code": stores[idx % len(stores)]["store_code"],
            "product_code": products[idx % len(products)]["product_code"],
            "request_quantity": 20 + idx, "request_reason": f"门店补货需求 {idx}",
            "request_time": f"{today - timedelta(days=idx)}T09:00:00",
            "audit_status": ["pending", "approved", "rejected", "converted"][idx % 4],
            "audited_by_username": "manager",
            "audit_time": f"{today - timedelta(days=max(1, idx - 1))}T18:00:00",
            "created_by_username": "store",
            "generated_outbound_order_no": outbound_orders[idx % len(outbound_orders)]["outbound_no"]
            if idx % 4 == 3 else None,
        })

    # ---------- Stock transactions ----------
    stock_transactions = []
    for idx in range(1, 51):
        stock_transactions.append({
            "transaction_no": f"TXEX{idx:05d}",
            "product_code": products[idx % len(products)]["product_code"],
            "transaction_type": "example_seed", "source_location_type": None,
            "source_warehouse_code": None, "source_store_code": None,
            "target_location_type": "warehouse",
            "target_warehouse_code": warehouses[idx % len(warehouses)]["warehouse_code"],
            "target_store_code": None, "change_quantity": 100 + idx,
            "before_quantity": 0, "after_quantity": 100 + idx,
            "transaction_time": f"{today - timedelta(days=idx)}T08:00:00",
            "operated_by_username": "admin",
            "related_doc_type": "example_seed", "related_doc_no": f"SEED{idx:04d}", "remark": "示例流水",
        })

    # ---------- AI recommendations ----------
    ai_recommendations = []
    for idx in range(1, 21):
        ai_recommendations.append({
            "store_code": stores[idx % len(stores)]["store_code"],
            "product_code": products[idx % len(products)]["product_code"],
            "current_stock": 10 + idx, "recent_7_sales": 20 + idx,
            "recent_30_sales": 80 + idx * 3, "avg_daily_sales": round((80 + idx * 3) / 30, 2),
            "safety_stock": 20, "recommended_quantity": 50 + idx,
            "recommended_supplier_name": suppliers[idx % len(suppliers)]["name"],
            "shortage_risk": idx % 2 == 0,
            "risk_level": ["low", "medium", "high"][idx % 3],
            "days_until_stockout": round((10 + idx) / max((80 + idx * 3) / 30, 0.1), 2),
            "reason": "规则模型生成的建议理由", "reason_enhanced": None,
            "llm_provider": "rule", "llm_used": False,
            "generated_at": f"{today}T12:00:00",
            "adoption_status": ["pending", "accepted", "rejected"][idx % 3],
        })

    # ---------- Supplier score snapshots ----------
    supplier_score_snapshots = []
    for idx, supplier in enumerate(suppliers, start=1):
        supplier_score_snapshots.append({
            "supplier_name": supplier["name"], "product_count": 4 + idx,
            "avg_lead_time_days": 2 + idx % 4, "total_purchase_amount": 5000 + idx * 1000,
            "delayed_arrival_count": idx % 3, "score": 72 + idx,
            "score_source": "example_seed", "generated_at": f"{today}T10:30:00",
        })

    # ---------- Promotions ----------
    promotions = [
        {"promotion_name": "开学季促销", "start_date": str(_safe_date(today.year, 9 if today.month >= 9 else today.month, 1)),
         "end_date": str(_safe_date(today.year, 9 if today.month >= 9 else today.month, 20)),
         "store_code": "STORE-A", "product_code": "P0021", "category_name": "文具", "promo_factor": 1.3, "description": "开学季文具热销"},
        {"promotion_name": "夏季饮料促销",
         "start_date": str(_safe_date(today.year, 6 if today.month >= 6 else today.month, 1)),
         "end_date": str(_safe_date(today.year, 8 if today.month >= 8 else today.month, 31)),
         "store_code": "STORE-B", "product_code": "P0001", "category_name": "饮料", "promo_factor": 1.4, "description": "夏季饮料销量提升"},
        {"promotion_name": "中秋节促销", "start_date": str(today),
         "end_date": str(today + timedelta(days=10)), "store_code": "STORE-C",
         "product_code": None, "category_name": "零食", "promo_factor": 1.2, "description": "节日礼盒促销"},
        {"promotion_name": "双十一促销", "start_date": str(today),
         "end_date": str(today + timedelta(days=5)), "store_code": "STORE-D",
         "product_code": None, "category_name": "日用品", "promo_factor": 1.5, "description": "双十一爆品活动"},
        {"promotion_name": "冬季日用品促销", "start_date": str(today),
         "end_date": str(today + timedelta(days=30)), "store_code": "STORE-E",
         "product_code": "P0017", "category_name": "日用品", "promo_factor": 1.15, "description": "冬季消耗品备货"},
    ]

    files = {
        "categories.json": categories,
        "products.json": products,
        "suppliers.json": suppliers,
        "supplier_products.json": supplier_products,
        "warehouses.json": warehouses,
        "stores.json": stores,
        "users.json": users,
        "inventory_seed.json": inventory_seed,
        "monthly_sales_facts.json": monthly_sales_facts,
        "purchase_orders.json": purchase_orders,
        "inbound_orders.json": inbound_orders,
        "outbound_orders.json": outbound_orders,
        "replenishment_requests.json": replenishment_requests,
        "stock_transactions.json": stock_transactions,
        "ai_recommendations.json": ai_recommendations,
        "supplier_score_snapshots.json": supplier_score_snapshots,
        "promotions.json": promotions,
    }

    counts = {}
    for name, data in files.items():
        _write_json(example_dir / name, data)
        counts[name.replace(".json", "")] = len(data) if isinstance(data, list) else 1

    return counts


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_id_from_code(db: Session, model, code_field: str, code_value: str) -> int | None:
    """根据编码字段查询模型 ID。"""
    row = db.scalar(select(model).where(getattr(model, code_field) == code_value))
    return row.id if row else None


def _get_id_from_name(db: Session, model, name_field: str, name_value: str) -> int | None:
    """根据名称字段查询模型 ID。"""
    row = db.scalar(select(model).where(getattr(model, name_field) == name_value))
    return row.id if row else None


def load_example_data(db: Session) -> dict[str, int]:
    """从 example/ 目录加载 JSON 数据到数据库。"""
    settings = get_settings()
    example_dir = settings.example_dir_path
    if not example_dir.exists():
        return {"error": "example data directory not found"}

    from agents.product_agent.models import Product, Category
    from agents.supplier_agent.models import Supplier, SupplierProduct, SupplierScoreSnapshot
    from agents.warehouse_agent.models import Warehouse
    from agents.store_agent.models import Store
    from agents.user_agent.models import User
    from agents.inventory_agent.models import Inventory
    from agents.recommendation_agent.models import AIRecommendation, MonthlySalesFact
    from agents.procurement_agent.models import PurchaseOrder, PurchaseOrderItem, InboundOrder, InboundItem
    from agents.fulfillment_agent.models import ReplenishmentRequest, OutboundOrder, OutboundItem
    from agents.transaction_agent.models import StockTransaction

    counts = {}

    # Categories
    categories_data = _load_json(example_dir / "categories.json")
    cat_name_map = {}
    for item in categories_data:
        c = Category(name=item["name"])
        db.add(c)
        db.flush()
        cat_name_map[item["name"]] = c.id
    # Second pass for parent
    for item in categories_data:
        if item["parent_name"]:
            child = db.scalar(select(Category).where(Category.name == item["name"]))
            parent = db.scalar(select(Category).where(Category.name == item["parent_name"]))
            if child and parent:
                child.parent_id = parent.id
    counts["categories"] = len(categories_data)

    # Products
    products_data = _load_json(example_dir / "products.json")
    product_code_map = {}
    for item in products_data:
        p = Product(
            product_code=item["product_code"], name=item["name"], barcode=item.get("barcode"),
            category_id=cat_name_map.get(item.get("category_name")),
            spec=item.get("spec"), unit=item.get("unit"),
            shelf_life_days=item.get("shelf_life_days"), default_safety_stock=item.get("default_safety_stock", 0),
            is_active=item.get("is_active", True),
        )
        db.add(p)
        db.flush()
        product_code_map[item["product_code"]] = p.id
    counts["products"] = len(products_data)

    # Suppliers
    suppliers_data = _load_json(example_dir / "suppliers.json")
    supplier_name_map = {}
    for item in suppliers_data:
        s = Supplier(name=item["name"], contact_person=item.get("contact_person"),
                     phone=item.get("phone"), email=item.get("email"), address=item.get("address"),
                     supplier_level=item.get("supplier_level"), cooperation_status=item.get("cooperation_status", "active"),
                     is_active=item.get("is_active", True))
        db.add(s)
        db.flush()
        supplier_name_map[item["name"]] = s.id
    counts["suppliers"] = len(suppliers_data)

    # SupplierProducts
    sp_data = _load_json(example_dir / "supplier_products.json")
    for item in sp_data:
        supplier_id = supplier_name_map.get(item["supplier_name"])
        product_id = product_code_map.get(item["product_code"])
        if supplier_id and product_id:
            sp = SupplierProduct(supplier_id=supplier_id, product_id=product_id,
                                supply_price=item.get("supply_price"),
                                lead_time_days=item.get("lead_time_days"),
                                on_time_rate=item.get("on_time_rate"),
                                quality_score=item.get("quality_score"),
                                is_preferred=item.get("is_preferred", False))
            db.add(sp)
    counts["supplier_products"] = len(sp_data)

    # Warehouses
    warehouses_data = _load_json(example_dir / "warehouses.json")
    wh_code_map = {}
    for item in warehouses_data:
        w = Warehouse(warehouse_code=item["warehouse_code"], name=item["name"],
                      address=item.get("address"), manager_name=item.get("manager_name"),
                      phone=item.get("phone"), capacity=item.get("max_capacity", 0),
                      status=item.get("status", "active"))
        db.add(w)
        db.flush()
        wh_code_map[item["warehouse_code"]] = w.id
    counts["warehouses"] = len(warehouses_data)

    # Stores
    stores_data = _load_json(example_dir / "stores.json")
    store_code_map = {}
    for item in stores_data:
        s = Store(store_code=item["store_code"], name=item["name"], region=item.get("region"),
                  address=item.get("address"), longitude=item.get("longitude"), latitude=item.get("latitude"),
                  contact_person=item.get("contact_person"), phone=item.get("phone"),
                  business_status=item.get("business_status", "active"))
        db.add(s)
        db.flush()
        store_code_map[item["store_code"]] = s.id
    counts["stores"] = len(stores_data)

    # Users
    users_data = _load_json(example_dir / "users.json")
    username_map = {}
    for item in users_data:
        wh_id = wh_code_map.get(item["warehouse_code"]) if item.get("warehouse_code") else None
        st_id = store_code_map.get(item["store_code"]) if item.get("store_code") else None
        u = db.scalar(select(User).where(or_(User.username == item["username"], User.employee_no == item["employee_no"])))
        if not u:
            u = User(username=item["username"], employee_no=item["employee_no"])
            db.add(u)
        u.password_hash = hash_password(item["password"])
        u.verification_code_hash = hash_password(item.get("verification_code", "000000"))
        u.real_name = item.get("real_name")
        u.role = item["role"]
        u.location_type = item.get("location_type")
        u.warehouse_id = wh_id
        u.store_id = st_id
        u.phone = item.get("phone")
        u.is_active = item.get("is_active", True)
        u.is_verified = item.get("is_verified", False)
        db.flush()
        username_map[item["username"]] = u.id
    counts["users"] = len(users_data)

    # Inventory
    inv_data = _load_json(example_dir / "inventory_seed.json")
    for item in inv_data:
        wh_id = wh_code_map.get(item["warehouse_code"]) if item.get("warehouse_code") else None
        st_id = store_code_map.get(item["store_code"]) if item.get("store_code") else None
        product_id = product_code_map.get(item["product_code"])
        if product_id:
            inv = Inventory(product_id=product_id, location_type=item["location_type"],
                           warehouse_id=wh_id, store_id=st_id,
                           current_quantity=item.get("current_quantity", 0),
                           frozen_quantity=item.get("frozen_quantity", 0),
                           safety_stock=item.get("safety_stock", 0), max_stock=item.get("max_stock", 0))
            db.add(inv)
    counts["inventory_records"] = len(inv_data)

    # MonthlySalesFacts
    msf_data = _load_json(example_dir / "monthly_sales_facts.json")
    for item in msf_data:
        supplier_id = supplier_name_map.get(item["supplier_name"])
        product_id = product_code_map.get(item["product_code"])
        category_id = cat_name_map.get(item.get("category_name"))
        store_id = store_code_map.get(item["store_code"])
        wh_id = wh_code_map.get(item["warehouse_code"])
        if product_id:
            msf = MonthlySalesFact(year=item["year"], month=item["month"],
                                  supplier_id=supplier_id, product_id=product_id,
                                  category_id=category_id,
                                  retail_sales=item.get("retail_sales", 0),
                                  retail_transfers=item.get("retail_transfers", 0),
                                  warehouse_sales=item.get("warehouse_sales", 0),
                                  store_id=store_id, warehouse_id=wh_id,
                                  promo_flag=item.get("promo_flag", False))
            db.add(msf)
    counts["monthly_sales_facts"] = len(msf_data)

    # PurchaseOrders
    po_data = _load_json(example_dir / "purchase_orders.json")
    po_no_map = {}
    po_supplier_map = {}
    for item in po_data:
        supplier_id = supplier_name_map.get(item["supplier_name"])
        created_by_id = username_map.get(item.get("created_by_username"))
        po = PurchaseOrder(order_no=item["order_no"], supplier_id=supplier_id,
                          created_by=created_by_id, created_at=_parse_datetime(item.get("created_at")),
                          expected_arrival_date=_parse_date(item.get("expected_arrival_date")),
                          status=item.get("status", "pending"), total_amount=0,
                          remark=item.get("remark"))
        db.add(po)
        db.flush()
        po_no_map[item["order_no"]] = po.id
        po_supplier_map[item["order_no"]] = supplier_id
        total = 0
        for poi in item.get("items", []):
            product_id = product_code_map.get(poi["product_code"])
            if product_id:
                qty = poi["purchase_quantity"]
                price = poi["purchase_price"]
                subtotal = qty * price
                db.add(PurchaseOrderItem(purchase_order_id=po.id, product_id=product_id,
                                        purchase_quantity=qty, purchase_price=price,
                                        subtotal_amount=subtotal))
                total += subtotal
        po.total_amount = total
    counts["purchase_orders"] = len(po_data)

    # InboundOrders
    ib_data = _load_json(example_dir / "inbound_orders.json")
    for item in ib_data:
        po_id = po_no_map.get(item.get("purchase_order_no"))
        supplier_id = po_supplier_map.get(item.get("purchase_order_no"))
        wh_id = wh_code_map.get(item.get("warehouse_code"))
        handled_by_id = username_map.get(item.get("handled_by_username"))
        ib = InboundOrder(inbound_no=item["inbound_no"], purchase_order_id=po_id,
                         supplier_id=supplier_id, warehouse_id=wh_id, inbound_time=_parse_datetime(item.get("inbound_time")),
                         handled_by=handled_by_id, status=item.get("status", "pending"),
                         remark=item.get("remark"))
        db.add(ib)
        db.flush()
        for ibi in item.get("items", []):
            product_id = product_code_map.get(ibi["product_code"])
            if product_id:
                db.add(InboundItem(inbound_order_id=ib.id, product_id=product_id,
                                  quantity=ibi["quantity"], batch_no=ibi.get("batch_no"),
                                  production_date=_parse_date(ibi.get("production_date")),
                                  expiry_date=_parse_date(ibi.get("expiry_date"))))
    counts["inbound_orders"] = len(ib_data)

    # OutboundOrders + ReplenishmentRequests
    ob_data = _load_json(example_dir / "outbound_orders.json")
    ob_no_map = {}
    for item in ob_data:
        wh_id = wh_code_map.get(item["source_warehouse_code"])
        st_id = store_code_map.get(item["target_store_code"])
        handled_by_id = username_map.get(item.get("handled_by_username"))
        ob = OutboundOrder(outbound_no=item["outbound_no"], source_warehouse_id=wh_id,
                          target_store_id=st_id, outbound_time=_parse_datetime(item.get("outbound_time")),
                          handled_by=handled_by_id, status=item.get("status", "pending"),
                          remark=item.get("remark"))
        db.add(ob)
        db.flush()
        ob_no_map[item["outbound_no"]] = ob.id
        for obi in item.get("items", []):
            product_id = product_code_map.get(obi["product_code"])
            if product_id:
                db.add(OutboundItem(outbound_order_id=ob.id, product_id=product_id,
                                   quantity=obi["quantity"], batch_no=obi.get("batch_no")))
    counts["outbound_orders"] = len(ob_data)

    # ReplenishmentRequests
    rr_data = _load_json(example_dir / "replenishment_requests.json")
    for item in rr_data:
        st_id = store_code_map.get(item["store_code"])
        product_id = product_code_map.get(item["product_code"])
        created_by_id = username_map.get(item.get("created_by_username"))
        audited_by_id = username_map.get(item.get("audited_by_username"))
        gen_ob_id = ob_no_map.get(item.get("generated_outbound_order_no")) if item.get("generated_outbound_order_no") else None
        if product_id:
            rr = ReplenishmentRequest(request_no=item["request_no"], store_id=st_id,
                                     product_id=product_id, request_quantity=item["request_quantity"],
                                     request_reason=item.get("request_reason"),
                                     request_time=_parse_datetime(item.get("request_time")),
                                     audit_status=item.get("audit_status", "pending"),
                                     audited_by=audited_by_id, audit_time=_parse_datetime(item.get("audit_time")),
                                     created_by=created_by_id,
                                     generated_outbound_order_id=gen_ob_id)
            db.add(rr)
    counts["replenishment_requests"] = len(rr_data)

    # StockTransactions
    tx_data = _load_json(example_dir / "stock_transactions.json")
    for item in tx_data:
        product_id = product_code_map.get(item["product_code"])
        target_wh_id = wh_code_map.get(item["target_warehouse_code"]) if item.get("target_warehouse_code") else None
        operated_by_id = username_map.get(item.get("operated_by_username"))
        if product_id:
            tx = StockTransaction(transaction_no=item["transaction_no"], product_id=product_id,
                                 transaction_type=item["transaction_type"],
                                 source_location_type=item.get("source_location_type"),
                                 target_location_type=item.get("target_location_type"),
                                 target_warehouse_id=target_wh_id,
                                 change_quantity=item["change_quantity"],
                                 before_quantity=item.get("before_quantity"),
                                 after_quantity=item.get("after_quantity"),
                                 transaction_time=_parse_datetime(item.get("transaction_time")),
                                 operated_by=operated_by_id,
                                 related_doc_type=item.get("related_doc_type"),
                                 remark=item.get("remark"))
            db.add(tx)
    counts["stock_transactions"] = len(tx_data)

    # AIRecommendations
    rec_data = _load_json(example_dir / "ai_recommendations.json")
    for item in rec_data:
        st_id = store_code_map.get(item["store_code"])
        product_id = product_code_map.get(item["product_code"])
        supplier_id = supplier_name_map.get(item.get("recommended_supplier_name"))
        if product_id:
            rec = AIRecommendation(store_id=st_id, product_id=product_id,
                                  current_stock=item.get("current_stock"),
                                  recent_7_sales=item.get("recent_7_sales"),
                                  recent_30_sales=item.get("recent_30_sales"),
                                  avg_daily_sales=item.get("avg_daily_sales"),
                                  safety_stock=item.get("safety_stock"),
                                  recommended_quantity=item["recommended_quantity"],
                                  recommended_supplier_id=supplier_id,
                                  shortage_risk=item.get("shortage_risk", False),
                                  risk_level=item.get("risk_level", "low"),
                                  days_until_stockout=item.get("days_until_stockout"),
                                  reason=item["reason"], reason_enhanced=item.get("reason_enhanced"),
                                  llm_provider=item.get("llm_provider", "rule"),
                                  llm_used=item.get("llm_used", False),
                                  generated_at=_parse_datetime(item.get("generated_at")),
                                  adoption_status=item.get("adoption_status", "pending"))
            db.add(rec)
    counts["ai_recommendations"] = len(rec_data)

    # SupplierScoreSnapshots
    sss_data = _load_json(example_dir / "supplier_score_snapshots.json")
    for item in sss_data:
        supplier_id = supplier_name_map.get(item["supplier_name"])
        if supplier_id:
            sss = SupplierScoreSnapshot(supplier_id=supplier_id, product_count=item.get("product_count"),
                                       avg_lead_time_days=item.get("avg_lead_time_days"),
                                       total_purchase_amount=item.get("total_purchase_amount"),
                                       delayed_arrival_count=item.get("delayed_arrival_count"),
                                       score=item.get("score"), score_source=item.get("score_source"),
                                       generated_at=_parse_datetime(item.get("generated_at")))
            db.add(sss)
    counts["supplier_score_snapshots"] = len(sss_data)

    db.flush()
    return counts


def get_example_status(db: Session) -> dict[str, int]:
    """获取当前示例数据状态（各表记录数）。"""
    from agents.product_agent.models import Product
    from agents.supplier_agent.models import Supplier
    from agents.warehouse_agent.models import Warehouse
    from agents.store_agent.models import Store
    from agents.inventory_agent.models import Inventory
    from agents.procurement_agent.models import InboundOrder
    from agents.fulfillment_agent.models import OutboundOrder, ReplenishmentRequest
    from agents.transaction_agent.models import StockTransaction

    return {
        "products": db.scalar(select(func.count(Product.id))) or 0,
        "suppliers": db.scalar(select(func.count(Supplier.id))) or 0,
        "warehouses": db.scalar(select(func.count(Warehouse.id))) or 0,
        "stores": db.scalar(select(func.count(Store.id))) or 0,
        "inventory_records": db.scalar(select(func.count(Inventory.id))) or 0,
        "inbound_orders": db.scalar(select(func.count(InboundOrder.id))) or 0,
        "outbound_orders": db.scalar(select(func.count(OutboundOrder.id))) or 0,
        "replenishment_requests": db.scalar(select(func.count(ReplenishmentRequest.id))) or 0,
        "stock_transactions": db.scalar(select(func.count(StockTransaction.id))) or 0,
    }
