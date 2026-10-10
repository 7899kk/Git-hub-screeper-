CREATE TABLE IF NOT EXISTS provider_history(provider TEXT NOT NULL,product_key TEXT NOT NULL,fetched_at REAL NOT NULL,series TEXT NOT NULL,PRIMARY KEY(provider,product_key));
