import datetime
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.services.feed_service as feed_service
from app.config.thread import init_thread_pool, shutdown_thread_pool
from app.crons import generate_daily_brief
from app.exception import BizException, handle_biz_exception, handle_exception
from app.middleware import LogMiddleware
from app.models.common import success_with_data
from app.models.request import ModifyGroupRequest
from app.models.view_model import (
    FeedBriefListResponse,
    FeedBriefResponse,
    FeedGroupDetailResponse,
    FeedGroupListResponse,
    FeedListResponse,
)

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
    logger.info("Initialize scheduler, thread pool")
    init_thread_pool()
    scheduler.add_job(generate_daily_brief, "cron", hour=0, minute=0)
    scheduler.start()
    yield
    logger.info("Shutdown scheduler, thread pool")
    scheduler.shutdown()
    # Shutdown: Clean up thread pool
    shutdown_thread_pool()


app = FastAPI(lifespan=lifespan)
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
    brief, group = feed_service.get_today_brief()
    brief.group = group
    return success_with_data(brief)


@app.get("/groups", response_model=FeedGroupListResponse)
async def get_all_feed_groups():
    """
    Get all feed groups.
    """
    return success_with_data(feed_service.get_feed_groups())


@app.get("/groups/{group_id}", response_model=FeedGroupDetailResponse)
async def get_feed_group_detail(group_id: int):
    """
    Get the detail of a feed group.
    """
    group = feed_service.get_group_detail(group_id)
    return success_with_data(group)


@app.get("/feeds", response_model=FeedListResponse)
async def get_all_feeds():
    """
    Get all feeds.
    """
    return success_with_data(feed_service.get_all_feeds())


@app.post("/groups")
async def add_group(request: ModifyGroupRequest):
    """
    Add a feed group.
    """
    gid = feed_service.create_group(request.title, request.desc, request.feed_ids)
    return success_with_data(gid)


@app.put("/groups/{group_id}")
async def update_group(group_id: int, request: ModifyGroupRequest):
    """
    Update a feed group.
    """
    feed_service.update_group(group_id, request.title, request.desc, request.feed_ids)
    return success_with_data()


@app.get("/briefs/{group_id}/today", response_model=FeedBriefResponse)
async def get_group_today_brief(group_id: int):
    """
    Get the today brief of a feed group.
    """
    return success_with_data(
        feed_service.get_group_brief(group_id, datetime.date.today())
    )
    
@app.get("/briefs/{group_id}/history", response_model=FeedBriefListResponse)
async def get_history_brief(group_id: int):
    """
    Get the history brief of a feed group.
    """
    return success_with_data(feed_service.get_history_brief(group_id))
