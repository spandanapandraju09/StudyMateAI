import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.services.ai_service import chat_completion

router = APIRouter(tags=["openai_compat"])


async def _process_completion(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    messages = data.get("messages", [])
    model = data.get("model", "aira-os")

    formatted_messages = []
    if isinstance(messages, list):
        for m in messages:
            if isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content", "")
                if content:
                    formatted_messages.append({"role": role, "content": str(content)})

    if not formatted_messages:
        formatted_messages = [{"role": "user", "content": "Hello"}]

    try:
        reply = chat_completion(
            messages=formatted_messages,
            persona_key="friendly_buddy",
            mood="neutral",
            memories=[],
            notes="",
        )
    except Exception as e:
        reply = f"Hello! I am AIRA — your AI Operating System. How can I help you today? (Note: {str(e)})"

    prompt_words = sum(len(m["content"].split()) for m in formatted_messages)
    comp_words = len(reply.split())

    response_payload = {
        "id": f"chatcmpl-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": max(1, prompt_words),
            "completion_tokens": max(1, comp_words),
            "total_tokens": max(2, prompt_words + comp_words),
        },
    }
    return JSONResponse(content=response_payload, status_code=200)


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
@router.post("/api/chat/completions")
@router.post("/api/v1/chat/completions")
async def chat_completions_endpoint(request: Request):
    return await _process_completion(request)
