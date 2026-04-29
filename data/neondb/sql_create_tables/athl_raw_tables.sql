------------------------------------------------------------
-- CORE ENTITIES
------------------------------------------------------------
-- Main Users table (Snowflake SQL)
-- Houses core identity + auth profile for ANY user (issuer or fan)
CREATE OR REPLACE TABLE users (
  -- Identity
  user_id                 VARCHAR(36)    NOT NULL,         -- UUID PK
  user_role               STRING         NOT NULL,         -- 'ISSUER','FAN','BOTH'
  display_name            STRING,                          -- "What should we call you?"
  username                STRING         NOT NULL,         -- 3–20 chars, unique across platform
  referral_id             STRING,                          -- UUID/unique code
  email                   STRING,                          -- validated + verified email
  email_verified          BOOLEAN        DEFAULT FALSE,    -- strong email verification
  email_verification_status STRING,                        -- 'PENDING','VERIFIED','REJECTED','RISKY'
  email_verification_score NUMBER(5,2),                    -- optional reputation score (0–100)

  -- Fan/Issuer profile basics (common to both)
  country                 STRING,                          -- ISO alpha-2
  zip_code                STRING,                          -- format-validated upstream
  gender                  STRING,                          -- 'Male','Female','Other','Prefer not to say'
  time_zone               STRING,

  -- Authentication modalities (top-level flags; details live in user_mfa/login tables)
  login_methods_allowed   ARRAY,                           -- e.g. ['SOCIAL','EMAIL_PASSWORD','PASSKEY']
  password_hash           STRING,                          -- for fans using email/password (nullable)
  passkey_public_key      VARIANT,                         -- WebAuthn credential (nullable)
  primary_social_platform STRING,                          -- e.g. 'X','INSTAGRAM','YOUTUBE' (nullable)
  primary_social_handle   STRING,                          -- nullable
  mfa_enabled             BOOLEAN        DEFAULT FALSE,    -- issuers must enable MFA; fans optional
  account_status          STRING         DEFAULT 'ACTIVE', -- 'ACTIVE','LOCKED','DISABLED','PENDING_VERIFICATION'

  -- System
  created_at              TIMESTAMP_TZ   DEFAULT CURRENT_TIMESTAMP(),
  updated_at              TIMESTAMP_TZ,
  last_login_at           TIMESTAMP_TZ,
  created_ip              STRING,
  created_user_agent      STRING,
  metadata                VARIANT,

  CONSTRAINT pk_users PRIMARY KEY (user_id),
  CONSTRAINT uq_users_username UNIQUE (username),
  CONSTRAINT uq_users_email UNIQUE (email),
  CONSTRAINT fk_referral_id FOREIGN KEY (referrer_id) REFERENCES athl.user_referral(referral_id),
);

-- Notes:
-- - Username must be unique, 3–20 alphanumeric (UI enforces format + real-time availability). :contentReference[oaicite:0]{index=0}
-- - Fans may log in with social/email/password/passkey; issuers use social login tied to their largest accounts. :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}
-- - Store results of strong email verification (status/score/evidence) in the user database. :contentReference[oaicite:3]{index=3}
-- - MFA must be tracked; issuers required, fans encouraged. Full event/config lives in dedicated MFA tables; this flag mirrors effective state. :contentReference[oaicite:4]{index=4} :contentReference[oaicite:5]{index=5}
-- - Common profile fields (country/zip/gender) are captured during sign-up and apply to both roles. :contentReference[oaicite:6]{index=6}

-- -- Optional convenience view to classify effective login options per policy


-- DROP TABLE IF EXISTS ISSUER;
CREATE OR REPLACE TABLE issuers (
  user_id            VARCHAR(36),
  issuer_id          VARCHAR(36)    PRIMARY KEY,    -- UUID PK
  issuer_type        STRING,             -- 'ATHLETE' | 'CREATOR'
    -- CHECK (issuer_type IN ('ATHLETE','CREATOR')),
  email              STRING,
  username           STRING,
  status             STRING,            -- 'PENDING','ACTIVE','SUSPENDED','ARCHIVED'
  level              STRING,            -- 'YOUTH','COLLEGE','PRO' (if applicable)
  country            STRING,
  region             STRING,
  created_at         TIMESTAMP_TZ,
  updated_at         TIMESTAMP_TZ,
  metadata           VARIANT,
  CONSTRAINT fk_user_id FOREIGN KEY (issuer_id) REFERENCES users(user_id),
  CONSTRAINT uq_issuer_user UNIQUE (user_id)
);

