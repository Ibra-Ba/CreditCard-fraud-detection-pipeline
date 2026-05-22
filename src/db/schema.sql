CREATE TABLE IF NOT EXISTS transactions (
    id               SERIAL PRIMARY KEY,
    trans_num        TEXT UNIQUE NOT NULL,
    cc_num           TEXT,
    amt              FLOAT,
    category         TEXT,
    gender           TEXT,
    city_pop         INTEGER,
    lat              FLOAT,
    long             FLOAT,
    merch_lat        FLOAT,
    merch_long       FLOAT,
    dob              TEXT,
    trans_date_trans_time TEXT,
    is_fraud_actual  BOOLEAN,
    is_fraud_pred    BOOLEAN,
    fraud_score      FLOAT,
    created_at       TIMESTAMP DEFAULT NOW()
);

-- index pour les requêtes du rapport quotidien
CREATE INDEX IF NOT EXISTS idx_transactions_created_at
    ON transactions (created_at);

CREATE INDEX IF NOT EXISTS idx_transactions_is_fraud_pred
    ON transactions (is_fraud_pred);