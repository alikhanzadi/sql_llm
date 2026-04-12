import os
import csv
import psycopg2
from psycopg2 import sql
from io import StringIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime, timedelta

np.random.seed(42)

conn_string = os.getenv("DATABASE_URL")

print(os.getcwd())

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

conn_string = os.getenv("DATABASE_URL")

def truncate_table(conn_string, table_name, cascade=False):
    """Forcefully clears the table and resets identities."""
    suffix = " CASCADE" if cascade else ""
    query = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY" + suffix).format(
        sql.Identifier(table_name)
    )
    
    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
        conn.commit()
    print(f"Table {table_name!r} truncated successfully.")

def copy_data(conn_string, df, table_name):
    buf = StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)
    
    # Identify the columns from the DataFrame
    columns = [sql.Identifier(col) for col in df.columns]
    
    # Format: COPY table_name (col1, col2, ...) FROM STDIN ...
    copy_sql = sql.SQL(
        "COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    ).format(
        sql.Identifier(table_name),
        sql.SQL(', ').join(columns)
    )
    
    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.copy_expert(copy_sql, buf)
        conn.commit()
    print(f"Loaded {len(df)} rows into {table_name!r}")


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
        "username": f"user_{1000 + _}",
        "referral_id": None,
        "email": f"user{10000 + _}@test.com",
        "email_verified": random.choice([True, False]),
        "email_verification_status": random.choice(["PENDING","VERIFIED"]),
        "email_verification_score": round(random.uniform(50,100),2),
        "country": random.choice(["US","CA","UK"]),
        "zip_code": str(random.randint(10000,99999)),
        "gender": random.choice(["Male","Female","Other"]),
        "time_zone": "UTC",
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
users_df.to_csv("./tables/users.csv", index=False)


# ------------------------
# ISSUERS + VERIFICATION LOGIC
# ------------------------
issuers = []
identity = []
social = []

platforms = ["YOUTUBE", "INSTAGRAM", "X"]

issuer_users = users_df.sample(NUM_ISSUERS).reset_index(drop=True)

PASSED_BOTH = 150

# split remaining 50
remaining = NUM_ISSUERS - PASSED_BOTH

id_only_pass = 30
social_only_pass = 20
none_pass = remaining - id_only_pass - social_only_pass  # 10

for i, row in issuer_users.iterrows():
    issuer_id = generate_uuid()

    # ---------------- STATUS ASSIGNMENT ----------------
    if i < PASSED_BOTH:
        id_status = "PASSED"
        social_status = "PASSED"

    elif i < PASSED_BOTH + id_only_pass:
        id_status = "PASSED"
        social_status = random.choice(["FAILED", "PENDING"])

    elif i < PASSED_BOTH + id_only_pass + social_only_pass:
        id_status = random.choice(["FAILED", "PENDING"])
        social_status = "PASSED"

    else:
        id_status = random.choice(["FAILED", "PENDING"])
        social_status = random.choice(["FAILED", "PENDING"])

    # issuer status derived
    issuer_status = "PASSED" if (id_status == "PASSED" and social_status == "PASSED") else (
        "PENDING" if "PENDING" in [id_status, social_status] else "FAILED"
    )

    # ---------------- ISSUER ----------------
    issuers.append({
        "issuer_id": issuer_id,
        "user_id": row["user_id"],
        "issuer_type": random.choice(["ATHLETE", "CREATOR"]),
        "email": row["email"],
        "username": row["username"],
        "status": issuer_status,
        "level": random.choice(["YOUTH","COLLEGE","PRO"]),
        "country": row["country"],
        "region": "NA",
        "created_at": row["created_at"],
        "updated_at": None,
        "metadata": None
    })

    # ---------------- IDENTITY ----------------
    identity.append({
        "identity_check_id": generate_uuid(),
        "issuer_id": issuer_id,
        "provider": "Persona",
        "status": id_status,
        "level": "basic",
        "alias_confidence": round(random.uniform(70,100),2),
        "opted_in": True,
        "initiated_at": random_timestamp(),
        "completed_at": random_timestamp(),
        "failure_reason": None if id_status == "PASSED" else "check_failed",
        "raw_response": None
    })

    # ---------------- SOCIAL ----------------
    for p in random.sample(platforms, k=1):
        social.append({
            "social_verif_id": generate_uuid(),
            "issuer_id": issuer_id,
            "platform": p,
            "handle": f"{p.lower()}_{random.randint(1000,9999)}",
            "followers_count": random.randint(1000,1000000),
            "verified": True if social_status == "PASSED" else False,
            "initiated_at": random_timestamp(),
            "completed_at": random_timestamp(),
            "attempts": random.randint(1,3),
            "status": social_status,
            "metadata": None
        })

issuers_df = pd.DataFrame(issuers)
identity_df = pd.DataFrame(identity)
social_df = pd.DataFrame(social)

issuers_df.to_csv("./tables/issuers.csv", index=False)
identity_df.to_csv("./tables/identity_verification.csv", index=False)
social_df.to_csv("./tables/social_verification.csv", index=False)


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

