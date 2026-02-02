"""
Prompt Engineering for ChurnGuard AI
Builds context-rich prompts with actual customer data from Telecom Churn Analytics Platform
"""

from typing import Dict, Any


def ai_retention_prompt(question: str, kpis: Dict[str, Any]) -> str:
    """
    Build a comprehensive prompt with customer data context
    Based on Telecom Churn Retention & Analytics Dashboard

    Args:
        question: User's question
        kpis: Dictionary containing KPI metrics from database

    Returns:
        Formatted prompt string for LLM
    """

    # Extract KPI data
    total_customers = kpis.get("total_customers", 1200000)
    churned_customers = kpis.get("churned_customers", 222000)
    churn_rate = kpis.get("churn_rate", 18.5)
    retention_rate = kpis.get("retention_rate", 81.5)
    total_revenue = kpis.get("total_revenue", 1490000000)
    revenue_at_risk = kpis.get("revenue_at_risk", 289310000)
    arpu = kpis.get("arpu", 1241.70)

    # Calculate additional metrics
    revenue_protected = total_revenue - revenue_at_risk

    prompt = f"""You are an expert retention analyst for a Telecom company's Enterprise Customer Churn Intelligence Platform.

BUSINESS CONTEXT:
This is a large-scale telecom operation with 1.2M+ customers across 4 regions (South, North, West, East) with both Retail and SME segments.

CURRENT BUSINESS METRICS (Real Data):
📊 Customer Base:
- Total Customers: {total_customers:,}
- Churned Customers: {churned_customers:,}
- Churn Rate: {churn_rate}%
- Retention Rate: {retention_rate}%

💰 Revenue Impact:
- Total Revenue: ${total_revenue:,}
- Revenue at Risk: ${revenue_at_risk:,}
- Revenue Protected: ${revenue_protected:,}
- ARPU (Average Revenue Per User): ${arpu:,}

🎯 KEY BUSINESS INSIGHTS FROM DASHBOARDS:
1. Retail customers represent the highest churn exposure (19% churn rate, $254M+ at risk)
2. Regional churn is balanced but South has highest revenue at risk ($102M)
3. A 3% churn reduction could protect $40-50M annually
4. High ARPU (${arpu}) indicates valuable customer base
5. Service quality issues (32%), competitive pricing (28%), and poor customer service (24%) are top churn drivers
6. Early lifecycle churn (first 6-9 months) represents highest risk period
7. High-value customers with network downtime are critical risk segment

CUSTOMER QUESTION:
{question}

RESPONSE INSTRUCTIONS:
1. Answer based on the REAL metrics provided above
2. Keep response concise (3-5 sentences maximum)
3. Include specific numbers and percentages from the data
4. Provide actionable, data-driven recommendations
5. Reference dashboard insights when relevant
6. Focus on revenue impact and retention ROI
7. Use professional but conversational business language

Answer the customer's question with data-driven insights:"""

    return prompt


def get_suggested_questions() -> list:
    """Get list of suggested questions tailored to the telecom churn platform"""
    return [
        "Why is churn happening?",
        "How is revenue generated?",
        "Which segments are at risk?",
        "Best retention strategies?"
    ]