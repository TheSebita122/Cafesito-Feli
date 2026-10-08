import numpy as np
import pandas as pd

STORES = {1: "Alpha Street", 2: "Beta Avenue", 3: "Gamma Square"}

PRODUCTS = [
    (1, "Coffee", "Barista Espresso", "Espresso Shot", 3.0),
    (2, "Coffee", "Barista Espresso", "Double Espresso", 3.5),
    (3, "Coffee", "Gourmet brewed coffee", "House Blend", 2.5),
    (4, "Coffee", "Gourmet brewed coffee", "Dark Roast", 2.7),
    (5, "Tea", "Brewed Chai tea", "Chai Regular", 3.1),
    (6, "Tea", "Brewed Black tea", "Earl Grey", 2.5),
    (7, "Flavours", "Regular syrup", "Hazelnut Syrup", 0.8),
    (8, "Flavours", "Sugar free syrup", "Vanilla Syrup", 0.8),
    (9, "Bakery", "Scone", "Cranberry Scone", 3.5),
    (10, "Coffee beans", "Premium beans", "Ethiopia Beans", 20.0),
    (11, "Coffee beans", "Premium beans", "Colombia Beans", 22.0),
    (12, "Branded", "Clothing", "Cafesito Shirt", 28.0),
]
PARTNERS = {1: 7, 2: 8, 3: 9}
HOURLY_WEIGHT = {
    7: 3.0,
    8: 3.5,
    9: 3.0,
    10: 2.0,
    11: 1.0,
    12: 1.0,
    13: 0.8,
    14: 0.8,
    15: 0.7,
    16: 0.7,
}
COLUMNS = [
    "transaction_id",
    "transaction_date",
    "transaction_time",
    "transaction_qty",
    "store_id",
    "store_location",
    "product_id",
    "unit_price",
    "product_category",
    "product_type",
    "product_detail",
]


def build_sales_frame(days: int = 40, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    catalogue = {pid: (cat, ptype, detail, price) for pid, cat, ptype, detail, price in PRODUCTS}
    popular = [1, 2, 3, 4, 5, 6, 9]
    rare = [10, 11, 12]
    rows: list[dict[str, object]] = []
    transaction_id = 1

    def add_line(day: pd.Timestamp, hour: int, store_id: int, product_id: int, second: int) -> None:
        nonlocal transaction_id
        category, product_type, detail, price = catalogue[product_id]
        rows.append(
            {
                "transaction_id": transaction_id,
                "transaction_date": f"{day.month}/{day.day}/{day.strftime('%y')}",
                "transaction_time": f"{hour}:{second // 60:02d}:{second % 60:02d}",
                "transaction_qty": int(rng.integers(1, 3)),
                "store_id": store_id,
                "store_location": STORES[store_id],
                "product_id": product_id,
                "unit_price": price,
                "product_category": category,
                "product_type": product_type,
                "product_detail": detail,
            }
        )
        transaction_id += 1

    for offset in range(days):
        day = pd.Timestamp("2023-01-02") + pd.Timedelta(days=offset)
        month_boost = 1.0 + 0.5 * (day.month - 1)
        for store_id in STORES:
            for hour, weight in HOURLY_WEIGHT.items():
                count = int(rng.poisson(6 * weight * month_boost))
                used_seconds: set[int] = set()
                for _ in range(count):
                    second = int(rng.integers(0, 3600))
                    while second in used_seconds:
                        second = int(rng.integers(0, 3600))
                    used_seconds.add(second)
                    if rng.random() < 0.03:
                        product_id = int(rng.choice(rare))
                    else:
                        product_id = int(rng.choice(popular))
                    add_line(day, hour, store_id, product_id, second)
                    if product_id in PARTNERS and rng.random() < 0.7:
                        add_line(day, hour, store_id, PARTNERS[product_id], second)
    return pd.DataFrame(rows, columns=COLUMNS)
