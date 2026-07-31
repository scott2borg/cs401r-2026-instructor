"""
NorthStar Retail — Synthetic Data Generator
CS 401R Lab 2 Starter Kit

Generates all five NorthStar datasets with realistic statistical properties.
Designed to support churn prediction, offer generation (RAG), and agentic AI labs.

Usage:
    python generate_northstar_data.py [--output-dir ./northstar-data] [--seed 42]

Output files:
    customers.csv           — 250,000 customer records
    transactions.parquet    — ~4.2M transaction records (18 months)
    clickstream.parquet     — ~8.1M clickstream events (90 days)
    store_events.csv        — ~14,400 store events (400 stores, 18 months)
    product_catalog.json    — 12,000 product SKUs

Requirements:
    pip install pandas numpy pyarrow faker tqdm
"""

import argparse
import hashlib
import json
import os
import random
import string
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable

# ── Configuration ──────────────────────────────────────────────────────────────

DEFAULT_SEED = 42
SNAPSHOT_DATE = datetime(2026, 8, 1)          # Represents the "today" of the dataset
HISTORY_START = datetime(2025, 2, 1)          # 18 months of transaction history
CLICKSTREAM_START = datetime(2026, 5, 3)      # 90 days of clickstream

N_CUSTOMERS = 250_000
N_STORES = 400
N_SKUS = 12_000
CHURN_RATE = 0.15                             # 15% of customers churned
AVG_TRANSACTIONS_PER_CUSTOMER = 16.8         # ~4.2M total / 250K customers

LOYALTY_TIERS = {
    "Bronze":   {"weight": 0.50, "spend_mult": 0.7,  "freq_mult": 0.7},
    "Silver":   {"weight": 0.30, "spend_mult": 1.0,  "freq_mult": 1.0},
    "Gold":     {"weight": 0.15, "spend_mult": 1.6,  "freq_mult": 1.5},
    "Platinum": {"weight": 0.05, "spend_mult": 2.8,  "freq_mult": 2.5},
}

PRODUCT_CATEGORIES = {
    "Apparel":           {"weight": 0.22, "price_range": (24.99, 299.99)},
    "Footwear":          {"weight": 0.14, "price_range": (49.99, 249.99)},
    "Camping & Hiking":  {"weight": 0.13, "price_range": (9.99, 599.99)},
    "Climbing":          {"weight": 0.07, "price_range": (14.99, 449.99)},
    "Water Sports":      {"weight": 0.06, "price_range": (29.99, 799.99)},
    "Cycling":           {"weight": 0.08, "price_range": (19.99, 1499.99)},
    "Winter Sports":     {"weight": 0.08, "price_range": (39.99, 699.99)},
    "Fitness":           {"weight": 0.07, "price_range": (14.99, 349.99)},
    "Travel":            {"weight": 0.05, "price_range": (24.99, 299.99)},
    "Electronics":       {"weight": 0.04, "price_range": (19.99, 499.99)},
    "Home & Garden":     {"weight": 0.04, "price_range": (9.99, 199.99)},
    "Pet Gear":          {"weight": 0.02, "price_range": (9.99, 149.99)},
}

US_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","ID","IL","IN","IA",
             "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH",
             "NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX",
             "UT","VT","VA","WA","WV","WI","WY"]

STATE_WEIGHTS = [0.01]*len(US_STATES)
for i, s in enumerate(US_STATES):
    if s in ["CA", "TX", "FL", "NY"]: STATE_WEIGHTS[i] = 0.06
    elif s in ["IL", "PA", "OH", "GA", "NC", "WA", "CO", "AZ"]: STATE_WEIGHTS[i] = 0.03
STATE_WEIGHTS = [w / sum(STATE_WEIGHTS) for w in STATE_WEIGHTS]

# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_email(email: str) -> str:
    return hashlib.sha256(email.encode()).hexdigest()[:32]

def random_date(start: datetime, end: datetime, rng: np.random.Generator) -> datetime:
    delta = (end - start).days
    return start + timedelta(days=int(rng.integers(0, delta)))

