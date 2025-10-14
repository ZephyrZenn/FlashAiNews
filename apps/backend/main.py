import logging
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import apps.backend.services.brief_service as brief_service
from core.config.loader import load_config
from apps.backend.config.thread import init_thread_pool, shutdown_thread_pool
from apps.backend.exception import BizException, handle_biz_exception, handle_exception
from apps.backend.middleware import LogMiddleware
from apps.backend.models.common import success_with_data
from apps.backend.models.view_model import FeedBriefResponse
from apps.backend.router import brief, feed, group, setting
from apps.backend.services import group_service, retrieve_and_generate_brief
from apps.backend.services.scheduler_service import shutdown_scheduler, start_scheduler
from apps.backend.utils.thread_utils import submit_to_thread

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
    start_scheduler(config.brief_time)
    yield
    logger.info("Shutdown scheduler, thread pool")
    shutdown_scheduler()
    # Shutdown: Clean up thread pool
    shutdown_thread_pool()


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
