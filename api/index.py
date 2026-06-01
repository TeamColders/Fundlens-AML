"""
Vercel serverless function entry point for FastAPI backend.
Wraps the FastAPI app with Mangum for Vercel/Lambda compatibility.
"""
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from mangum import Mangum
from backend.api.main import app

handler = Mangum(app, lifespan="off")
