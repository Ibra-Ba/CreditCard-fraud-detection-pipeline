import psycopg2
from psycopg2.extras import RealDictCursor
from src.config import DATABASE_URL


# ── Connexion ────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ── Insert ───────────────────────────────────────────────

def insert_transaction(record: dict) -> None:
    """
    Insère une transaction enrichie de sa prédiction.
    ON CONFLICT ignore les doublons (trans_num unique).
    """
    sql = """
        INSERT INTO transactions (
            trans_num, cc_num, amt, category, gender, city_pop,
            lat, long, merch_lat, merch_long, dob,
            trans_date_trans_time, is_fraud_actual,
            is_fraud_pred, fraud_score
        ) VALUES (
            %(trans_num)s, %(cc_num)s, %(amt)s, %(category)s,
            %(gender)s, %(city_pop)s, %(lat)s, %(long)s,
            %(merch_lat)s, %(merch_long)s, %(dob)s,
            %(trans_date_trans_time)s, %(is_fraud_actual)s,
            %(is_fraud_pred)s, %(fraud_score)s
        )
        ON CONFLICT (trans_num) DO NOTHING;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, record)
        conn.commit()


# ── Queries rapport quotidien ─────────────────────────────

def fetch_yesterday_summary() -> dict:
    """
    Retourne les agrégats du jour précédent pour le rapport Streamlit.
    """
    sql = """
        SELECT
            COUNT(*)                                    AS total_transactions,
            SUM(CASE WHEN is_fraud_pred THEN 1 ELSE 0 END) AS total_frauds,
            ROUND(AVG(amt)::numeric, 2)                 AS avg_amount,
            ROUND(SUM(CASE WHEN is_fraud_pred
                      THEN amt ELSE 0 END)::numeric, 2) AS fraud_amount,
            ROUND(
                100.0 * SUM(CASE WHEN is_fraud_pred THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0), 4
            )                                           AS fraud_rate_pct
        FROM transactions
        WHERE created_at >= NOW() - INTERVAL '1 day';
    """
    with get_connection() as conn:
        with RealDictCursor(conn) as cur:
            cur.execute(sql)
            return dict(cur.fetchone())


def fetch_recent_frauds(limit: int = 50) -> list:
    """
    Retourne les dernières transactions frauduleuses détectées.
    """
    sql = """
        SELECT
            trans_num, amt, category, gender,
            fraud_score, created_at
        FROM transactions
        WHERE is_fraud_pred = TRUE
        ORDER BY created_at DESC
        LIMIT %s;
    """
    with get_connection() as conn:
        with RealDictCursor(conn) as cur:
            cur.execute(sql, (limit,))
            return [dict(row) for row in cur.fetchall()]