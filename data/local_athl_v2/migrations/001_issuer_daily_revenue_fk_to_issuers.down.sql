-- Rollback: restore FK to users(user_id) for pre-fix data (issuer_id column held user_id values).

ALTER TABLE athl_v2.issuer_daily_revenue
  DROP CONSTRAINT IF EXISTS fk_rev_issuer;

ALTER TABLE athl_v2.issuer_daily_revenue
  ADD CONSTRAINT fk_rev_issuer
  FOREIGN KEY (issuer_id) REFERENCES athl_v2.users(user_id);
