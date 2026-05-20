def recommendation_prompt(rule_reason: str) -> str:
    return f"请润色以下补货建议理由，保持业务含义不变，用中文输出：\n{rule_reason}"


def analytics_summary_prompt(data: dict) -> str:
    return f"请根据以下供应链经营数据生成中文摘要，突出缺货、积压、需求热度和供应商表现：\n{data}"