CREATE OR REPLACE TABLE athlete_profile (
  issuer_id          VARCHAR(36)        PRIMARY KEY,
  user_id            VARCHAR(36),
  sport              STRING,
  -- sport_id           STRING,            --ADD LATER
  team               STRING,
  league             STRING,
  position_primary   STRING,
  position_secondary STRING,
  multi_sport        BOOLEAN,
  biography          STRING,
  profile_completion NUMBER(5,2),       -- percent 0-100
  created_at         TIMESTAMP_TZ,
  updated_at         TIMESTAMP_TZ,
  metadata           VARIANT,
  CONSTRAINT fk_athlete_issuer FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id),
  CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) 
);

CREATE OR REPLACE TABLE creator_profile (
  issuer_id           VARCHAR(36)       PRIMARY KEY,
  user_id             VARCHAR(36),
  creator_category    STRING,           -- e.g., 'YouTuber','Streamer','Musician'
  content_mediums     ARRAY,            -- list of mediums (YouTube, TikTok, IG, etc.)
  niche               STRING,
  biography           STRING,
  profile_completion  NUMBER(5,2),      -- percent 0-100
  created_at          TIMESTAMP_TZ,
  updated_at          TIMESTAMP_TZ,
  metadata            VARIANT,
  CONSTRAINT fk_creator_issuer FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id),
  CONSTRAINT fk_user_id FOREIGN KEY (issuer_id) REFERENCES users(user_id)  
);
-- =========================================================
-- ONBOARDING / POST-SIGNUP
-- =========================================================
-- DROP TABLE post_signup;
CREATE OR REPLACE TABLE issuer_post_signup (
  issuer_id           VARCHAR(36)       PRIMARY KEY,
  wallet_provisioned  BOOLEAN,
  wallet_address      STRING,
  wallet_email_sent   BOOLEAN,
  dashboard_redirect  BOOLEAN,
  oauth_verified_min2 BOOLEAN,          -- verified at least 2 platforms
  verified_at         TIMESTAMP_TZ,
  created_at          TIMESTAMP_TZ,
  updated_at          TIMESTAMP_TZ,
  metadata            VARIANT,
  CONSTRAINT fk_post_signup_issuer FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id)
);

CREATE OR REPLACE TABLE waitlist (
  waitlist_id        VARCHAR(36)        PRIMARY KEY,
  issuer_id          VARCHAR(36),
  added_at           TIMESTAMP_TZ,
  status             STRING,            -- 'PENDING','APPROVED','REJECTED','REMOVED'
  approved_at        TIMESTAMP_TZ,
  activated_at       TIMESTAMP_TZ,      -- when issuer becomes active
  notes              STRING,
  metadata           VARIANT,
  CONSTRAINT fk_waitlist_issuer FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id)
);

CREATE OR REPLACE TABLE issuer_preferences (
  issuer_id          VARCHAR(36)        PRIMARY KEY,
  raise_target_usd   NUMBER(38, 6),
  token_supply_goal  NUMBER(38, 6),
  enable_referrals   BOOLEAN,
  notification_prefs VARIANT,
  created_at         TIMESTAMP_TZ,
  updated_at         TIMESTAMP_TZ,
  metadata           VARIANT,
  CONSTRAINT fk_preferences_issuer FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id)
);

-- =========================================================
-- IDENTITY & SOCIAL VERIFICATION
-- =========================================================
CREATE OR REPLACE TABLE identity_verification (
  identity_check_id  VARCHAR(36)        PRIMARY KEY,
  issuer_id          VARCHAR(36),
  provider           STRING,            -- e.g., 'Persona','Onfido'
  status             STRING,            -- 'INITIATED','PENDING','PASSED','FAILED','MANUAL_REVIEW'
  level              STRING,            -- optional verification level
  alias_confidence   NUMBER(5,2),       -- 0-100
  opted_in           BOOLEAN,           -- if high-profile opted-in to identity verification
  initiated_at       TIMESTAMP_TZ,
  completed_at       TIMESTAMP_TZ,
  failure_reason     STRING,
  raw_response       VARIANT,
  CONSTRAINT fk_identity_issuer FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id)
);

