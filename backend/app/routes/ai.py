# backend/app/routes/ai.py
from pathlib import Path
import json
import logging

import httpx
from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI

from app.config.settings import settings
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.routes.mcp_server import MCPRequest
from app.schemas.ai import AIMessage, AIMessages
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])

_IMPROVE_PROMPT_PATH = Path(__file__).with_name("ImproveDiaryNoteSystemPrompt.md")
_AI_PROMPT_PATH = Path(__file__).with_name("AIAnswerSystemPrompt.md")


def _load_system_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"{path.name} file is missing") from exc


system_message = {
    "role": "system",
    "content": _load_system_prompt(_IMPROVE_PROMPT_PATH),
}

mcp_system_message = {
    "role": "system",
    "content": _load_system_prompt(_AI_PROMPT_PATH),
}


@router.post("/improve", response_model=DiaryEntryUpdate, status_code=201)
def improve_note(entry_data: DiaryEntryCreate):
    client = OpenAI(api_key=settings.GROK_API_KEY, base_url=settings.GROK_BASE_URL)
    chat_completion = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[
            system_message,
            {"role": "user", "content": f"Improve this diary entry:\n\n{entry_data.raw_text}"},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    new_entry = DiaryEntryUpdate(
        raw_text=entry_data.raw_text,
        improved_text=chat_completion.choices[0].message.content,
        is_improved=True,
    )

    return new_entry


def build_payload(user_message: AIMessage) -> dict:
    schema = MCPRequest.model_json_schema()
    required_fields = ["from_date", "to_date"]
    return {
        "model": settings.AI_MODEL,
        "messages": [
            mcp_system_message,
            {"role": user_message.role, "content": user_message.content},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "searchDiaryEntryTool",
                    "description": "Finds diary entries based on date range and search query",
                    "parameters": {
                        "type": "object",
                        "properties": schema["properties"],
                        "required": required_fields,
                    },
                },
            }
        ],
        "tool_choice": "auto",
    }


def call_search_tool(args: dict) -> dict:
    url = f"{settings.API_ROOT}/tools/searchDiaryEntryTool"
    response = httpx.post(url, json=args, timeout=10.0)
    response.raise_for_status()
    return response.json()


@router.post("/answer", response_model=AIMessages, status_code=201)
def answer_query(
    query_request: AIMessages,
    current_user: User = Depends(get_current_user),
):
    client = OpenAI(api_key=settings.GROK_API_KEY, base_url=settings.GROK_BASE_URL)
    user_msg = query_request.messages[-1]
    logger.info("Answering query for user %s (message role=%s)", current_user.id, user_msg.role)

    response = client.chat.completions.create(**build_payload(user_msg))
    message = response.choices[0].message

    tool_calls = message.tool_calls or []
    if tool_calls:
        tool_call = tool_calls[0]
        if tool_call.function.name != "searchDiaryEntryTool":
            raise HTTPException(
                status_code=400,
                detail=f"Unexpected tool call: {tool_call.function.name}",
            )

        try:
            args_dict = json.loads(tool_call.function.arguments)
        except Exception as exc:
            logger.error("Invalid tool arguments: %s", exc)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid arguments for tool: {exc}",
            ) from exc

        args_dict["user_id"] = str(current_user.id)
        logger.debug("Calling searchDiaryEntryTool for user %s with %s", current_user.id, args_dict)
        tool_result = call_search_tool(args_dict)
        logger.debug("searchDiaryEntryTool returned %d entries", len(tool_result or []))

        follow_up_payload = build_payload(user_msg)
        follow_up_payload["messages"] = [
            mcp_system_message,
            {"role": user_msg.role, "content": user_msg.content},
            {
                "role": "function",
                "name": "searchDiaryEntryTool",
                "content": json.dumps(tool_result),
            },
        ]
        follow_up = client.chat.completions.create(**follow_up_payload)
        final_content = follow_up.choices[0].message.content or ""
        logger.info("Appending assistant response after tool call (length=%d)", len(final_content))
        query_request.messages.append(AIMessage(role="assistant", content=final_content))
    else:
        plain_content = message.content or ""
        logger.info("Appending assistant direct response (length=%d)", len(plain_content))
        query_request.messages.append(AIMessage(role="assistant", content=plain_content))

    return query_request
