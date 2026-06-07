-- Apply: point issuer_daily_revenue.issuer_id at issuers(issuer_id)
-- Run after reloading corrected CSV data (real issuer_id values).

ALTER TABLE athl_v2.issuer_daily_revenue
  DROP CONSTRAINT IF EXISTS fk_rev_issuer;

ALTER TABLE athl_v2.issuer_daily_revenue
  ADD CONSTRAINT fk_rev_issuer
  FOREIGN KEY (issuer_id) REFERENCES athl_v2.issuers(issuer_id);
