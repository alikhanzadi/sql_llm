import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime, timedelta

np.random.seed(42)


# ------------------------
# CONFIG
# ------------------------
NUM_USERS = 2000
NUM_ISSUERS = 200
NUM_TOKENS = 150
NUM_TRANSACTIONS = 50000

START_DATE = datetime(2025, 1, 1)

PRICE_INCREMENT = 0.000023
MAX_PRICE = 24.0

def generate_uuid():
    return str(uuid.uuid4())

def random_timestamp():
    return START_DATE + timedelta(days=random.randint(0, 365))

# ------------------------
# USERS
# ------------------------
users = []

for _ in range(NUM_USERS):
    user_id = generate_uuid()
    users.append({
        "user_id": user_id,
        "user_role": random.choice(["FAN", "ISSUER", "BOTH"]),
        "display_name": f"user_{random.randint(1000,9999)}",
        "username": f"user_{random.randint(10000,99999)}",
        "referral_id": None,
        "email": f"user{random.randint(10000,99999)}@test.com",
        "email_verified": random.choice([True, False]),
        "email_verification_status": random.choice(["PENDING","VERIFIED"]),
        "email_verification_score": round(random.uniform(50,100),2),
        "country": random.choice(["US","CA","UK"]),
        "zip_code": str(random.randint(10000,99999)),
        "gender": random.choice(["Male","Female","Other"]),
        "time_zone": "UTC",
        "login_methods_allowed": ["EMAIL_PASSWORD"],
        "password_hash": "hash",
        "passkey_public_key": None,
        "primary_social_platform": None,
        "primary_social_handle": None,
        "mfa_enabled": False,
        "account_status": "ACTIVE",
        "created_at": random_timestamp(),
        "updated_at": None,
        "last_login_at": None,
        "created_ip": "127.0.0.1",
        "created_user_agent": "generator",
        "metadata": None
    })
users_df = pd.DataFrame(users)


# ------------------------
# ISSUERS
# ------------------------
issuer_users = users_df.sample(NUM_ISSUERS)
issuers = []

for _, row in issuer_users.iterrows():
    issuer_id = generate_uuid()
    issuers.append({
        "issuer_id": issuer_id,
        "user_id": row["user_id"],
        "issuer_type": random.choice(["ATHLETE","CREATOR"]),
        "email": row["email"],
        "username": row["username"],
        "status": random.choice(["ACTIVE","PENDING"]),
        "level": random.choice(["YOUTH","COLLEGE","PRO"]),
        "country": row["country"],
        "region": "NA",
        "created_at": row["created_at"],
        "updated_at": None,
        "metadata": None
    })
issuers_df = pd.DataFrame(issuers)

# ------------------------
# ATHLETE PROFILE
# ------------------------
athletes = []
for _, row in issuers_df.iterrows():
    if row["issuer_type"] == "ATHLETE":
        athletes.append({
            "issuer_id": row["issuer_id"],
            "user_id": row["user_id"],
            "sport": random.choice(["Basketball","Soccer","Football"]),
            "team": f"Team_{random.randint(1,20)}",
            "league": "Youth",
            "position_primary": "Forward",
            "position_secondary": None,
            "multi_sport": False,
            "biography": "bio",
            "profile_completion": random.randint(50,100),
            "created_at": random_timestamp(),
            "updated_at": None,
            "metadata": None
        })
athlete_df = pd.DataFrame(athletes)

# ------------------------
# CREATOR PROFILE (EMPTY)
# ------------------------
creator_df = pd.DataFrame(columns=[
    "issuer_id","user_id","creator_category","content_mediums",
    "niche","biography","profile_completion","created_at","updated_at","metadata"
])

# ------------------------
# IDENTITY VERIFICATION
# ------------------------
identity = []
verified_issuers = []

for _, row in issuers_df.iterrows():
    status = random.choice(["PENDING","PASSED","FAILED"])
    if status == "PASSED":
        verified_issuers.append(row["issuer_id"])

    identity.append({
        "identity_check_id": generate_uuid(),
        "issuer_id": row["issuer_id"],
        "provider": "Persona",
        "status": status,
        "level": "basic",
        "alias_confidence": round(random.uniform(70,100),2),
        "opted_in": True,
        "initiated_at": random_timestamp(),
        "completed_at": random_timestamp(),
        "failure_reason": None,
        "raw_response": None
    })

identity_df = pd.DataFrame(identity)

# ------------------------
# SOCIAL VERIFICATION
# ------------------------
social = []