def fmt_date(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def progress(iterable, desc="", total=None):
    if TQDM_AVAILABLE:
        return tqdm(iterable, desc=desc, total=total)
    print(f"  Generating {desc}...")
    return iterable

# ── Generator Functions ───────────────────────────────────────────────────────

def generate_customers(rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    print("Generating customers.csv...")

    tiers = list(LOYALTY_TIERS.keys())
    tier_weights = [LOYALTY_TIERS[t]["weight"] for t in tiers]

    n = N_CUSTOMERS
    customer_ids = [f"CUST-{i+1:08d}" for i in range(n)]
    emails = [hash_email(fake.email()) for _ in progress(range(n), "emails", n)]

    signup_dates = [
        random_date(datetime(2015, 1, 1), SNAPSHOT_DATE - timedelta(days=90), rng)
        for _ in range(n)
    ]

    assigned_tiers = rng.choice(tiers, size=n, p=tier_weights)
    states = rng.choice(US_STATES, size=n, p=STATE_WEIGHTS)

    age_bands = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age_weights = [0.10, 0.22, 0.25, 0.20, 0.13, 0.10]
    assigned_ages = rng.choice(age_bands, size=n, p=age_weights)
    # ~8% null for pre-2019 signups
    pre_2019_mask = np.array([sd.year < 2019 for sd in signup_dates])
    null_age_mask = pre_2019_mask & (rng.random(n) < 0.80)
    assigned_ages = [None if null_age_mask[i] else assigned_ages[i] for i in range(n)]

    preferred_channels = rng.choice(["store", "online", "both"], size=n, p=[0.45, 0.25, 0.30])

    # Loyalty points correlated with tier and tenure
    tenure_days = np.array([(SNAPSHOT_DATE - sd).days for sd in signup_dates])
    base_points = {
        "Bronze": 500, "Silver": 3000, "Gold": 12000, "Platinum": 45000
    }
    loyalty_points = np.array([
        max(0, int(base_points[t] + rng.normal(0, base_points[t] * 0.3)))
        for t in assigned_tiers
    ])

    # Lifetime spend
    spend_mults = np.array([LOYALTY_TIERS[t]["spend_mult"] for t in assigned_tiers])
    lifetime_spend = np.round(
        tenure_days / 365 * 340 * spend_mults * rng.lognormal(0, 0.4, n), 2
    )

    # Churn labels — higher churn in lower tiers, shorter tenure
    churn_probs = np.where(
        assigned_tiers == np.array("Bronze"),
        0.22,
        np.where(assigned_tiers == np.array("Silver"), 0.12,
        np.where(assigned_tiers == np.array("Gold"), 0.06, 0.03))
    )
    # Faster churners have shorter tenure
    tenure_factor = np.clip(1 - tenure_days / 3650, 0, 1)
    churn_probs = np.clip(churn_probs * (1 + tenure_factor * 0.5), 0, 1)
    churn_labels = (rng.random(n) < churn_probs).astype(int)

    # Churn dates for churned customers
    churn_dates = []
    for i in range(n):
        if churn_labels[i] == 1:
            days_before = int(rng.integers(90, 365))
            churn_dates.append(fmt_date(SNAPSHOT_DATE - timedelta(days=days_before)))
        else:
            churn_dates.append(None)

    # Zip codes (simplified: 5 random digits)
    zips = [f"{rng.integers(10000, 99999):05d}" for _ in range(n)]
    # Inject ~0.3% invalid
    for i in rng.choice(n, size=int(n * 0.003), replace=False):
        zips[i] = "XXXXX"

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "email": emails,
        "signup_date": [fmt_date(sd) for sd in signup_dates],
        "loyalty_tier": assigned_tiers,
        "loyalty_points": loyalty_points,
        "preferred_channel": preferred_channels,
        "age_band": assigned_ages,
        "state": states,
        "zip_code": zips,
        "lifetime_spend": lifetime_spend,
        "churn_label": churn_labels,
        "churn_date": churn_dates,
        "snapshot_date": fmt_date(SNAPSHOT_DATE),
    })

    print(f"  ✓ {len(df):,} customers | churn rate: {df['churn_label'].mean():.1%}")
    return df


