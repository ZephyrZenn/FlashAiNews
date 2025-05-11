from contextlib import contextmanager
from typing import Callable
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = int(os.getenv("POSTGRES_PORT", 5432))
database = os.getenv("POSTGRES_DB")

try:
    pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
except Exception as e:
    print(f"Error creating connection pool: {e}")
    pool = None


@contextmanager
def get_connection():
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        pool.putconn(conn)


def execute_transaction(call: Callable, *args, **kwargs):
    """
    Executes a callable with a connection from the pool.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            return call(cur, *args, **kwargs)
