from fastapi import FastAPI

from app.middleware import ResponseWrapperMiddleware
from app.services import get_newest_brief

app = FastAPI()
app.add_middleware(ResponseWrapperMiddleware)

@app.get("/")
async def newest_brief():
    return get_newest_brief()
