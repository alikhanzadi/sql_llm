------------------------------------------------------------
-- CORE ENTITIES
------------------------------------------------------------
-- PostgreSQL version of athl_raw_tables.sql
-- Notes:
-- - Replaced Snowflake types/functions with PostgreSQL equivalents.
-- - Keeps original comments/intent where possible.

-- Main Users table
CREATE TABLE IF NOT EXISTS users (
  -- Identity
  user_id                    VARCHAR(36) PRIMARY KEY,     -- UUID PK
  user_role                  TEXT NOT NULL,               -- 'ISSUER','FAN','BOTH'
  display_name               TEXT,                        -- "What should we call you?"
  username                   TEXT NOT NULL,               -- 3-20 chars, unique across platform
  referral_id                TEXT,                        -- UUID/unique code
  email                      TEXT,                        -- validated + verified email
  email_verified             BOOLEAN DEFAULT FALSE,       -- strong email verification
  email_verification_status  TEXT,                        -- 'PENDING','VERIFIED','REJECTED','RISKY'
  email_verification_score   NUMERIC(5,2),               -- optional reputation score (0-100)

  -- Fan/Issuer profile basics (common to both)
  country                    TEXT,                        -- ISO alpha-2
  zip_code                   TEXT,                        -- format-validated upstream
  gender                     TEXT,                        -- 'Male','Female','Other','Prefer not to say'
  time_zone                  TEXT,

  -- Authentication modalities
  -- login_methods_allowed      TEXT[],                      -- e.g. {'SOCIAL','EMAIL_PASSWORD','PASSKEY'}
  password_hash              TEXT,                        -- for fans using email/password (nullable)
  passkey_public_key         JSONB,                       -- WebAuthn credential (nullable)
  primary_social_platform    TEXT,                        -- e.g. 'X','INSTAGRAM','YOUTUBE' (nullable)
  primary_social_handle      TEXT,                        -- nullable
  mfa_enabled                BOOLEAN DEFAULT FALSE,       -- issuers must enable MFA; fans optional
  account_status             TEXT DEFAULT 'ACTIVE',       -- 'ACTIVE','LOCKED','DISABLED','PENDING_VERIFICATION'

  -- System
  created_at                 TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at                 TIMESTAMPTZ,
  last_login_at              TIMESTAMPTZ,
  created_ip                 TEXT,
  created_user_agent         TEXT,
  metadata                   JSONB,

  CONSTRAINT uq_users_username UNIQUE (username),
  CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS issuers (
  user_id            VARCHAR(36),
  issuer_id          VARCHAR(36) PRIMARY KEY,   -- UUID PK
  issuer_type        TEXT,                      -- 'ATHLETE' | 'CREATOR'
  email              TEXT,
  username           TEXT,
  status             TEXT,                      -- 'PENDING','ACTIVE','SUSPENDED','ARCHIVED'
  level              TEXT,                      -- 'YOUTH','COLLEGE','PRO'
  country            TEXT,
  region             TEXT,
  created_at         TIMESTAMPTZ,
  updated_at         TIMESTAMPTZ,
  metadata           JSONB,
  CONSTRAINT fk_issuers_user_id FOREIGN KEY (user_id) REFERENCES users(user_id),
  CONSTRAINT uq_issuer_user UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS athlete_profile (
  issuer_id          VARCHAR(36) PRIMARY KEY,
  user_id            VARCHAR(36),
  sport              TEXT,
  -- sport_id         TEXT, -- ADD LATER
  team               TEXT,
  league             TEXT,
  position_primary   TEXT,
  position_secondary TEXT,
  multi_sport        BOOLEAN,
  biography          TEXT,
  profile_completion NUMERIC(5,2),              -- percent 0-100
  created_at         TIMESTAMPTZ,
  updated_at         TIMESTAMPTZ,
  metadata           JSONB,
  CONSTRAINT fk_athlete_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id),
  CONSTRAINT fk_athlete_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS creator_profile (
  issuer_id           VARCHAR(36) PRIMARY KEY,
  user_id             VARCHAR(36),
  creator_category    TEXT,                     -- e.g., 'YouTuber','Streamer','Musician'
  content_mediums     TEXT[],                   -- list of mediums (YouTube, TikTok, IG, etc.)
  niche               TEXT,
  biography           TEXT,
  profile_completion  NUMERIC(5,2),             -- percent 0-100
  created_at          TIMESTAMPTZ,
  updated_at          TIMESTAMPTZ,
  metadata            JSONB,
  CONSTRAINT fk_creator_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id),
  CONSTRAINT fk_creator_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- =========================================================
-- ONBOARDING / POST-SIGNUP
-- =========================================================
CREATE TABLE IF NOT EXISTS issuer_post_signup (
  issuer_id           VARCHAR(36) PRIMARY KEY,
  wallet_provisioned  BOOLEAN,
  wallet_address      TEXT,
  wallet_email_sent   BOOLEAN,
  dashboard_redirect  BOOLEAN,
  oauth_verified_min2 BOOLEAN,                  -- verified at least 2 platforms
  verified_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ,
  updated_at          TIMESTAMPTZ,
  metadata            JSONB,
  CONSTRAINT fk_post_signup_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id)
);

CREATE TABLE IF NOT EXISTS waitlist (
  waitlist_id        VARCHAR(36) PRIMARY KEY,
  issuer_id          VARCHAR(36),
  added_at           TIMESTAMPTZ,
  status             TEXT,                      -- 'PENDING','APPROVED','REJECTED','REMOVED'
  approved_at        TIMESTAMPTZ,
  activated_at       TIMESTAMPTZ,               -- when issuer becomes active
  notes              TEXT,
  metadata           JSONB,
  CONSTRAINT fk_waitlist_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id)
);

