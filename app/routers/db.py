import os
import psycopg2
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(tags=["PostgreSQL Database"])


def get_db_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


@router.get("/db/health")
def db_health():
    try:
        conn = get_db_conn()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@router.get("/db/tables")
def list_tables(schema: str = Query(default="app", description="Database schema name")):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s ORDER BY table_name
        """, (schema,))
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return {"schema": schema, "tables": tables}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
