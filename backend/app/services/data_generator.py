import random

from app.models import InventoryItem


CATEGORIES = ["Raw Materials", "Fasteners", "Electrical", "Packaging", "Machined Parts"]
SUPPLIERS = ["Northline Supply", "Atlas Components", "Prime Industrial", "Maple Parts", "Vertex Manufacturing"]


def generate_inventory(seed: int = 42, count: int = 40) -> list[InventoryItem]:
    rng = random.Random(seed)
    items: list[InventoryItem] = []

    for index in range(1, count + 1):
        daily_demand = round(rng.uniform(2.5, 28.0), 1)
        lead_time = rng.randint(4, 25)
        safety_stock = rng.randint(15, 140)
        baseline = daily_demand * lead_time + safety_stock
        stock_factor = rng.uniform(0.25, 2.1)

        items.append(
            InventoryItem(
                sku=f"MAT-{index:04d}",
                name=f"Manufacturing Item {index:02d}",
                category=rng.choice(CATEGORIES),
                on_hand=max(0, int(baseline * stock_factor)),
                daily_demand=daily_demand,
                lead_time_days=lead_time,
                supplier_reliability=round(rng.uniform(0.78, 0.99), 2),
                safety_stock=safety_stock,
                unit_cost=round(rng.uniform(3.5, 240.0), 2),
                supplier=rng.choice(SUPPLIERS),
            )
        )

    return items