CREATE TABLE IF NOT EXISTS issuer_preferences (
  issuer_id          VARCHAR(36) PRIMARY KEY,
  raise_target_usd   NUMERIC(38,6),
  token_supply_goal  NUMERIC(38,6),
  enable_referrals   BOOLEAN,
  notification_prefs JSONB,
  created_at         TIMESTAMPTZ,
  updated_at         TIMESTAMPTZ,
  metadata           JSONB,
  CONSTRAINT fk_preferences_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id)
);

-- =========================================================
-- IDENTITY & SOCIAL VERIFICATION
-- =========================================================
CREATE TABLE IF NOT EXISTS identity_verification (
  identity_check_id  VARCHAR(36) PRIMARY KEY,
  issuer_id          VARCHAR(36),
  provider           TEXT,                      -- e.g., 'Persona','Onfido'
  status             TEXT,                      -- 'INITIATED','PENDING','PASSED','FAILED','MANUAL_REVIEW'
  level              TEXT,                      -- optional verification level
  alias_confidence   NUMERIC(5,2),              -- 0-100
  opted_in           BOOLEAN,
  initiated_at       TIMESTAMPTZ,
  completed_at       TIMESTAMPTZ,
  failure_reason     TEXT,
  raw_response       JSONB,
  CONSTRAINT fk_identity_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id)
);

CREATE TABLE IF NOT EXISTS social_verification (
  social_verif_id    VARCHAR(36) PRIMARY KEY,
  issuer_id          VARCHAR(36),
  platform           TEXT,                      -- 'YOUTUBE','TIKTOK','INSTAGRAM','TWITCH','X','FACEBOOK'
  handle             TEXT,
  followers_count    NUMERIC(38,0),
  verified           BOOLEAN,
  initiated_at       TIMESTAMPTZ,
  completed_at       TIMESTAMPTZ,
  attempts           NUMERIC(38,0),
  status             TEXT,                      -- 'SUCCESS','FAILED','PENDING'
  metadata           JSONB,
  CONSTRAINT fk_socialverif_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id)
);

