CREATE TABLE IF NOT EXISTS sourced_history (
 id TEXT PRIMARY KEY,source_name TEXT NOT NULL,source_url TEXT NOT NULL,source_sha256 TEXT NOT NULL,
 license TEXT NOT NULL,platform_id TEXT NOT NULL REFERENCES platforms(id),external_product_id TEXT,
 product_url TEXT NOT NULL,title TEXT NOT NULL,price INTEGER NOT NULL CHECK(price>0),
 observed_at_reported TEXT NOT NULL,timezone TEXT,attributes TEXT NOT NULL,
 verification TEXT NOT NULL DEFAULT 'external_unverified',imported_at TEXT NOT NULL,
 UNIQUE(source_url,platform_id,product_url,observed_at_reported,price,title)
);
CREATE INDEX IF NOT EXISTS sourced_history_url ON sourced_history(product_url,observed_at_reported);