CREATE OR REPLACE TABLE social_verification (
  social_verif_id    VARCHAR(36)        PRIMARY KEY,
  issuer_id          VARCHAR(36),
  platform           STRING,            -- 'YOUTUBE','TIKTOK','INSTAGRAM','TWITCH','X','FACEBOOK'
  handle             STRING,
  followers_count    NUMBER(38,0),
  verified           BOOLEAN,
  initiated_at       TIMESTAMP_TZ,
  completed_at       TIMESTAMP_TZ,
  attempts           NUMBER(38,0),
  status             STRING,            -- 'SUCCESS','FAILED','PENDING'
  metadata           VARIANT,
  CONSTRAINT fk_socialverif_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
);

CREATE OR REPLACE TABLE social_media_auth_fail (
  auth_fail_id       VARCHAR(36)        PRIMARY KEY,
  issuer_id          VARCHAR(36),
  platform           STRING,
  failed_at          TIMESTAMP_TZ,
  reason_code        STRING,            -- 'OAUTH_ERROR','ALIAS_MISMATCH','RATE_LIMIT','WALLET_ERROR', etc.
  reason_detail      STRING,
  metadata           VARIANT,
  CONSTRAINT fk_socialfail_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
);

-- =========================================================
-- REFERRALS
-- =========================================================
-- CREATE OR REPLACE TABLE athl.user_referral (
--   referral_id        VARCHAR(36)        PRIMARY KEY,
--   referrer_issuer_id VARCHAR(36),
--   referred_issuer_id VARCHAR(36),
--   referral_code      STRING,
--   link_created_at    TIMESTAMP_TZ,
--   redeemed_at        TIMESTAMP_TZ,
--   status             STRING,            -- 'ACTIVE','EXPIRED','REDEEMED','CANCELLED'
--   reward_usdc        NUMBER(38, 6),
--   metadata           VARIANT,
--   CONSTRAINT fk_referral_referrer FOREIGN KEY (referrer_issuer_id) REFERENCES athl.issuer(issuer_id),
--   CONSTRAINT fk_referral_referred FOREIGN KEY (referred_issuer_id) REFERENCES athl.issuer(issuer_id)
-- );
-- =========================================================
-- AUTH / LOGIN / MFA
-- =========================================================
-- CREATE OR REPLACE TABLE athl.user_login (
--   login_id           VARCHAR(36)        PRIMARY KEY,
--   issuer_id          VARCHAR(36),
--   email              STRING,
--   attempted_at       TIMESTAMP_TZ,
--   success            BOOLEAN,
--   failure_reason     STRING,
--   ip_address         STRING,
--   user_agent         STRING,
--   metadata           VARIANT,
--   CONSTRAINT fk_login_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
-- );

-- CREATE OR REPLACE TABLE athl.login_session (
--   session_id         VARCHAR(36)        PRIMARY KEY,
--   issuer_id          VARCHAR(36),
--   started_at         TIMESTAMP_TZ,
--   last_seen_at       TIMESTAMP_TZ,
--   ended_at           TIMESTAMP_TZ,
--   end_reason         STRING,            -- 'LOGOUT','TIMEOUT','INVALIDATED'
--   num_attempts       NUMBER(38,0),
--   mfa_required       BOOLEAN,
--   metadata           VARIANT,
--   CONSTRAINT fk_session_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
-- );

-- CREATE OR REPLACE TABLE athl.user_mfa (
--   issuer_id          VARCHAR(36)        PRIMARY KEY,
--   mfa_enabled        BOOLEAN,
--   enabled_at         TIMESTAMP_TZ,
--   methods_enabled    ARRAY,             -- ['TOTP','SMS','EMAIL','BACKUP_CODES','SECURITY_QUESTIONS']
--   metadata           VARIANT,
--   CONSTRAINT fk_mfa_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
-- );

