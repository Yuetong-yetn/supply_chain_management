"""Agent 注册入口。"""

from kernel.sisyphus.orchestrator import SisyphusOrchestrator


def register_all_agents(orchestrator: SisyphusOrchestrator) -> None:
    """启动时注册所有 Agent 到 Sisyphus。"""
    from agents.user_agent.agent import UserAgent
    from agents.product_agent.agent import ProductAgent
    from agents.supplier_agent.agent import SupplierAgent
    from agents.procurement_agent.agent import ProcurementAgent
    from agents.inventory_agent.agent import InventoryAgent
    from agents.warehouse_agent.agent import WarehouseAgent
    from agents.store_agent.agent import StoreAgent
    from agents.fulfillment_agent.agent import FulfillmentAgent
    from agents.transaction_agent.agent import TransactionAgent
    from agents.analytics_agent.agent import AnalyticsAgent
    from agents.recommendation_agent.agent import RecommendationAgent
    from agents.monitoring_agent.agent import MonitoringAgent

    agents = [
        UserAgent(),
        ProductAgent(),
        SupplierAgent(),
        ProcurementAgent(),
        InventoryAgent(),
        WarehouseAgent(),
        StoreAgent(),
        FulfillmentAgent(),
        TransactionAgent(),
        AnalyticsAgent(),
        RecommendationAgent(),
        MonitoringAgent(),
    ]
    for agent in agents:
        orchestrator.register_agent(agent)
