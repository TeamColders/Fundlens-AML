"""
Vercel serverless function entry point for FastAPI backend.
Wraps the FastAPI app with Mangum for Vercel/Lambda compatibility.
"""
import logging
import sys
import traceback

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from mangum import Mangum
    from backend.api.main import app

    handler = Mangum(app, lifespan="off")
    logger.info("App loaded successfully")

except Exception as e:
    logger.error("STARTUP IMPORT ERROR: %s", traceback.format_exc())

    # Return a minimal ASGI app that reports the import error
    from fastapi import FastAPI
    _error_app = FastAPI()
    _error_detail = traceback.format_exc()

    @_error_app.get("/{path:path}")
    @_error_app.post("/{path:path}")
    async def startup_error(path: str):
        return {"error": "Startup failed", "detail": _error_detail}

    handler = Mangum(_error_app, lifespan="off")
#comment