-- CREATE OR REPLACE TABLE athl.mfa_log (
--   mfa_event_id       VARCHAR(36)        PRIMARY KEY,
--   issuer_id          VARCHAR(36),
--   session_id         VARCHAR(36),
--   method             STRING,
--   attempted_at       TIMESTAMP_TZ,
--   success            BOOLEAN,
--   failure_reason     STRING,
--   metadata           VARIANT,
--   CONSTRAINT fk_mfalog_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
-- );

-- CREATE OR REPLACE TABLE athl.mfa_security_questions (
--   issuer_id          VARCHAR(36),
--   question_id        VARCHAR(36),
--   question           STRING,
--   answer_hash        STRING,
--   created_at         TIMESTAMP_TZ,
--   updated_at         TIMESTAMP_TZ,
--   PRIMARY KEY (issuer_id, question_id),
--   CONSTRAINT fk_mfaq_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
-- );

-- CREATE OR REPLACE TABLE athl.mfa_backup_code (
--   issuer_id          VARCHAR(36),
--   code_hash          STRING,
--   issued_at          TIMESTAMP_TZ,
--   used_at            TIMESTAMP_TZ,
--   revoked            BOOLEAN DEFAULT FALSE,
--   PRIMARY KEY (issuer_id, code_hash),
--   CONSTRAINT fk_mfabackup_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuer(issuer_id)
-- );
-- =========================================================
-- WALLET AND TOKENS -_CREATE WALLET TABLE !
-- =========================================================
CREATE OR REPLACE TABLE athl.tokens (
  token_id                   BIGINT          NOT NULL IDENTITY(1,1) PRIMARY KEY,
  issuer_id                  VARCHAR(36)     NOT NULL,  -- must reference users.user_id and be an issuer
  token_symbol               STRING          NOT NULL,  -- e.g. 'LEBRON-FT'
  initial_supply             NUMBER(38,0)    NOT NULL,  -- max tokens initial sale
  current_supply_minted      NUMBER(38,0)    DEFAULT 0,
  bonding_curve_start_price  NUMBER(18,2)    DEFAULT 1.00,
  bonding_curve_end_price    NUMBER(18,2)    DEFAULT 24.00,
  mint_timestamp             TIMESTAMP_TZ,
  paused_sales               BOOLEAN         DEFAULT FALSE,
  secondary_trading_enabled  BOOLEAN         DEFAULT FALSE,
  total_revenue_raised       NUMBER(18,2)    DEFAULT 0,
  created_at                 TIMESTAMP_TZ    DEFAULT CURRENT_TIMESTAMP(),
  updated_at                 TIMESTAMP_TZ    DEFAULT CURRENT_TIMESTAMP(),

  -- CONSTRAINT pk_fan_tokens PRIMARY KEY (token_id),
  CONSTRAINT fk_tokens_issuer FOREIGN KEY (issuer_id) REFERENCES athl.issuers(issuer_id),
  CONSTRAINT uq_tokens_symbol UNIQUE (issuer_id, token_symbol)
);

-- =========================================================
-- Transactions (primary + secondary)
-- =========================================================
CREATE OR REPLACE TABLE athl.transactions (
  transaction_id       BIGINT         NOT NULL IDENTITY(1,1),
  token_id             BIGINT         NOT NULL,
  buyer_id             VARCHAR(36)    NOT NULL,
  seller_id            VARCHAR(36),              -- null for primary/platform sell !
  quantity             NUMBER(38,0)   NOT NULL,
  price_per_token      NUMBER(18,2)   NOT NULL,
  total_amount_usdc    NUMBER(18,2)   NOT NULL,
  transaction_type     STRING         NOT NULL,  -- 'primary' | 'secondary'
  swap_api_reference   STRING,                   -- Alchemy Swap ID
  original_currency    STRING,                   -- e.g., 'ETH'
  status               STRING         NOT NULL,  -- 'pending' | 'completed' | 'reversed' | 'voided'
  reversal_reason      STRING,                   -- nullable
  timestamp            TIMESTAMP_TZ   DEFAULT CURRENT_TIMESTAMP(),
  on_chain_tx_hash     STRING,                   -- 66-char hex hash (nullable pre-rollup)
  merkle_proof_hash    STRING,                   -- 64-char hex

  CONSTRAINT pk_transactions PRIMARY KEY (transaction_id),
  CONSTRAINT fk_tx_token  FOREIGN KEY (token_id)  REFERENCES athl.tokens(token_id),
  CONSTRAINT fk_tx_buyer  FOREIGN KEY (buyer_id)  REFERENCES athl.users(user_id),
  CONSTRAINT fk_tx_seller FOREIGN KEY (seller_id) REFERENCES athl.users(user_id)
);

