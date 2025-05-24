import logging
from contextlib import asynccontextmanager
import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.llm import close_config_watcher, init_llm_config
import app.services.brief_service as brief_service
from app.config.thread import init_thread_pool, shutdown_thread_pool
from app.crons import generate_daily_brief
from app.exception import BizException, handle_biz_exception, handle_exception
from app.middleware import LogMiddleware
from app.models.common import success_with_data
from app.models.view_model import FeedBriefResponse
from app.router import brief, feed, group, setting
from app.services import group_service, retrieve_and_generate_brief
from app.utils.thread_utils import submit_to_thread

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Start app. Current env: %s", os.getenv("ENV"))
    logger.info("Initialize scheduler, thread pool")
    init_thread_pool()
    init_llm_config()
    scheduler.add_job(generate_daily_brief, "cron", hour=0, minute=0)
    scheduler.start()
    yield
    logger.info("Shutdown scheduler, thread pool")
    scheduler.shutdown()
    # Shutdown: Clean up thread pool
    shutdown_thread_pool()
    close_config_watcher()


# Router
app = FastAPI(lifespan=lifespan, root_path="/api")
app.include_router(feed.router)
app.include_router(group.router)
app.include_router(brief.router)
app.include_router(setting.router)

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
app.add_exception_handler(BizException, handle_biz_exception)
app.add_exception_handler(Exception, handle_exception)


@app.get("/", response_model=FeedBriefResponse)
async def newest_brief():
    """
    Get the newest brief.
    """
    brief = brief_service.get_today_brief()
    if not brief:
        submit_to_thread(retrieve_and_generate_brief)
        return success_with_data(None)
    group = group_service.get_group_detail(brief.group_id)
    return success_with_data(brief.to_view_model(group))
