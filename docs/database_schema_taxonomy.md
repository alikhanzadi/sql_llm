# ATHL Database Taxonomy

## Overview

This schema supports a tokenized marketplace where issuers (athletes/creators) sell tokens to users via a bonding curve.

The system is organized into:

- Core entities (users, issuers)
- Verification & onboarding
- Token economy
- Transactions (event layer)
- Financial state (wallets, aggregates)

---

# 1. Core Entities

## users (DIMENSION)

Represents all platform participants.

### Data Type

- Master entity (dimension table)

### Key Fields

- user_id (PK)
- user_role
- email, username

### Measures

- None (descriptive only)

### Source

- Created during signup

---

## issuers (DIMENSION)

Subset of users who issue tokens.

### Data Type

- Master entity

### Measures

- None directly

### Derived Fields

- status → derived from:
  - identity_verification.status
  - social_verification.status

### Source

- Derived + onboarding process

---

## athlete_profile (DIMENSION)

Additional metadata for athlete issuers.

### Measures

- None

### Source

- User input during onboarding

---

## creator_profile (DIMENSION)

Currently unused (empty placeholder).

---

# 2. Verification & Onboarding

## identity_verification (FACT - EVENT)

Tracks identity/KYC checks.

### Measures

- alias_confidence (score)

### Source

- External provider (e.g. Persona)

---

## social_verification (FACT - EVENT)

Tracks verification of social accounts.

### Measures

- followers_count
- verified (boolean)

### Source

- External APIs (YouTube, Instagram, etc.)

---

## issuer_post_signup (STATE)

Tracks onboarding completion.

### Measures

- wallet_provisioned (boolean)
- oauth_verified_min2 (boolean)

### Source

- System-generated during onboarding flow

---

## issuer_preferences (CONFIG)

Stores issuer-specific settings.

### Measures

- raise_target_usd
- token_supply_goal

### Source

- Issuer input

---

# 3. Token Economy

## tokens (STATE + DERIVED METRICS)

Represents tokenized assets.

### Data Type

- Hybrid (entity + aggregated metrics)

### Measures


| Field                | Meaning                  | Source                     |
| -------------------- | ------------------------ | -------------------------- |
| initial_supply       | total tokens available   | issuer input               |
| numbers_sold         | total tokens sold        | derived from transactions  |
| current_price        | price of last token sold | derived from bonding curve |
| total_revenue_raised | cumulative sales         | sum(transactions)          |


### Derived Logic

- numbers_sold = SUM(quantity)
- current_price = 1 + (numbers_sold - 1) * increment
- total_revenue_raised = SUM(total_amount_usdc)

---

# 4. Transactions (FACT TABLE)

## transactions

Represents primary market purchases.

### Data Type

- Event table (fact)

### Measures


| Field             | Meaning          | Source            |
| ----------------- | ---------------- | ----------------- |
| quantity          | tokens purchased | generated         |
| price_per_token   | marginal price   | bonding curve     |
| total_amount_usdc | total paid       | arithmetic series |


### Pricing Logic

- price(n) = 1 + (n - 1) * increment
- total = sum of prices over batch

### Source

- Generated simulation logic

---

# 5. Aggregations

## issuer_daily_revenue (AGGREGATE FACT)

### Measures

- total_amount_usdc

### Source

- Aggregated from transactions

### Grain

- issuer_id + date

---

# 6. Wallet System (STATE)

## user_token_wallet (FACT - HOLDINGS)

Normalized token ownership.

### Measures


| Field       | Meaning              | Source                     |
| ----------- | -------------------- | -------------------------- |
| quantity    | tokens held          | SUM(transactions.quantity) |
| total_value | total purchase value | SUM(total_amount_usdc)     |


### Grain

- user_id + token_id

---

## user_wallet (STATE SNAPSHOT)

User-level balances.

### Measures


| Field             | Meaning         | Source                             |
| ----------------- | --------------- | ---------------------------------- |
| eth_balance       | crypto balance  | simulated                          |
| usdc_balance      | fiat stablecoin | derived + random                   |
| total_token_value | portfolio value | SUM(user_token_wallet.total_value) |


---

---

# Data Flow

## Core Flow

**Users → Issuers → Tokens → Transactions → Wallets**

## Financial Layer

## **Transactions → Revenue + Wallets**

# Key Concepts

## Event vs State vs Aggregate


| Type      | Example              | Description             |
| --------- | -------------------- | ----------------------- |
| Event     | transactions         | something that happened |
| State     | wallets              | current snapshot        |
| Aggregate | issuer_daily_revenue | summarized events       |


---

# Pricing Model

Bonding curve:

price(n) = 1 + (n - 1) * 0.000023

Batch cost:

cost(a → b) = total_cost(b) - total_cost(a - 1)

---

# Constraints

- Only issuers with:
  - identity = PASSED
  - social = PASSED  
  can mint tokens
- Token price capped at 24
- ≤ 65% of users participate in trading

