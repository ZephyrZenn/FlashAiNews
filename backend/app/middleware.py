import json

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            # If the response is not JSON, return it as is
            return response

        wrapped = {
            "code": 0,
            "message": "success",
            "data": payload
        }

        return JSONResponse(content=wrapped, status_code=response.status_code)