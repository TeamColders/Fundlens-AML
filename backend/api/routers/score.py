import logging

import httpx
from fastapi import APIRouter, HTTPException

from backend.core.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("")
def score(payload: dict):
    try:
        response = httpx.post(settings.gnn_score_url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("GNN score failed: %s", exc)
        raise HTTPException(status_code=502, detail="GNN scoring failed") from exc

    return response.json()
