from fastapi import APIRouter


router = APIRouter()


@router.post("")
def run_query(payload: dict):
    return {
        "message": "Query processing placeholder",
        "query": payload,
    }