def generate_product_catalog(rng: np.random.Generator) -> list:
    print("Generating product_catalog.json...")

    categories = list(PRODUCT_CATEGORIES.keys())
    cat_weights = [PRODUCT_CATEGORIES[c]["weight"] for c in categories]

    brands = [
        "NorthStar Own Brand", "TrailPeak", "Summit Co.", "ArcLight", "PeakForm",
        "TerraStride", "RidgeLine", "WildRoots", "ClearPath", "VertexGear",
        "EcoTread", "IronClad", "PolarVault", "SunBlazer", "DriftCo.",
    ]

    adjectives = ["Pro", "Elite", "Ultra", "Lite", "Core", "Sport", "Trail", "Peak",
                  "Summit", "Ridge", "Alpine", "Venture", "Endurance", "Force", "Swift"]
    nouns = {
        "Apparel": ["Jacket", "Vest", "Pants", "Shorts", "Base Layer", "Fleece", "Hoodie", "Tee"],
        "Footwear": ["Boot", "Sandal", "Trail Runner", "Approach Shoe", "Sneaker", "Slipper"],
        "Camping & Hiking": ["Tent", "Sleeping Bag", "Backpack", "Trekking Pole", "Headlamp", "Filter"],
        "Climbing": ["Harness", "Helmet", "Belay Device", "Carabiner", "Rope", "Chalk Bag"],
        "Water Sports": ["Kayak Paddle", "PFD", "Drysuit", "Wetsuit", "Board", "Pump"],
        "Cycling": ["Helmet", "Gloves", "Jersey", "Shorts", "Saddle", "Light", "Lock"],
        "Winter Sports": ["Ski", "Boot", "Pole", "Goggles", "Gloves", "Helmet", "Layer"],
        "Fitness": ["Mat", "Resistance Band", "Kettlebell", "Foam Roller", "Rope", "Weights"],
        "Travel": ["Bag", "Organizer", "Lock", "Pillow", "Adapter", "Wallet", "Pouch"],
        "Electronics": ["GPS", "Watch", "Headlamp", "Speaker", "Camera", "Charger", "Sensor"],
        "Home & Garden": ["Hammock", "Chair", "Table", "Cooler", "Fire Starter", "Tool"],
        "Pet Gear": ["Harness", "Leash", "Pack", "Coat", "Bowl", "Toy"],
    }

    catalog = []
    for i in range(N_SKUS):
        cat = rng.choice(categories, p=cat_weights)
        cat_config = PRODUCT_CATEGORIES[cat]
        price_min, price_max = cat_config["price_range"]
        base_price = float(np.round(rng.uniform(price_min, price_max) * 2) / 2)

        on_sale = rng.random() < 0.18
        sale_price = float(np.round(base_price * rng.uniform(0.60, 0.85) * 2) / 2) if on_sale else None

        noun = rng.choice(nouns[cat])
        adj = rng.choice(adjectives)
        brand = rng.choice(brands)
        product_name = f"{adj} {noun}" if rng.random() > 0.3 else noun

        rating = round(float(np.clip(rng.normal(4.1, 0.6), 1.0, 5.0)), 1)
        review_count = int(np.clip(rng.lognormal(4.5, 1.5), 0, 15000))

        tags = rng.choice(
            ["outdoor", "waterproof", "lightweight", "durable", "eco-friendly",
             "technical", "casual", "unisex", "men", "women", "kids", "sale"],
            size=rng.integers(2, 6), replace=False
        ).tolist()
        if on_sale:
            tags.append("sale")

        related = [f"SKU-{rng.integers(1, N_SKUS):06d}" for _ in range(rng.integers(0, 5))]

        catalog.append({
            "sku_id": f"SKU-{i+1:06d}",
            "product_name": product_name,
            "category": cat,
            "subcategory": noun,
            "brand": brand,
            "price": base_price,
            "sale_price": sale_price,
            "in_stock": bool(rng.random() < 0.88),
            "rating": rating,
            "review_count": review_count,
            "description": f"{brand} {product_name}. Designed for {cat.lower()} enthusiasts. "
                           f"Features include {', '.join(tags[:3])} construction.",
            "tags": tags,
            "related_skus": related,
            "last_updated": fmt_date(SNAPSHOT_DATE - timedelta(days=int(rng.integers(0, 30)))),
        })

    print(f"  ✓ {len(catalog):,} SKUs across {len(categories)} categories")
    return catalog


