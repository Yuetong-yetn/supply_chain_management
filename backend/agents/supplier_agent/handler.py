from sqlalchemy import delete, func, select
from kernel.common.database import Session
from kernel.common.exceptions import BusinessException
from .models import Supplier, SupplierProduct, SupplierScoreSnapshot

def list_suppliers(db: Session, page=1, page_size=20, keyword=None):
    q = select(Supplier)
    if keyword: q = q.where(Supplier.name.contains(keyword))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(db.scalars(q.offset((page-1)*page_size).limit(page_size)))
    return items, total

def create_supplier(db: Session, data: dict):
    s = Supplier(**data); db.add(s); db.flush(); return s

def get_supplier(db: Session, sid: int):
    s = db.get(Supplier, sid)
    if not s: raise BusinessException("supplier not found", 404)
    return s

def get_supplier_products(db: Session, sid: int):
    return list(db.scalars(select(SupplierProduct).where(SupplierProduct.supplier_id == sid)))

def recalculate_scores(db: Session):
    db.execute(delete(SupplierScoreSnapshot))
    suppliers = list(db.scalars(select(Supplier)))
    snapshots = []
    for s in suppliers:
        products = list(db.scalars(select(SupplierProduct).where(SupplierProduct.supplier_id == s.id)))
        count = len(products)
        if count == 0:
            snapshots.append(SupplierScoreSnapshot(supplier_id=s.id, product_count=0, score=0, score_source="no_data"))
            continue
        avg_lt = sum(p.lead_time_days for p in products) / count
        avg_ot = sum(p.on_time_rate for p in products) / count
        avg_q = sum(p.quality_score for p in products) / count
        delayed = max(0, int(count * (1 - avg_ot) * 10))
        score = max(0, min(100, round(100 - avg_lt*2 - delayed*5 + avg_ot*20 + avg_q*10, 2)))
        snapshots.append(SupplierScoreSnapshot(
            supplier_id=s.id, product_count=count, avg_lead_time_days=avg_lt,
            delayed_arrival_count=delayed, score=score, score_source="calculated",
        ))
    for snap in snapshots: db.add(snap)
    db.flush()
    return snapshots

def get_ranking(db: Session):
    return list(db.scalars(select(SupplierScoreSnapshot).order_by(SupplierScoreSnapshot.score.desc())))

def get_supplier_score(db: Session, sid: int):
    return db.scalar(select(SupplierScoreSnapshot).where(SupplierScoreSnapshot.supplier_id == sid).order_by(SupplierScoreSnapshot.generated_at.desc()))


def bind_supplier_product(db: Session, sid: int, data: dict) -> SupplierProduct:
    """绑定商品到供应商。"""
    product_id = data.get("product_id")
    if not product_id:
        raise BusinessException("product_id is required")
    # 检查是否已存在相同绑定
    existing = db.scalar(
        select(SupplierProduct).where(
            SupplierProduct.supplier_id == sid,
            SupplierProduct.product_id == int(product_id),
        )
    )
    if existing:
        raise BusinessException("该商品已绑定到此供应商")
    sp = SupplierProduct(
        supplier_id=sid,
        product_id=int(product_id),
        supply_price=data.get("supply_price"),
        lead_time_days=data.get("lead_time_days"),
        on_time_rate=data.get("on_time_rate"),
        quality_score=data.get("quality_score"),
        is_preferred=data.get("is_preferred", False),
    )
    db.add(sp)
    db.flush()
    return sp
