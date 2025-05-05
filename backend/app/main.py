import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exception import BizException, handle_biz_exception, handle_exception
from app.middleware import LogMiddleware
from app.models.common import success_with_data
from app.models.view_model import FeedBriefResponse
from app.services import get_today_brief

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

app = FastAPI()
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


@app.get("/", response_model=FeedBriefResponse)
async def newest_brief():
    """
    Get the newest brief.
    """
    return success_with_data(get_today_brief())
