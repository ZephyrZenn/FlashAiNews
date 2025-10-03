import logging
import os
from contextlib import contextmanager
from typing import Callable

from psycopg2 import InterfaceError, OperationalError
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)

# Remove global pool variable
_pool = None


def get_pool():
    global _pool
    if _pool is None:
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        port = int(os.getenv("POSTGRES_PORT", 5432))
        database = os.getenv("POSTGRES_DB")

        try:
            _pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                user=user,
                password=password,
                host=host,
                port=port,
                database=database,
            )
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}", exc_info=True)
            return None
    return _pool


def validate_connection(conn):
    """Check if connection is still valid"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except (OperationalError, InterfaceError):
        return False


@contextmanager
def get_connection():
    """Get a connection from the pool with validation and retry logic"""
    conn = None
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            pool = get_pool()
            if pool is None:
                raise Exception("Failed to create connection pool")

            conn = pool.getconn()

            # Validate connection before use
            if not validate_connection(conn):
                logger.warning(
                    "Invalid connection detected, returning to pool and retrying"
                )
                pool.putconn(conn)
                conn = None
                retry_count += 1
                continue

            try:
                yield conn
                conn.commit()
            except Exception as e:
                if conn and not conn.closed:
                    conn.rollback()
                raise e
            finally:
                if conn and not conn.closed:
                    pool.putconn(conn)
            break  # Success - exit the retry loop

        except (OperationalError, InterfaceError) as e:
            logger.warning(
                f"Database connection error (attempt {retry_count + 1}): {e}"
            )
            if conn:
                try:
                    pool.putconn(conn)
                except:
                    pass
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(
                    "Failed to establish database connection after multiple retries"
                )


def execute_transaction(call: Callable, *args, **kwargs):
    """
    Executes a callable with a connection from the pool.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            return call(cur, *args, **kwargs)
