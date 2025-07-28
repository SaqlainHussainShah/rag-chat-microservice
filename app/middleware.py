
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from fastapi.responses import JSONResponse
import os

API_KEY = os.getenv("API_KEY")

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)
        api_key = request.headers.get("X-API-KEY")
        print("API Key ", api_key)
        if api_key != API_KEY:
            return JSONResponse(status_code=401, content={"error": "Invalid API Key"})
        return await call_next(request)