def generate_store_events(rng: np.random.Generator) -> pd.DataFrame:
    print("Generating store_events.csv...")
    fake = Faker()
    Faker.seed(rng.integers(10000))

    event_types = ["promotion", "holiday_closure", "remodel", "clearance_sale",
                   "inventory_event", "seasonal_reset", "grand_opening"]
    event_weights = [0.35, 0.20, 0.08, 0.15, 0.12, 0.07, 0.03]

    stores = [f"STORE-{i+1:03d}" for i in range(N_STORES)]
    store_cities = [fake.city() for _ in range(N_STORES)]
    store_states = rng.choice(US_STATES, size=N_STORES, p=STATE_WEIGHTS)

    records = []
    for store_idx in range(N_STORES):
        n_events = int(rng.integers(20, 55))
        for _ in range(n_events):
            event_date = random_date(HISTORY_START, SNAPSHOT_DATE, rng)
            event_type = rng.choice(event_types, p=event_weights)

            multi_day = event_type in ["remodel", "clearance_sale", "grand_opening"]
            end_date = event_date + timedelta(days=int(rng.integers(2, 14))) if multi_day else None

            has_desc = rng.random() > 0.15
            has_impact = rng.random() > 0.40

            records.append({
                "store_id": stores[store_idx] + (" " if rng.random() < 0.08 else ""),  # ~8% trailing space
                "store_name": f"NorthStar {store_cities[store_idx]}",
                "city": store_cities[store_idx],
                "state": store_states[store_idx],
                "event_date": fmt_date(event_date),
                "event_end_date": fmt_date(end_date) if end_date else None,
                "event_type": event_type,
                "event_description": fake.sentence(nb_words=8) if has_desc else None,
                "revenue_impact_estimate": float(np.round(rng.normal(0, 15000), 2)) if has_impact else None,
            })

    # Inject ~2% with MM/DD/YYYY format (data quality issue documented in schema)
    df = pd.DataFrame(records)
    bad_date_idx = rng.choice(len(df), size=int(len(df) * 0.02), replace=False)
    for i in bad_date_idx:
        d = datetime.strptime(df.at[i, "event_date"], "%Y-%m-%d")
        df.at[i, "event_date"] = d.strftime("%m/%d/%Y")

    print(f"  ✓ {len(df):,} store events across {N_STORES} stores")
    return df


def generate_transactions(customers_df: pd.DataFrame,
                          catalog: list,
                          rng: np.random.Generator) -> pd.DataFrame:
    print("Generating transactions.parquet (this takes ~60-90 seconds)...")

    customer_ids = customers_df["customer_id"].tolist()
    tiers = customers_df["loyalty_tier"].tolist()
    churn_dates = customers_df["churn_date"].tolist()
    channels = customers_df["preferred_channel"].tolist()

    skus = [p["sku_id"] for p in catalog]
    sku_categories = {p["sku_id"]: p["category"] for p in catalog}

    payment_methods = ["credit_card", "debit_card", "loyalty_points", "gift_card", "cash"]
    pay_weights = [0.52, 0.25, 0.10, 0.08, 0.05]

    promo_codes = [f"PROMO{rng.integers(100,999)}" for _ in range(50)]
    stores = [f"STORE-{i+1:03d}" for i in range(N_STORES)]

    all_txns = []
    txn_counter = 0

    for idx in progress(range(len(customer_ids)), "transactions", len(customer_ids)):
        cid = customer_ids[idx]
        tier = tiers[idx]
        channel_pref = channels[idx]
        churn_date_str = churn_dates[idx]

        # Determine transaction end date
        if churn_date_str:
            txn_end = datetime.strptime(churn_date_str, "%Y-%m-%d")
        else:
            txn_end = SNAPSHOT_DATE

        if txn_end <= HISTORY_START:
            continue

        # Number of transactions (Poisson-distributed, tier-adjusted)
        freq_mult = LOYALTY_TIERS[tier]["freq_mult"]
        spend_mult = LOYALTY_TIERS[tier]["spend_mult"]
        n_txns = max(0, int(rng.poisson(AVG_TRANSACTIONS_PER_CUSTOMER * freq_mult *
                                         ((txn_end - HISTORY_START).days / 548))))

        for _ in range(n_txns):
            txn_date = random_date(HISTORY_START, txn_end, rng)

            # Channel based on preference
            if channel_pref == "store":
                channel = "store" if rng.random() < 0.82 else "online"
            elif channel_pref == "online":
                channel = "online" if rng.random() < 0.76 else "store"
            else:
                channel = rng.choice(["store", "online"], p=[0.52, 0.48])

            store_id = rng.choice(stores) if channel == "store" else "ONLINE"

            # Amount (lognormal, tier-adjusted, seasonal boost in Nov-Dec)
            seasonal_mult = 1.35 if txn_date.month in [11, 12] else 1.0
            amount = float(np.round(
                rng.lognormal(np.log(68 * spend_mult * seasonal_mult), 0.65), 2
            ))
            amount = max(9.99, amount)

            # Promotion
            has_promo = rng.random() < 0.22
            promo_code = rng.choice(promo_codes) if has_promo else None
            discount = float(np.round(amount * rng.uniform(0.05, 0.30), 2)) if has_promo else None

            # Items
            num_items = int(np.clip(rng.integers(1, 7), 1, 6))
            num_units = int(num_items + rng.integers(0, 3))

            # Categories
            n_cats = min(num_items, rng.integers(1, 4))
            txn_skus = rng.choice(skus, size=n_cats, replace=False)
            cats = "|".join(sorted(set(sku_categories[s] for s in txn_skus)))

            # Payment
            payment = rng.choice(payment_methods, p=pay_weights)
            if channel == "store" and payment == "loyalty_points":
                payment = "credit_card"  # Loyalty points not redeemable in-store

            is_return = rng.random() < 0.04  # 4% return rate

            txn_counter += 1
            txn_id_prefix = "TXN-"
            chars = string.ascii_uppercase + string.digits
            txn_suffix = "".join(rng.choice(list(chars), size=12))

            all_txns.append({
                "transaction_id": f"{txn_id_prefix}{txn_suffix}",
                "customer_id": cid,
                "store_id": store_id,
                "transaction_date": txn_date.isoformat(),
                "transaction_amount": amount,
                "net_amount": float(np.round(amount - (discount or 0), 2)),
                "num_items": num_items,
                "num_units": num_units,
                "payment_method": payment,
                "promotion_code": promo_code,
                "promotion_discount": discount,
                "channel": channel,
                "device_type": rng.choice(["mobile", "desktop", "tablet"], p=[0.55, 0.35, 0.10])
                               if channel == "online" else None,
                "return_flag": is_return,
                "product_categories": cats,
            })

    df = pd.DataFrame(all_txns)
    # Inject ~2% with unknown customer_id (guest checkouts)
    n_guest = int(len(df) * 0.02)
    guest_ids = [f"GUEST-{rng.integers(100000, 999999)}" for _ in range(n_guest)]
    guest_idx = rng.choice(len(df), size=n_guest, replace=False)
    for i, idx in enumerate(guest_idx):
        df.at[idx, "customer_id"] = guest_ids[i]

    print(f"  ✓ {len(df):,} transactions")
    return df


