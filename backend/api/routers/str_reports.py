import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.llm.str_generator import generate_str


router = APIRouter()


@router.post("/{case_id}/generate")
async def generate_str_report(case_id: str):
    async def event_stream():
        yield _event({
            "stage": "analysing_pattern",
            "message": "Extracting subgraph from Neo4j...",
            "progress": 20,
        })
        await asyncio.sleep(0.2)
        yield _event({
            "stage": "compiling_evidence",
            "message": "Assembling case evidence...",
            "progress": 50,
        })
        await asyncio.sleep(0.2)
        yield _event({
            "stage": "drafting_narrative",
            "message": "LLM drafting STR narrative...",
            "progress": 75,
        })

        task = asyncio.create_task(generate_str({"case_id": case_id}))
        while not task.done():
            yield ": keep-alive\n\n"
            await asyncio.sleep(15)

        report = await task
        yield _event({
            "stage": "complete",
            "message": "STR ready for review",
            "progress": 100,
            "report": report,
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"