---

# Design Principles

- Separation of:
  - events (transactions)
  - state (wallets)
  - aggregates (revenue)
- Deterministic pricing model
- Fully relational (no JSON blobs)

---

# Future Improvements

- Secondary market
- Price history table
- Fraud detection
- Liquidity modeling

Alt text!

# ATHL Data Model & Metrics

---

## Key Relationship Explanations

### Users ↔ Issuers

- 1 user → 0 or 1 issuer  
- Issuer is an extension of user

### Issuers → Tokens

- 1 issuer → many tokens  
- Only **PASSED issuers** create tokens

### Tokens → Transactions

- 1 token → many transactions  
- Transactions define:
  - price
  - volume
  - revenue

### Transactions → Wallets

- Buyer → gains tokens  
- Seller (issuer) → gains USDC

---

## Wallet Structure

- **user_token_wallet** → granular holdings  
- **user_wallet** → aggregated snapshot

---

## Aggregation Layer

- **issuer_daily_revenue**
  - derived from transactions  
  - grouped by issuer + date

---

## Mental Model

Think in layers:

### 1. Identity Layer

- users  
- issuers  
- verification tables

### 2. Asset Layer

- tokens

### 3. Event Layer

- transactions

### 4. State Layer

- wallets

### 5. Analytics Layer

- issuer_daily_revenue

---

## Important Design Choices

- **Transactions = source of truth**
- Everything else is:
  - derived (tokens, revenue)  
  - aggregated (wallets)

---

# Metrics Catalog

## Issuer Metrics

### Total Revenue (Lifetime)

- **Definition:** Sum of all primary sales for an issuer  
- **Calc:** `SUM(transactions.total_amount_usdc)`  
- **Filter:** `transaction_type = 'primary' AND status = 'completed'`  
- **Group by:** `seller_id`

### Daily Revenue

- **Calc:** `SUM(total_amount_usdc)`  
- **Group by:** `seller_id, DATE(timestamp)`  
- **Table:** issuer_daily_revenue

### Tokens Issued (Count)

- **Calc:** `COUNT(tokens.token_id)`  
- **Filter:** `issuer_id = X`

### Total Supply Issued

- **Calc:** `SUM(tokens.initial_supply)`

### Tokens Sold

- **Calc:** `SUM(transactions.quantity)`  
- **Join:** tokens ↔ transactions

### Sell-through Rate

- **Calc:** `SUM(quantity) / SUM(initial_supply)`

### Average Selling Price (ASP)

- **Calc:** `SUM(total_amount_usdc) / SUM(quantity)`

### Latest Price

- **Calc:** last `ending_price` by timestamp  
- Or: `tokens.current_price`

---

## Token Metrics

### Numbers Sold

- **Calc:** `SUM(transactions.quantity)`

### Current Price (Last Sold)

- **Calc:** last `ending_price`  
- Or: `1 + (numbers_sold - 1) * increment`

### Next Price (Marginal)

- **Calc:** `1 + numbers_sold * increment`

### Total Revenue Raised

- **Calc:** `SUM(total_amount_usdc)`

### Average Price

- **Calc:** `SUM(total_amount_usdc) / SUM(quantity)`

### Volume

- **Calc:** `SUM(quantity)`

### Number of Buyers

- **Calc:** `COUNT(DISTINCT buyer_id)`

---

## User Metrics

### Tokens Held

- **Calc:** `SUM(quantity)`  
- **Table:** user_token_wallet

### Total Token Portfolio Value

- **Calc:** `SUM(user_token_wallet.total_value)`  
- **Stored in:** user_wallet.total_token_value

### USDC Balance

- From: `user_wallet.usdc_balance`

### ETH Balance

- From: `user_wallet.eth_balance`

### Number of Tokens Owned

- **Calc:** `COUNT(DISTINCT token_id)`

### Total Purchases

- **Calc:** `SUM(total_amount_usdc)`  
- **Filter:** buyer_id = X

---

## Platform Metrics

### Total Platform Revenue

- **Calc:** `SUM(transactions.total_amount_usdc)`

### Active Users

- **Calc:** `COUNT(DISTINCT buyer_id)`

### Participation Rate

- **Calc:** `active_users / total_users`

### Total Tokens Sold

- **Calc:** `SUM(quantity)`

### Average Transaction Size

- **Calc:** `AVG(total_amount_usdc)`

### Average Tokens per Transaction

- **Calc:** `AVG(quantity)`

---

## Pricing (Bonding Curve)

### Price at n

price(n) = 1 + (n - 1) * 0.000023

### Batch Cost

cost(a → b) = total_cost(b) - total_cost(a - 1)

### Revenue Consistency Check

SUM(total_amount_usdc) ≈ derived from curve

---

## Data Lineage

- **transactions** → source of truth  
- **tokens** → derived aggregates  
- **user_token_wallet** → holdings  
- **user_wallet** → snapshot  
- **issuer_daily_revenue** → aggregated revenue

