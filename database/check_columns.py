from database.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.begin() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
print("Schema resetado!")