athlete_df.to_csv("./tables/athletes.csv", index=False)


# ------------------------
# POST SIGNUP 
# ------------------------
post_signup = []

for _, row in issuers_df.iterrows():
    post_signup.append({
        "issuer_id": row["issuer_id"],
        "wallet_provisioned": random.choice([True, False]),
        "wallet_address": f"0x{uuid.uuid4().hex[:40]}",
        "wallet_email_sent": True,
        "dashboard_redirect": True,
        "oauth_verified_min2": random.choice([True, False]),
        "verified_at": random_timestamp(),
        "created_at": random_timestamp(),
        "updated_at": None,
        "metadata": None
    })

post_signup_df = pd.DataFrame(post_signup)
post_signup_df.to_csv("./tables/issuer_post_signup.csv", index=False)


# ------------------------
# ISSUER PREFERENCES 
# ------------------------
preferences = []

for _, row in issuers_df.iterrows():
    preferences.append({
        "issuer_id": row["issuer_id"],
        "raise_target_usd": random.randint(10000,1000000), # not needed
        "token_supply_goal": random.randint(100000,1000000), # issuers with higher social followers should have a higher number (loosely)
        "enable_referrals": False,
        "notification_prefs": None,
        "created_at": random_timestamp(),
        "updated_at": None,
        "metadata": None
    })

preferences_df = pd.DataFrame(preferences)

preferences_df.to_csv("./tables/issuer_preferences.csv", index=False)


# ------------------------
# TOKENS  (ONLY VERIFIED ISSUERS)
# ------------------------
tokens = []
eligible_issuers = issuers_df[issuers_df["status"] == 'PASSED']

for _, row in eligible_issuers.sample(min(NUM_TOKENS, len(eligible_issuers))).reset_index(drop=True).iterrows():
    tokens.append({
        "token_id": len(tokens) + 1,
        "issuer_id": row["issuer_id"],
        "token_symbol": f"TOKEN_{random.randint(1000,9999)}",
        "initial_supply": random.randint(100000,1000000),
        "current_supply_minted": 0,
        "mint_timestamp": random_timestamp(),
        "paused_sales": False,
        "secondary_trading_enabled": False,
        "created_at": random_timestamp(),
        "updated_at": random_timestamp()
    })

tokens_df_temp = pd.DataFrame(tokens)


# ------------------------
# TRANSACTIONS (PRIMARY ONLY)
# ------------------------
from decimal import Decimal, getcontext
getcontext().prec = 28

PRICE_INCREMENT = Decimal(0.000023)
START_PRICE = Decimal(1.0)
MAX_PRICE = Decimal(24.0)

# ---------------- BUILD ISSUER FOLLOWER MAP ----------------
# take max followers per issuer from social table
issuer_followers = (
    social_df.groupby("issuer_id")["followers_count"]
    .max()
    .to_dict()
)

# ---------------- HELPER ----------------
def total_cost(n):
    n = Decimal(n)
    first = START_PRICE
    last = START_PRICE + (n - 1) * PRICE_INCREMENT
    return (n / 2) * (first + last)

# ---------------- TRANSACTIONS ----------------
transactions = []
transaction_id = 1

user_ids = users_df["user_id"].tolist()
active_users = random.sample(user_ids, int(len(user_ids) * 0.65))

# build mapping once
issuer_to_user = dict(zip(issuers_df["issuer_id"], issuers_df["user_id"]))

for _, token in tokens_df_temp.iterrows():
    token_id = token["token_id"]
    issuer_id = token["issuer_id"]

    followers = issuer_followers.get(issuer_id, 0)

    # ---------------- RULE 1: NO SALES ----------------
    if followers < 100001:
        continue

    # ---------------- DEMAND FUNCTION ----------------
    # scale sales with followers
    max_tokens_to_sell = int(min(
        token["initial_supply"],
        followers * random.uniform(0.01, 0.05)
    ))

    tokens_sold = 0

    while tokens_sold < max_tokens_to_sell:

        # batch size (simulate transactions)
        batch = random.randint(1, 50)

        if tokens_sold + batch > max_tokens_to_sell:
            batch = max_tokens_to_sell - tokens_sold

        if batch <= 0:
            break

        # ---------------- PRICE CALC ----------------
        start_n = tokens_sold + 1
        end_n = tokens_sold + batch

        # price of next token
        current_price = min(
            MAX_PRICE,
            START_PRICE + (Decimal(start_n - 1) * PRICE_INCREMENT)
        )

        final_price = min(
            MAX_PRICE,
            START_PRICE + (Decimal(end_n - 1) * PRICE_INCREMENT)
        )

        # total cost using arithmetic series
        total_amount = total_cost(end_n) - total_cost(start_n - 1)

        transactions.append({
            "transaction_id": transaction_id,
            "token_id": token_id,
            "buyer_id": random.choice(user_ids),
            "seller_id": issuer_to_user[issuer_id],
            "quantity": batch,
            "starting_price": float(current_price),
            "ending_price": float(final_price),
            "total_amount_usdc": float(total_amount),
            "transaction_type": "primary",
            "swap_api_reference": None,
            "original_currency": "USD",
            "status": "completed",
            "reversal_reason": None,
            "timestamp": random_timestamp(),
            "on_chain_tx_hash": None,
            "merkle_proof_hash": None
        })

        tokens_sold += batch
        transaction_id += 1

