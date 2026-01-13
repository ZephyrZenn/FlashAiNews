import logging
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import init_agent
from core.config.loader import load_config
from apps.backend.config.thread import init_thread_pool, shutdown_thread_pool
from fastapi.exceptions import RequestValidationError
from apps.backend.exception import (
    BizException,
    handle_biz_exception,
    handle_exception,
    handle_validation_exception,
)
from apps.backend.middleware import LogMiddleware
from apps.backend.models.common import success_with_data
from apps.backend.models.view_model import FeedBriefResponse
from apps.backend.router import brief, feed, group, setting, schedule
from apps.backend.services.scheduler_service import (
    init_scheduler,
    shutdown_scheduler,
    update_schedule_jobs,
)
from apps.backend.services.system_scheduler import (
    init_system_scheduler,
    shutdown_system_scheduler,
)
from core.db.pool import close_async_pool, close_pool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file in development mode
if os.getenv("ENV") == "dev":
    from dotenv import load_dotenv

    load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Start app. Current env: %s", os.getenv("ENV"))
    logger.info("Initialize scheduler, thread pool")
    config = load_config()
    init_thread_pool()
    # Start user scheduler and load all schedules
    init_scheduler()
    update_schedule_jobs()
    # Start system scheduler for maintenance tasks
    init_system_scheduler()
    init_agent()
    yield
    logger.info("Shutdown scheduler, thread pool")
    shutdown_scheduler()
    shutdown_system_scheduler()
    # Shutdown: Clean up thread pool
    shutdown_thread_pool()
    close_pool()
    close_async_pool()


# Router
app = FastAPI(lifespan=lifespan, root_path="/api")
app.include_router(feed.router)
app.include_router(group.router)
app.include_router(brief.router)
app.include_router(setting.router)
app.include_router(schedule.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# LOG
app.add_middleware(LogMiddleware)

# Exception Handler
app.add_exception_handler(RequestValidationError, handle_validation_exception)
app.add_exception_handler(BizException, handle_biz_exception)
app.add_exception_handler(Exception, handle_exception)


@app.get("/", response_model=FeedBriefResponse)
async def newest_brief():
    return success_with_data(None)
