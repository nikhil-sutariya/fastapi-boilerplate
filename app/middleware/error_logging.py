from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_time = datetime.utcnow()
        client_ip = request.client.host

        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            logger.error(
                f"\n[Unhandled Exception] {request.method} {request.url}\n"
                f"Time: {request_time.isoformat()} UTC\n"
                f"IP: {client_ip}\n"
                f"Headers: {dict(request.headers)}\n"
                f"Error: {str(exc)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )
