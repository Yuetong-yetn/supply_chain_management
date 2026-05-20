from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analytics import MonthlySalesFact, SupplierScoreSnapshot
from app.models.purchase import PurchaseOrder
from app.models.supplier import Supplier, SupplierProduct
from app.utils.datetime_utils import now_local


def calculate_supplier_score(avg_lead_time_days: float, delayed_arrival_count: int, on_time_rate: float, quality_score: float) -> float:
    score = 100 - avg_lead_time_days * 2 - delayed_arrival_count * 5 + on_time_rate * 20 + quality_score * 10
    return max(0, min(100, round(score, 2)))


def recalculate_scores(db: Session) -> list[SupplierScoreSnapshot]:
    db.query(SupplierScoreSnapshot).delete()
    snapshots: list[SupplierScoreSnapshot] = []
    suppliers = list(db.scalars(select(Supplier)))
    for supplier in suppliers:
        relations = list(db.scalars(select(SupplierProduct).where(SupplierProduct.supplier_id == supplier.id)))
        product_count = len(relations)
        avg_lead_time = sum(item.lead_time_days for item in relations) / product_count if product_count else 0
        avg_on_time = sum(item.on_time_rate for item in relations) / product_count if product_count else 0
        avg_quality = sum(item.quality_score for item in relations) / product_count if product_count else 0
        total_purchase_amount = db.scalar(
            select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0)).where(PurchaseOrder.supplier_id == supplier.id)
        ) or Decimal("0.00")
        activity = db.scalar(
            select(func.count(MonthlySalesFact.id)).where(MonthlySalesFact.supplier_id == supplier.id)
        ) or 0
        delayed_arrival_count = max(0, int(product_count * (1 - avg_on_time) * 10 + activity * 0.01))
        score_source = "real_purchase_data" if total_purchase_amount else "estimated_from_sales"
        snapshot = SupplierScoreSnapshot(
            supplier_id=supplier.id,
            product_count=product_count,
            avg_lead_time_days=avg_lead_time,
            total_purchase_amount=total_purchase_amount,
            delayed_arrival_count=delayed_arrival_count,
            score=calculate_supplier_score(avg_lead_time, delayed_arrival_count, avg_on_time, avg_quality),
            score_source=score_source if activity else "example_seed",
            generated_at=now_local(),
        )
        db.add(snapshot)
        snapshots.append(snapshot)
    db.flush()
    return snapshots


def get_supplier_score(db: Session, supplier_id: int) -> SupplierScoreSnapshot | None:
    return db.scalar(
        select(SupplierScoreSnapshot)
        .where(SupplierScoreSnapshot.supplier_id == supplier_id)
        .order_by(SupplierScoreSnapshot.generated_at.desc())
    )


def get_supplier_ranking(db: Session) -> list[SupplierScoreSnapshot]:
    return list(db.scalars(select(SupplierScoreSnapshot).order_by(SupplierScoreSnapshot.score.desc())))