transactions_df = pd.DataFrame(transactions)
transactions_df["total_amount_usdc"] = transactions_df["total_amount_usdc"].astype(float).round(6)

transactions_df.to_csv("./tables/transactions.csv", index=False)


# ------------------------
# USER TOKEN WALLET
# ------------------------
user_token_wallet_df = (
    transactions_df
    .groupby(["buyer_id", "token_id"])
    .agg({
        "quantity": "sum",
        "total_amount_usdc": "sum"
    })
    .reset_index()
    .rename(columns={
        "buyer_id": "user_id",
        "total_amount_usdc": "total_value"
    })
)

user_token_wallet_df.to_csv("./tables/user_token_wallet.csv", index=False)


# ------------------------
# USER WALLET
# ------------------------

wallets = []

user_token_totals_USDC = (
    user_token_wallet_df.groupby("user_id")["total_value"]
    .sum()
    .to_dict()
)

issuer_revenue = (
    transactions_df
    .groupby("seller_id")["total_amount_usdc"]
    .sum()
    .to_dict()
)

for user_id in users_df["user_id"]:

    # ETH balance (random)
    eth_balance = round(random.uniform(0, 5), 6)

    # USDC
    if user_id in issuer_revenue:
        # issuer → must be ≥ revenue
        revenue = issuer_revenue[user_id]
        usdc_balance = revenue + random.uniform(0, 500)
    else:
        usdc_balance = random.uniform(0, 500)

    # token holdings
    # tokens = user_token_balances.get(user_id, {})
    token_value = user_token_totals_USDC.get(user_id, 0)

    wallets.append({
        "wallet_id": generate_uuid(),
        "user_id": user_id,
        "eth_balance": format(eth_balance, ".6f"),
        "usdc_balance": format(usdc_balance, ".6f"),
        "total_token_value": token_value,    
        # "token_balances": tokens,   # dict {token_id: qty}
        "created_at": random_timestamp()
    })

wallets_df = pd.DataFrame(wallets)

wallets_df.to_csv("./tables/user_wallet.csv", index=False)


# ------------------------
# TOKENS FINAL
# ------------------------

token_stats = (
    transactions_df
    .groupby("token_id")
    .agg({
        "quantity": "sum",
        "total_amount_usdc": "sum",
        # "ending_price" :"max"
        
    })
    .reset_index()
)

token_stats["current_price"] = (
    1 + token_stats["quantity"] * 0.000023
).clip(upper=24)

# round
token_stats["current_price"] = token_stats["current_price"].round(6) 
token_stats["total_amount_usdc"] = token_stats["total_amount_usdc"].round(6)

# # merge into existing tokens_df
tokens_df = tokens_df_temp.merge(token_stats, on="token_id", how="left")

tokens_df["quantity"] = tokens_df["quantity"].fillna(0)
tokens_df["total_amount_usdc"] = tokens_df["total_amount_usdc"].fillna(0)
tokens_df["current_price"] = tokens_df["current_price"].fillna(1.0)
tokens_df.rename(columns={
    "quantity": "total_sold",
    "total_amount_usdc": "total_revenue"
}, inplace=True)

tokens_df.to_csv("./tables/tokens.csv", index=False)

# ------------------------
# WRITE TO DATABASE
# ------------------------
truncate_table(conn_string, 'users', cascade=True)
copy_data(conn_string, users_df,'users')

truncate_table(conn_string, 'issuers', cascade=True)
copy_data(conn_string, issuers_df,'issuers')

truncate_table(conn_string, 'identity_verification', cascade=True)
copy_data(conn_string, identity_df,'identity_verification')

truncate_table(conn_string, 'social_verification', cascade=True)
copy_data(conn_string, social_df,'social_verification')

truncate_table(conn_string, 'athlete_profile', cascade=True)
copy_data(conn_string, athlete_df,'athlete_profile')

truncate_table(conn_string, 'issuer_post_signup', cascade=True)
copy_data(conn_string, post_signup_df,'issuer_post_signup')

truncate_table(conn_string, 'issuer_preferences', cascade=True)
copy_data(conn_string, preferences_df,'issuer_preferences')

truncate_table(conn_string, 'transactions', cascade=True)
copy_data(conn_string, transactions_df,'transactions')

truncate_table(conn_string, 'user_token_wallet', cascade=True)
copy_data(conn_string, user_token_wallet_df,'user_token_wallet')

truncate_table(conn_string, 'user_wallet', cascade=True)
copy_data(conn_string, wallets_df,'user_wallet')

truncate_table(conn_string, 'tokens', cascade=True)
copy_data(conn_string, tokens_df,'tokens')