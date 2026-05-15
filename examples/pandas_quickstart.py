"""Pandas quickstart for PipeDoctor."""

import pandas as pd

from pipedoctor import diagnose, diagnose_join


orders = pd.DataFrame(
    {
        "order_id": [1, 1, 2, 3, 4, 5, 6, 7],
        "customer_id": [101, 101, 102, None, None, 104, 105, 106],
        "country": ["US", "US", "US", "US", "IN", "US", "UK", "US"],
        "amount": [120.0, 120.0, 75.0, 9999.0, 225.0, 180.0, 60.0, 15.0],
        "event_time": pd.to_datetime(
            [
                "2026-05-01 10:00",
                "2026-05-01 10:00",
                "2026-05-01 10:02",
                "2026-05-01 09:59",
                "2026-05-01 10:04",
                "2026-05-01 10:05",
                "2026-05-01 10:06",
                "2026-05-01 10:07",
            ]
        ),
    }
)

customers = pd.DataFrame(
    {
        "customer_id": [101, 101, 102, 103, 104, 105],
        "segment": ["enterprise", "enterprise", "smb", "smb", "midmarket", "smb"],
    }
)


if __name__ == "__main__":
    report = diagnose(
        orders,
        name="orders",
        key_columns=["customer_id"],
        critical_columns=["customer_id"],
        cdc_order_column="event_time",
    )
    report.to_markdown("orders-report.md")

    diagnose_join(orders, customers, on=["customer_id"])
