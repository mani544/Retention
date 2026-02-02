#queries.py file

import pandas as pd
from services.db import get_engine

engine = get_engine()


def load_kpis():
    query = """
    SELECT
        SUM(total_customers) as total_customers,
        SUM(churned_customers) as churned,
        AVG(churn_rate) as churn_rate,
        AVG(retention_rate) as retention_rate,
        SUM(total_revenue) as revenue,
        SUM(revenue_at_risk) as risk
    FROM mart_retention_kpis;
    """
    return pd.read_sql(query, engine)


def churn_by_region():
    query = """
    SELECT region,
           AVG(churn_rate) as churn_rate
    FROM mart_retention_kpis
    GROUP BY region;
    """
    return pd.read_sql(query, engine)


def revenue_by_region():
    query = """
    SELECT region,
           SUM(total_revenue) as revenue
    FROM mart_retention_kpis
    GROUP BY region;
    """
    return pd.read_sql(query, engine)


def segment_metrics():
    query = """
    SELECT customer_segment,
           SUM(total_customers) as customers,
           SUM(revenue_at_risk) as risk
    FROM mart_retention_kpis
    GROUP BY customer_segment;
    """
    return pd.read_sql(query, engine)
