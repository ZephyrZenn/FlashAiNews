import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log requests and responses.
    """

    async def dispatch(self, request: Request, call_next):
        logger.info(
            f"Request Path: {request.url.path}. Param: {request.query_params}. Method: {request.method}. Headers: {request.headers}. Body: {await request.body()}")
        response = await call_next(request)

        return response