CREATE TABLE IF NOT EXISTS social_media_auth_fail (
  auth_fail_id       VARCHAR(36) PRIMARY KEY,
  issuer_id          VARCHAR(36),
  platform           TEXT,
  failed_at          TIMESTAMPTZ,
  reason_code        TEXT,                      -- 'OAUTH_ERROR','ALIAS_MISMATCH','RATE_LIMIT','WALLET_ERROR'
  reason_detail      TEXT,
  metadata           JSONB,
  CONSTRAINT fk_socialfail_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id)
);

-- =========================================================
-- WALLET AND TOKENS
-- =========================================================
CREATE TABLE IF NOT EXISTS tokens (
  token_id                   BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  issuer_id                  VARCHAR(36) NOT NULL,     -- must reference users.user_id and be an issuer
  token_symbol               TEXT NOT NULL,            -- e.g. 'LEBRON-FT'
  initial_supply             NUMERIC(38,0) NOT NULL,   -- max tokens initial sale
  current_supply_minted      NUMERIC(38,0) DEFAULT 0,
  bonding_curve_start_price  NUMERIC(18,2) DEFAULT 1.00,
  bonding_curve_end_price    NUMERIC(18,2) DEFAULT 24.00,
  mint_timestamp             TIMESTAMPTZ,
  paused_sales               BOOLEAN DEFAULT FALSE,
  secondary_trading_enabled  BOOLEAN DEFAULT FALSE,
  total_revenue_raised       NUMERIC(18,2) DEFAULT 0,
  created_at                 TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at                 TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tokens_issuer FOREIGN KEY (issuer_id) REFERENCES issuers(issuer_id),
  CONSTRAINT uq_tokens_symbol UNIQUE (issuer_id, token_symbol)
);

-- =========================================================
-- Transactions (primary + secondary)
-- =========================================================
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id       BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  token_id             BIGINT NOT NULL,
  buyer_id             VARCHAR(36) NOT NULL,
  seller_id            VARCHAR(36),                    -- null for primary/platform sell
  quantity             NUMERIC(38,0) NOT NULL,
  price_per_token      NUMERIC(18,2) NOT NULL,
  total_amount_usdc    NUMERIC(18,2) NOT NULL,
  transaction_type     TEXT NOT NULL,                  -- 'primary' | 'secondary'
  swap_api_reference   TEXT,                           -- Alchemy Swap ID
  original_currency    TEXT,                           -- e.g., 'ETH'
  status               TEXT NOT NULL,                  -- 'pending' | 'completed' | 'reversed' | 'voided'
  reversal_reason      TEXT,
  "timestamp"          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  on_chain_tx_hash     TEXT,                           -- 66-char hex hash
  merkle_proof_hash    TEXT,                           -- 64-char hex
  CONSTRAINT fk_tx_token  FOREIGN KEY (token_id)  REFERENCES tokens(token_id),
  CONSTRAINT fk_tx_buyer  FOREIGN KEY (buyer_id)  REFERENCES users(user_id),
  CONSTRAINT fk_tx_seller FOREIGN KEY (seller_id) REFERENCES users(user_id)
);

-- =========================================================
-- Payments (issuer payouts & referral payouts)
-- =========================================================
CREATE TABLE IF NOT EXISTS payments (
  payment_id            BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  recipient_id          VARCHAR(36) NOT NULL,          -- issuer or referrer
  linked_transaction_id BIGINT,                        -- nullable for aggregated payouts
  amount_usdc           NUMERIC(18,2) NOT NULL,
  installment_number    NUMERIC(3,0),                  -- 1..12 for issuers; NULL for one-offs
  due_date              DATE NOT NULL,
  status                TEXT NOT NULL,                 -- 'pending' | 'paid' | 'failed'
  payout_tx_reference   TEXT,                          -- USDC transfer hash
  "timestamp"           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_payments_recipient FOREIGN KEY (recipient_id) REFERENCES users(user_id),
  CONSTRAINT fk_payments_tx FOREIGN KEY (linked_transaction_id) REFERENCES transactions(transaction_id)
);
