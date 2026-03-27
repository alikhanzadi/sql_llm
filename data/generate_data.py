import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)

# ------------------------
# CONFIG
# ------------------------
NUM_USERS = 2000
NUM_ATHLETES = 100
NUM_TRADES = 50000

START_DATE = datetime(2025, 1, 1)

# ------------------------
# USERS
# ------------------------
users = pd.DataFrame({
    "user_id": range(1, NUM_USERS + 1),
    "signup_date": [START_DATE + timedelta(days=random.randint(0, 365)) for _ in range(NUM_USERS)],
    "region": np.random.choice(["North", "South", "East", "West"], NUM_USERS)
})

# ------------------------
# ATHLETES
# ------------------------
sports = ["Basketball", "Soccer", "Football"]

athletes = pd.DataFrame({
    "athlete_id": range(1, NUM_ATHLETES + 1),
    "name": [f"Athlete_{i}" for i in range(1, NUM_ATHLETES + 1)],
    "sport": np.random.choice(sports, NUM_ATHLETES),
    "team": [f"Team_{random.randint(1,10)}" for _ in range(NUM_ATHLETES)]
})

# ------------------------
# TOKENS
# ------------------------
tokens = pd.DataFrame({
    "token_id": range(1, NUM_ATHLETES + 1),
    "athlete_id": range(1, NUM_ATHLETES + 1),
    "initial_price": np.round(np.random.uniform(5, 50, NUM_ATHLETES), 2)
})

# ------------------------
# EVENTS (performance)
# ------------------------
events = []
for athlete_id in range(1, NUM_ATHLETES + 1):
    for _ in range(20):
        event_date = START_DATE + timedelta(days=random.randint(0, 365))
        performance_score = np.round(np.random.normal(50, 15), 2)
        events.append([athlete_id, event_date, performance_score])

events = pd.DataFrame(events, columns=["athlete_id", "event_date", "performance_score"])

# ------------------------
# TRADES
# ------------------------
trades = []

for i in range(NUM_TRADES):
    user_id = random.randint(1, NUM_USERS)
    token_id = random.randint(1, NUM_ATHLETES)
    trade_date = START_DATE + timedelta(days=random.randint(0, 365))
    
    quantity = random.randint(1, 10)
    
    base_price = tokens.loc[tokens["token_id"] == token_id, "initial_price"].values[0]
    price_fluctuation = np.random.normal(0, 5)
    price = max(1, base_price + price_fluctuation)
    
    trades.append([i+1, user_id, token_id, trade_date, quantity, round(price, 2)])

trades = pd.DataFrame(trades, columns=[
    "trade_id", "user_id", "token_id", "trade_date", "quantity", "price"
])

# ------------------------
# SAVE FILES
# ------------------------
users.to_csv("data/users.csv", index=False)
athletes.to_csv("data/athletes.csv", index=False)
tokens.to_csv("data/tokens.csv", index=False)
trades.to_csv("data/trades.csv", index=False)
events.to_csv("data/events.csv", index=False)

print("✅ Data generated in /data folder")