from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings

_EXCLUDED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Always allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow health/docs without auth
        if request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        # If no key configured, allow all (local dev)
        if not settings.api_key:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
