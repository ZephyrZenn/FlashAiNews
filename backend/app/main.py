from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.common import success_with_data
from app.models.view_model import FeedBriefVO, FeedBriefResponse
from app.services import get_newest_brief

app = FastAPI()
# CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=FeedBriefResponse)
async def newest_brief():
    """
    Get the newest brief.
    """
    return success_with_data(get_newest_brief())
