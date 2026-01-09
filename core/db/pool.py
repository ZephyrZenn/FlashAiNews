import logging
import os
from contextlib import asynccontextmanager, contextmanager
from typing import Callable
from psycopg import OperationalError
from psycopg_pool import ConnectionPool, AsyncConnectionPool, PoolTimeout

logger = logging.getLogger(__name__)

# 配置 psycopg_pool 的日志，确保能看到详细的连接错误信息
_pool_logger = logging.getLogger("psycopg.pool")
_pool_logger.setLevel(logging.DEBUG)

_sync_pool: ConnectionPool | None = None
_async_pool: AsyncConnectionPool | None = None


def _get_conninfo() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    database = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _get_conninfo_masked() -> str:
    """返回脱敏的连接字符串，用于日志输出"""
    user = os.getenv("POSTGRES_USER")
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    database = os.getenv("POSTGRES_DB")
    return f"postgresql://{user}:***@{host}:{port}/{database}"


def get_pool() -> ConnectionPool | None:
    global _sync_pool
    def check_connection(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    if _sync_pool is None:
        try:
            logger.debug(f"Creating sync connection pool: {_get_conninfo_masked()}")
            _sync_pool = ConnectionPool(
                conninfo=_get_conninfo(),
                min_size=1,
                max_size=10,
                # 1) 借出前健康检查，避免拿到 BAD/closed
                check=check_connection,
                # 2) 空闲回收：避免 idle 被 LB/防火墙断开后留在池里
                max_idle=300,  # 5min，可按环境调 60~900
                # 3) 生命周期轮换：避免长连接偶发失效
                max_lifetime=1800,  # 30min，可按环境调 900~3600
                # 4) 从池里获取连接的等待时间
                timeout=10,  # 秒
                open=True,
            )
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}", exc_info=True)
            return None
    return _sync_pool


@contextmanager
def get_connection(*, autocommit: bool = False):
    """
    autocommit=False：默认事务；正常提交，异常回滚
    autocommit=True ：只读/不需要事务时可用
    """
    pool = get_pool()
    if pool is None:
        raise RuntimeError("Failed to create connection pool")

    try:
        with pool.connection() as conn:
            if autocommit:
                conn.autocommit = True
                yield conn
                return

            try:
                yield conn
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            else:
                conn.commit()

    except (OperationalError, PoolTimeout):
        # 保留原始异常信息，便于定位
        raise


def execute_transaction(call: Callable, *args, **kwargs):
    """Executes a callable with a connection from the pool."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            return call(cur, *args, **kwargs)


# ============ 异步 API ============


async def get_async_pool() -> AsyncConnectionPool | None:
    async def _async_check_connection(conn):
        """连接健康检查：验证连接是否可用"""
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
    global _async_pool
    if _async_pool is None:
        try:
            logger.debug(f"Creating async connection pool: {_get_conninfo_masked()}")
            _async_pool = AsyncConnectionPool(
                conninfo=_get_conninfo(),
                min_size=0,  # 先 0，避免 open 阶段预热卡住
                max_size=10,
                timeout=30,
                check=_async_check_connection,
                max_idle=120,
                max_lifetime=900,
                open=False,
            )
            await _async_pool.open()
        except Exception as e:
            logger.error(f"Error creating async connection pool: {e}", exc_info=True)
            return None
    return _async_pool


@asynccontextmanager
async def get_async_connection(*, autocommit: bool = False):
    """
    autocommit=False：默认事务模式；业务正常则提交，异常回滚
    autocommit=True ：只读/不需要事务时可用，避免无意义 commit
    """
    pool = await get_async_pool()
    if pool is None:
        raise RuntimeError("Failed to create async connection pool")

    try:
        async with pool.connection() as conn:
            # 建议：不要手写 validate_async_connection；交给 pool.check
            # 如果你仍想保留校验，至少要在失败时丢弃连接（见下）

            if autocommit:
                conn.autocommit = True
                yield conn
                return

            try:
                yield conn
            except Exception:
                # 确保异常时回滚
                try:
                    await conn.rollback()
                except Exception:
                    pass
                raise
            else:
                # 正常时提交
                await conn.commit()

    except (OperationalError, PoolTimeout) as e:
        # 这里直接把原异常抛出，别包成 Exception 丢失根因
        raise


async def execute_async_transaction(call: Callable, *args, **kwargs):
    """Executes an async callable with a connection from the pool."""
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            return await call(cur, *args, **kwargs)


# ============ 清理 ============


def close_pool():
    global _sync_pool
    if _sync_pool:
        _sync_pool.close()
        _sync_pool = None


async def close_async_pool():
    global _async_pool
    if _async_pool:
        await _async_pool.close()
        _async_pool = None
