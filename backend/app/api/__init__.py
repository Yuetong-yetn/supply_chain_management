"""统一 API 路由注册。

所有业务路由在 app/api/routers/ 下定义，通过此入口统一挂载到 FastAPI 应用。
"""

from fastapi import FastAPI


def register_business_routes(app: FastAPI) -> None:
    """注册所有业务路由到 FastAPI 应用（非 AI 部分）。"""
    from app.api.routers.users import router as users_router
    from app.api.routers.products import router as products_router
    from app.api.routers.suppliers import router as suppliers_router
    from app.api.routers.procurement import router as procurement_router
    from app.api.routers.inventory import router as inventory_router
    from app.api.routers.warehouses import router as warehouses_router
    from app.api.routers.stores import router as stores_router
    from app.api.routers.fulfillment import router as fulfillment_router
    from app.api.routers.transactions import router as transactions_router
    from app.api.routers.analytics import router as analytics_router
    from app.api.routers.monitoring import router as monitoring_router

    for r in [
        users_router, products_router, suppliers_router,
        procurement_router, inventory_router, warehouses_router,
        stores_router, fulfillment_router, transactions_router,
        analytics_router, monitoring_router,
    ]:
        app.include_router(r)