-- -- =========================================================
-- -- 4) Referrals (sign-ups & commissions)
-- -- =========================================================
-- CREATE OR REPLACE TABLE <SCHEMA>.referrals (
--   referral_id         BIGINT         NOT NULL IDENTITY(1,1),
--   referrer_user_id    BIGINT         NOT NULL,
--   referred_user_id    BIGINT         NOT NULL,
--   referral_timestamp  TIMESTAMP_TZ   DEFAULT CURRENT_TIMESTAMP(),
--   commission_earned   NUMBER(18,2),             -- nullable until payout  !
--   commission_year     NUMBER(3,0),              -- 1..3
--   lifetime_earnings   NUMBER(18,2)   DEFAULT 0,
--   cap_reached         BOOLEAN        DEFAULT FALSE,

--   CONSTRAINT pk_referrals PRIMARY KEY (referral_id),
--   CONSTRAINT fk_referrals_referrer FOREIGN KEY (referrer_user_id) REFERENCES <SCHEMA>.users(user_id),
--   CONSTRAINT fk_referrals_referred FOREIGN KEY (referred_user_id) REFERENCES <SCHEMA>.users(user_id),
--   CONSTRAINT uq_referrals UNIQUE (referrer_user_id, referred_user_id)
-- );

-- ALTER TABLE <SCHEMA>.referrals ADD SEARCH OPTIMIZATION ON EQUALITY(referrer_user_id, referred_user_id); 


-- =========================================================
-- 5) Payments (issuer payouts & referral payouts)
-- =========================================================
CREATE OR REPLACE TABLE athl.payments (
  payment_id            BIGINT         NOT NULL IDENTITY(1,1),
  recipient_id          VARCHAR(36)    NOT NULL,               -- issuer or referrer
  linked_transaction_id BIGINT,                                -- nullable for aggregated payouts
  amount_usdc           NUMBER(18,2)   NOT NULL,
  installment_number    NUMBER(3,0),                           -- 1..12 for issuers; NULL for one-offs
  due_date              DATE           NOT NULL,
  status                STRING         NOT NULL,               -- 'pending' | 'paid' | 'failed'
  payout_tx_reference   STRING,                                -- USDC transfer hash
  timestamp             TIMESTAMP_TZ   DEFAULT CURRENT_TIMESTAMP(),

  CONSTRAINT pk_payments PRIMARY KEY (payment_id),
  CONSTRAINT fk_payments_recipient FOREIGN KEY (recipient_id) REFERENCES athl.users(user_id),
  CONSTRAINT fk_payments_tx        FOREIGN KEY (linked_transaction_id) REFERENCES athl.transactions(transaction_id)
  -- CONSTRAINT ck_payments_status    CHECK (status IN ('pending','paid','failed'))
);

-- ALTER TABLE athl.payments ADD SEARCH OPTIMIZATION ON EQUALITY(status, due_date, recipient_id);

-- =========================================================
-- -- 6) AuditLogs (compliance/fraud trail)
-- -- =========================================================
-- CREATE OR REPLACE TABLE athl.audit_logs (
--   log_id        BIGINT         NOT NULL IDENTITY(1,1),
--   user_id       BIGINT         NOT NULL,
--   action_type   STRING         NOT NULL, -- 'purchase','reversal','pause_sales','enable_secondary','airdrop','referral_signup'
--   details       VARIANT,                -- flexible JSON
--   timestamp     TIMESTAMP_TZ   DEFAULT CURRENT_TIMESTAMP(),
--   ip_address    STRING,

--   CONSTRAINT pk_audit_logs PRIMARY KEY (log_id),
--   CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES <SCHEMA>.users(user_id),
--   CONSTRAINT ck_audit_action CHECK (action_type IN ('purchase','reversal','pause_sales','enable_secondary','airdrop','referral_signup'))
-- );

-- ALTER TABLE athl.audit_logs ADD SEARCH OPTIMIZATION ON EQUALITY(action_type, user_id);