platforms = ["YOUTUBE","INSTAGRAM","X"]

for _, row in issuers_df.iterrows():
    for p in random.sample(platforms, k=2):
        social.append({
            "social_verif_id": generate_uuid(),
            "issuer_id": row["issuer_id"],
            "platform": p,
            "handle": f"{p.lower()}_{random.randint(1000,9999)}",
            "followers_count": random.randint(1000,1000000),
            "verified": random.choice([True,False]),
            "initiated_at": random_timestamp(),
            "completed_at": random_timestamp(),
            "attempts": random.randint(1,3),
            "status": random.choice(["SUCCESS","FAILED"]),
            "metadata": None
        })

social_df = pd.DataFrame(social)

# ------------------------
# SOCIAL AUTH FAIL
# ------------------------
fails = []

for _, row in issuers_df.sample(frac=0.3).iterrows():
    fails.append({
        "auth_fail_id": generate_uuid(),
        "issuer_id": row["issuer_id"],
        "platform": random.choice(platforms),
        "failed_at": random_timestamp(),
        "reason_code": "OAUTH_ERROR",
        "reason_detail": "error",
        "metadata": None
    })

social_fails_df = pd.DataFrame(fails)

# ------------------------
# TOKENS  (ONLY VERIFIED ISSUERS)
# ------------------------
tokens = []

eligible_issuers = issuers_df[issuers_df["issuer_id"].isin(verified_issuers)]

for _, row in eligible_issuers.sample(min(NUM_TOKENS, len(eligible_issuers))).iterrows():
    tokens.append({
        "token_id": len(tokens) + 1,
        "issuer_id": row["issuer_id"],
        "token_symbol": f"TOKEN_{random.randint(1000,9999)}",
        "initial_supply": random.randint(100000,1000000),
        "current_supply_minted": 0,
        "bonding_curve_start_price": 1.000000,
        "bonding_curve_end_price": 24.000000,
        "mint_timestamp": random_timestamp(),
        "paused_sales": False,
        "secondary_trading_enabled": False,
        "total_revenue_raised": 0,
        "created_at": random_timestamp(),
        "updated_at": random_timestamp()
    })

tokens_df = pd.DataFrame(tokens)

# ------------------------
# TRANSACTIONS (PRIMARY ONLY)
# ------------------------
transactions = []
token_prices = {tid: 1.0 for tid in tokens_df["token_id"]}

user_ids = users_df["user_id"].tolist()
token_ids = tokens_df["token_id"].tolist()

for i in range(NUM_TRANSACTIONS):
    token_id = random.choice(token_ids)

    current_price = token_prices[token_id]
    new_price = min(MAX_PRICE, current_price + PRICE_INCREMENT)

    token_prices[token_id] = new_price

    quantity = random.randint(1, 20)

    transactions.append({
        "transaction_id": i + 1,
        "token_id": token_id,
        "buyer_id": random.choice(user_ids),
        "seller_id": None,
        "quantity": quantity,
        "price_per_token": format(new_price, ".6f"),
        "total_amount_usdc": format(quantity * new_price, ".6f"),
        "transaction_type": "primary",
        "status": "completed",
        "timestamp": random_timestamp()
    })

transactions_df = pd.DataFrame(transactions)

# ------------------------
# PAYMENTS
# ------------------------
payments = []

for i in range(5000):
    tx = transactions_df.sample(1).iloc[0]

    payments.append({
        "payment_id": i + 1,
        "recipient_id": tx["buyer_id"],
        "linked_transaction_id": tx["transaction_id"],
        "amount_usdc": tx["total_amount_usdc"],
        "installment_number": None,
        "due_date": datetime.now().date(),
        "status": random.choice(["paid","pending"]),
        "payout_tx_reference": None,
        "timestamp": random_timestamp()
    })

payments_df = pd.DataFrame(payments)

# ------------------------
# SAVE 
# ------------------------
users_df.to_csv("./users.csv", index=False)
issuers_df.to_csv("./issuers.csv", index=False)
athlete_df.to_csv("./athlete_profile.csv", index=False)
creator_df.to_csv("./creator_profile.csv", index=False)
identity_df.to_csv("./identity_verification.csv", index=False)
social_df.to_csv("./social_verification.csv", index=False)
social_fails_df.to_csv("./social_fails.csv", index=False)
tokens_df.to_csv("./tokens.csv", index=False)
transactions_df.to_csv("./transactions.csv", index=False)
payments_df.to_csv("./payments.csv", index=False)

print("Updated data generated")