import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from src.config import DATABASE_URL
from sqlalchemy import create_engine


load_dotenv()

# ── Page config ──────────────────────────────────────────

st.set_page_config(
    page_title="CC Fraud Dashboard",
    page_icon=":credit_card:",
    layout="wide",
)

st.title(":credit_card: Credit Card Fraud — Rapport quotidien")
st.caption("Transactions et fraudes détectées — dernières 24h")

# ── Connexion DB ─────────────────────────────────────────

#@st.cache_resource
# ── Engine SQLAlchemy ────────────────────────────────────
ENGINE = create_engine(
    (DATABASE_URL or "").replace("postgresql://", "postgresql+psycopg2://")
)


# ── Queries ──────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_summary() -> dict:
    sql = """
        SELECT
            COUNT(*)                                        AS total_transactions,
            SUM(CASE WHEN is_fraud_pred THEN 1 ELSE 0 END) AS total_frauds,
            ROUND(AVG(amt)::numeric, 2)                     AS avg_amount,
            ROUND(SUM(CASE WHEN is_fraud_pred
                      THEN amt ELSE 0 END)::numeric, 2)     AS fraud_amount,
            ROUND(
                100.0 * SUM(CASE WHEN is_fraud_pred THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0), 4
            )                                               AS fraud_rate_pct
        FROM transactions
        WHERE created_at >= NOW() - INTERVAL '1 day';
    """
    with psycopg2.connect(DATABASE_URL) as conn:
        with RealDictCursor(conn) as cur:
            cur.execute(sql)
            return dict(cur.fetchone())


@st.cache_data(ttl=300)
def load_transactions() -> pd.DataFrame:
    sql = """
        SELECT
            trans_num, amt, category, gender,
            is_fraud_pred, fraud_score, created_at
        FROM transactions
        WHERE created_at >= NOW() - INTERVAL '1 day'
        ORDER BY created_at DESC
        LIMIT 500;
    """
    return pd.read_sql(sql, ENGINE)


@st.cache_data(ttl=300)
def load_fraud_by_category() -> pd.DataFrame:
    sql = """
        SELECT
            category,
            COUNT(*) AS total,
            SUM(CASE WHEN is_fraud_pred THEN 1 ELSE 0 END) AS frauds
        FROM transactions
        WHERE created_at >= NOW() - INTERVAL '1 day'
        GROUP BY category
        ORDER BY frauds DESC;
    """
    return pd.read_sql(sql, ENGINE)

# ── KPIs ─────────────────────────────────────────────────

summary = load_summary()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", int(summary.get("total_transactions") or 0))
col2.metric("Fraudes détectées", int(summary.get("total_frauds") or 0))
col3.metric("Taux de fraude", f"{summary.get('fraud_rate_pct') or 0} %")
col4.metric("Montant fraudé", f"{summary.get('fraud_amount') or 0} €")

st.divider()

# ── Graphiques ───────────────────────────────────────────

df = load_transactions()

if df.empty:
    st.info("Aucune transaction dans les dernières 24h.")
else:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Transactions par heure")
        df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
        hourly = df.groupby("hour").size().reset_index(name="count")
        st.bar_chart(hourly.set_index("hour"))

    with col_right:
        st.subheader("Fraudes par catégorie")
        cat_df = load_fraud_by_category()
        if not cat_df.empty:
            st.bar_chart(cat_df.set_index("category")["frauds"])

    st.divider()

    # ── Tableau transactions récentes ─────────────────────

    st.subheader("Transactions récentes")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        show_fraud_only = st.checkbox("Fraudes uniquement", value=False)
    with col_filter2:
        categories = ["Toutes"] + sorted(df["category"].dropna().unique().tolist())
        selected_cat = st.selectbox("Catégorie", categories)

    filtered = df.copy()
    if show_fraud_only:
        filtered = filtered[filtered["is_fraud_pred"]]
    if selected_cat != "Toutes":
        filtered = filtered[filtered["category"] == selected_cat]

    # colorise les fraudes
    def highlight_fraud(row):
        color = "background-color: #ffcccc" if row["is_fraud_pred"] else ""
        return [color] * len(row)

    st.dataframe(
        filtered[[
            "trans_num", "amt", "category",
            "gender", "fraud_score", "is_fraud_pred", "created_at"
        ]].style.apply(highlight_fraud, axis=1),
        use_container_width=True,
        height=400,
    )