
import psycopg2
from src.config import DATABASE_URL

with psycopg2.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        with open('src/db/schema.sql') as f:
            cur.execute(f.read())
    conn.commit()
    print('Table transactions créée.')