def generate_clickstream(customers_df: pd.DataFrame,
                         catalog: list,
                         rng: np.random.Generator) -> pd.DataFrame:
    print("Generating clickstream.parquet (this takes ~60-90 seconds)...")

    active_customers = customers_df[customers_df["churn_label"] == 0]["customer_id"].tolist()
    # ~35% of events are anonymous
    n_active = len(active_customers)

    skus = [p["sku_id"] for p in catalog]
    pages = ["home", "category", "product", "search", "cart", "checkout",
             "account", "wishlist", "loyalty", "help", "sale", "new-arrivals"]
    event_types = ["page_view", "product_view", "search", "add_to_cart",
                   "remove_from_cart", "checkout_start", "checkout_complete",
                   "checkout_abandon", "login", "logout"]
    event_weights = [0.30, 0.25, 0.15, 0.10, 0.03, 0.05, 0.04, 0.04, 0.02, 0.02]
    referrals = ["organic", "email", "paid_search", "social", "direct", "affiliate"]
    ref_weights = [0.28, 0.22, 0.18, 0.14, 0.12, 0.06]
    devices = ["mobile", "desktop", "tablet"]
    dev_weights = [0.58, 0.34, 0.08]

    records = []
    # Generate ~8.1M events: ~32 events/day × 90 days × ~2800 active customers/day
    n_sessions = 320_000  # Sessions (avg ~25 events per session)

    for _ in progress(range(n_sessions), "clickstream sessions", n_sessions):
        is_anonymous = rng.random() < 0.35
        customer_id = None if is_anonymous else rng.choice(active_customers)

        session_id = "".join(
            rng.choice(list(string.hexdigits[:16]), size=36).tolist()
        ).replace("0123456789abcdef", "")  # pseudo-UUID
        # Simpler approach:
        session_id = f"{rng.integers(10**15, 10**16):016x}-{rng.integers(10**3, 10**4):04x}"

        session_start = CLICKSTREAM_START + timedelta(
            days=float(rng.random() * (SNAPSHOT_DATE - CLICKSTREAM_START).days),
            hours=float(rng.random() * 24),
            minutes=float(rng.random() * 60),
        )
        device = rng.choice(devices, p=dev_weights)
        referral = rng.choice(referrals, p=ref_weights)

        n_events = int(np.clip(rng.integers(3, 60), 3, 59))

        for j in range(n_events):
            ts = session_start + timedelta(seconds=int(rng.integers(0, 1800)))
            event_type = rng.choice(event_types, p=event_weights)

            is_product_event = event_type in ["product_view", "add_to_cart", "remove_from_cart"]
            is_search = event_type == "search"
            is_entry = j == 0

            product_id = rng.choice(skus) if is_product_event else None
            # ~0.5% of searches have PII (data quality issue)
            search_query = None
            if is_search:
                if rng.random() < 0.005:
                    search_query = Faker().email()  # PII injection (must be masked)
                else:
                    search_query = rng.choice([
                        "waterproof jacket", "trail running shoes", "sleeping bag",
                        "kids backpack", "cycling helmet", "yoga mat", "camping tent",
                        "sale items", "gift ideas", "new arrivals",
                    ])

            cart_value = float(np.round(rng.uniform(29.99, 399.99), 2)) \
                if event_type in ["add_to_cart", "checkout_start", "checkout_complete"] else None

            records.append({
                "event_id": f"EVT-{rng.integers(10**12, 10**13):013d}",
                "customer_id": customer_id,
                "session_id": session_id,
                "event_timestamp": ts.isoformat(),
                "event_type": event_type,
                "page_name": rng.choice(pages) if not is_product_event else None,
                "product_id": product_id,
                "search_query": search_query,
                "device_type": device,
                "referral_source": referral if is_entry else None,
                "cart_value": cart_value,
            })

    df = pd.DataFrame(records)
    print(f"  ✓ {len(df):,} clickstream events")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate NorthStar Retail synthetic datasets")
    parser.add_argument("--output-dir", default="./northstar-data", help="Output directory")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--small", action="store_true",
                        help="Generate small sample (1%% of normal size — for testing)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    fake = Faker()
    Faker.seed(args.seed)
    random.seed(args.seed)

    if args.small:
        global N_CUSTOMERS, N_SKUS
        N_CUSTOMERS = 2_500
        N_SKUS = 120
        print("⚠️  Small mode: generating 1% of normal dataset size for testing.\n")

    print(f"\n🏪 NorthStar Retail Data Generator")
    print(f"   Seed: {args.seed} | Output: {args.output_dir}\n")
    print("─" * 50)

    # 1. Customers
    customers_df = generate_customers(rng, fake)
    customers_df.to_csv(os.path.join(args.output_dir, "customers.csv"), index=False)
    print(f"   → Saved customers.csv ({os.path.getsize(os.path.join(args.output_dir, 'customers.csv')) / 1e6:.1f} MB)\n")

    # 2. Product catalog
    catalog = generate_product_catalog(rng)
    with open(os.path.join(args.output_dir, "product_catalog.json"), "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"   → Saved product_catalog.json\n")

    # 3. Store events
    store_events_df = generate_store_events(rng)
    store_events_df.to_csv(os.path.join(args.output_dir, "store_events.csv"), index=False)
    print(f"   → Saved store_events.csv\n")

    # 4. Transactions (memory-intensive — written in chunks if large)
    txn_df = generate_transactions(customers_df, catalog, rng)
    txn_df.to_parquet(os.path.join(args.output_dir, "transactions.parquet"),
                      engine="pyarrow", compression="snappy", index=False)
    print(f"   → Saved transactions.parquet ({os.path.getsize(os.path.join(args.output_dir, 'transactions.parquet')) / 1e6:.1f} MB)\n")

    # 5. Clickstream
    click_df = generate_clickstream(customers_df, catalog, rng)
    click_df.to_parquet(os.path.join(args.output_dir, "clickstream.parquet"),
                        engine="pyarrow", compression="snappy", index=False)
    print(f"   → Saved clickstream.parquet ({os.path.getsize(os.path.join(args.output_dir, 'clickstream.parquet')) / 1e6:.1f} MB)\n")

    print("─" * 50)
    print("✅ All datasets generated successfully.")
    print(f"\nDataset summary:")
    print(f"  customers:      {len(customers_df):>10,} rows")
    print(f"  transactions:   {len(txn_df):>10,} rows")
    print(f"  clickstream:    {len(click_df):>10,} rows")
    print(f"  store_events:   {len(store_events_df):>10,} rows")
    print(f"  product_catalog:{len(catalog):>10,} items")
    print(f"\nNext step: Run the Glue job skeleton to ingest into S3.")
    print(f"  cp -r {args.output_dir}/* s3://YOUR-BUCKET/raw/")


if __name__ == "__main__":
    main()
