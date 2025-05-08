import logging
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.thread import init_thread_pool, shutdown_thread_pool
from app.crons import generate_daily_brief
from app.exception import BizException, handle_biz_exception, handle_exception
from app.middleware import LogMiddleware
from app.models.common import success_with_data
from app.models.view_model import FeedBriefResponse, FeedGroupListResponse
from app.services import get_today_brief
from app.services.feed_service import get_feed_groups

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Initialize scheduler, thread pool")
    init_thread_pool()
    scheduler.add_job(generate_daily_brief, "cron", hour=0, minute=0)
    scheduler.start()
    yield
    logger.info(f"Shutdown scheduler, thread pool")
    scheduler.shutdown()
    # Shutdown: Clean up thread pool
    shutdown_thread_pool()

app = FastAPI(lifespan=lifespan)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# LOG
app.add_middleware(LogMiddleware)

# Exception Handler
app.add_exception_handler(BizException, handle_biz_exception)
app.add_exception_handler(Exception, handle_exception)

# Scheduler
@app.get("/", response_model=FeedBriefResponse)
async def newest_brief():
    """
    Get the newest brief.
    """
    return success_with_data(get_today_brief())

@app.get("/groups", response_model=FeedGroupListResponse)
async def get_all_feed_groups():
    """
    Get all feed groups.
    """
    return success_with_data(get_feed_groups())
