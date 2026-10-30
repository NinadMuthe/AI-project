import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_transactions.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

start_date = date(2026, 5, 1)
end_date = date(2026, 10, 28)

records = []

# Recurring monthly salary and rent/bills
current = start_date
while current <= end_date:
    # 1st of month: Salary
    if current.day == 1:
        records.append({
            "amount": 5500.00,
            "transaction_type": "income",
            "category": "Salary",
            "merchant": "Northstar Labs",
            "description": f"Monthly salary deposit - {current.strftime('%B %Y')}",
            "transaction_date": current.isoformat(),
        })
        # 1st of month: Rent / Housing
        records.append({
            "amount": 1650.00,
            "transaction_type": "expense",
            "category": "Housing",
            "merchant": "City View Apartments",
            "description": "Monthly apartment rent",
            "transaction_date": current.isoformat(),
        })

    # 15th of month: Freelance / Bonus occasionally
    if current.day == 15 and current.month in [6, 8, 10]:
        records.append({
            "amount": round(random.uniform(400, 850), 2),
            "transaction_type": "income",
            "category": "Freelance",
            "merchant": "TechConsult LLC",
            "description": "Freelance advisory payout",
            "transaction_date": current.isoformat(),
        })

    # 5th of month: Utilities & Internet
    if current.day == 5:
        records.append({
            "amount": round(random.uniform(85, 135), 2),
            "transaction_type": "expense",
            "category": "Bills",
            "merchant": "Metro Power & Light",
            "description": "Electric and gas utility bill",
            "transaction_date": current.isoformat(),
        })
        records.append({
            "amount": 75.00,
            "transaction_type": "expense",
            "category": "Bills",
            "merchant": "FiberNet Communications",
            "description": "Gigabit fiber internet service",
            "transaction_date": current.isoformat(),
        })

    # 8th of month: Subscriptions
    if current.day == 8:
        records.append({
            "amount": 19.99,
            "transaction_type": "expense",
            "category": "Subscriptions",
            "merchant": "StreamBox",
            "description": "Monthly video streaming package",
            "transaction_date": current.isoformat(),
        })
        records.append({
            "amount": 11.99,
            "transaction_type": "expense",
            "category": "Subscriptions",
            "merchant": "Spotify Music",
            "description": "Premium audio subscription",
            "transaction_date": current.isoformat(),
        })
        records.append({
            "amount": 49.00,
            "transaction_type": "expense",
            "category": "Subscriptions",
            "merchant": "Peak Fitness Gym",
            "description": "Monthly gym membership",
            "transaction_date": current.isoformat(),
        })

    # Regular daily spending (1-3 expenses per day on average)
    num_daily = random.choices([0, 1, 2, 3], weights=[0.1, 0.4, 0.35, 0.15])[0]
    for _ in range(num_daily):
        choice = random.random()
        if choice < 0.40:
            # Food & Groceries
            merch, desc, min_a, max_a = random.choice([
                ("Fresh Market", "Weekly fresh produce and groceries", 45, 120),
                ("Trader Joe's", "Grocery run & snacks", 30, 95),
                ("Corner Kitchen Deli", "Lunch sandwich & drink", 14, 25),
                ("Whole Foods", "Organic groceries & staples", 60, 140),
                ("Artisan Cafe", "Morning espresso and pastry", 6.5, 15),
            ])
            records.append({
                "amount": round(random.uniform(min_a, max_a), 2),
                "transaction_type": "expense",
                "category": "Food",
                "merchant": merch,
                "description": desc,
                "transaction_date": current.isoformat(),
            })
        elif choice < 0.65:
            # Transport
            merch, desc, min_a, max_a = random.choice([
                ("Metro Transit", "Subway card reload", 20, 45),
                ("Shell Oil", "Vehicle gas refuel", 35, 65),
                ("Uber", "Rideshare trip", 16, 38),
                ("Chevron", "Fuel refill", 32, 58),
            ])
            records.append({
                "amount": round(random.uniform(min_a, max_a), 2),
                "transaction_type": "expense",
                "category": "Transport",
                "merchant": merch,
                "description": desc,
                "transaction_date": current.isoformat(),
            })
        elif choice < 0.85:
            # Shopping
            merch, desc, min_a, max_a = random.choice([
                ("Amazon", "Home essentials and books", 22, 110),
                ("Target", "Household items and toiletries", 28, 90),
                ("Nike Store", "Running apparel", 55, 140),
                ("IKEA Home", "Kitchen supplies & organizers", 35, 150),
            ])
            records.append({
                "amount": round(random.uniform(min_a, max_a), 2),
                "transaction_type": "expense",
                "category": "Shopping",
                "merchant": merch,
                "description": desc,
                "transaction_date": current.isoformat(),
            })
        else:
            # Entertainment
            merch, desc, min_a, max_a = random.choice([
                ("Cinema City", "Movie tickets and concessions", 22, 45),
                ("Steam Games", "Video game digital purchase", 15, 60),
                ("Acoustic Lounge", "Concert tickets", 40, 95),
                ("Books & Brews", "Weekend book and tea", 18, 35),
            ])
            records.append({
                "amount": round(random.uniform(min_a, max_a), 2),
                "transaction_type": "expense",
                "category": "Entertainment",
                "merchant": merch,
                "description": desc,
                "transaction_date": current.isoformat(),
            })

    current += timedelta(days=1)

# Specific clearly unusual large anomalous transactions (for Stage 6 anomaly detection)
unusual_txs = [
    {
        "amount": 3450.00,
        "transaction_type": "expense",
        "category": "Shopping",
        "merchant": "Apex Ultra Electronics",
        "description": "Unusually large luxury 8K monitor & workstation purchase",
        "transaction_date": "2026-06-18",
    },
    {
        "amount": 2850.00,
        "transaction_type": "expense",
        "category": "Bills",
        "merchant": "Metro Emergency Dental",
        "description": "Unusually large emergency surgical procedure",
        "transaction_date": "2026-07-24",
    },
    {
        "amount": 1980.00,
        "transaction_type": "expense",
        "category": "Entertainment",
        "merchant": "Grand Royale Resort Casino",
        "description": "Unusually large VIP resort booking and casino charge",
        "transaction_date": "2026-08-20",
    },
    {
        "amount": 1750.00,
        "transaction_type": "expense",
        "category": "Shopping",
        "merchant": "Haute Couture Boutique",
        "description": "Unusual luxury designer purchase",
        "transaction_date": "2026-09-28",
    },
    {
        "amount": 4200.00,
        "transaction_type": "expense",
        "category": "Transport",
        "merchant": "Autobahn Transmission Specialists",
        "description": "Unusually large complete transmission rebuild repair",
        "transaction_date": "2026-10-14",
    },
]

records.extend(unusual_txs)

# Sort by date ascending
records.sort(key=lambda r: r["transaction_date"])

with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["amount", "transaction_type", "category", "merchant", "description", "transaction_date"],
    )
    writer.writeheader()
    writer.writerows(records)

print(f"Generated {len(records)} synthetic transactions to {OUT_PATH}")
