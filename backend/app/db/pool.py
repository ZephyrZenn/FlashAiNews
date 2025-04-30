from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')
host = os.getenv('POSTGRES_HOST')
port = int(os.getenv('POSTGRES_PORT', 5432))
database = os.getenv('POSTGRES_DB')

try:
  pool = ThreadedConnectionPool(minconn=1, maxconn=10,
                                user=user,
                                password=password,
                                host=host,
                                port=port,
                                database=database)
except Exception as e:
  print(f"Error creating connection pool: {e}")
  pool = None


def get_pool() -> ThreadedConnectionPool:
  if not pool:
    raise Exception("Connection pool is not initialized.")
  return pool