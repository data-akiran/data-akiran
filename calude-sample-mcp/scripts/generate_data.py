"""
Generates a synthetic dataset of user accounts across several phone/tech
brands (Samsung, Apple, Google, OnePlus, Xiaomi) for the sample MCP server
to query. Re-run this script any time to regenerate data/accounts.json.
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

BRANDS = {
    "Samsung": 0.34,
    "Apple": 0.28,
    "Google": 0.14,
    "Xiaomi": 0.14,
    "OnePlus": 0.10,
}

COUNTRIES = ["US", "IN", "UK", "DE", "BR", "KR", "JP", "FR", "CA", "AU"]
PLANS = {"free": 0.55, "premium": 0.32, "business": 0.13}
STATUSES = {"active": 0.78, "inactive": 0.15, "suspended": 0.07}

FIRST_NAMES = [
    "Aditya", "Priya", "Wei", "Maria", "John", "Sara", "Liam", "Noah",
    "Emma", "Olivia", "Yuki", "Hana", "Carlos", "Sofia", "Ahmed", "Fatima",
    "Ivan", "Elena", "Ravi", "Anjali", "Tom", "Grace", "Ken", "Mei",
]
LAST_NAMES = [
    "Kumar", "Smith", "Chen", "Silva", "Johnson", "Khan", "Muller", "Kim",
    "Tanaka", "Rossi", "Garcia", "Nguyen", "Patel", "Brown", "Lee", "Diaz",
]


def weighted_choice(weights: dict):
    return random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def random_date(start: date, end: date) -> str:
    delta_days = (end - start).days
    return (start + timedelta(days=random.randint(0, delta_days))).isoformat()


def make_account(idx: int) -> dict:
    brand = weighted_choice(BRANDS)
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    domain = {
        "Samsung": "samsung.com",
        "Apple": "icloud.com",
        "Google": "gmail.com",
        "Xiaomi": "mi.com",
        "OnePlus": "oneplus.com",
    }[brand]
    return {
        "id": f"acct_{idx:05d}",
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}{idx}@{domain}",
        "brand": brand,
        "country": random.choice(COUNTRIES),
        "plan": weighted_choice(PLANS),
        "status": weighted_choice(STATUSES),
        "created_at": random_date(date(2019, 1, 1), date(2026, 9, 1)),
    }


def main():
    n = 1200
    accounts = [make_account(i) for i in range(1, n + 1)]
    out_path = Path(__file__).resolve().parent.parent / "data" / "accounts.json"
    out_path.write_text(json.dumps(accounts, indent=2))
    print(f"Wrote {len(accounts)} accounts to {out_path}")


if __name__ == "__main__":
    main()
