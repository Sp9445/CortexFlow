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
    try:
        response = httpx.post(url, json=args, timeout=20.0)
        response.raise_for_status()
        return response.json()
    except httpx.ReadTimeout as exc:
        logger.error("Diary search tool timed out for args=%s", args, exc_info=exc)
        raise HTTPException(status_code=504, detail="Diary lookup timed out") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Diary search tool returned %s for args=%s", exc.response.status_code, args, exc_info=exc)
        raise HTTPException(status_code=exc.response.status_code, detail="Diary lookup failed") from exc


@router.post("/answer", response_model=AIMessages, status_code=201)
def answer_query(
    query_request: AIMessages,
    current_user: User = Depends(get_current_user),
):
    client = OpenAI(api_key=settings.GROK_API_KEY, base_url=settings.GROK_BASE_URL)
    user_msg = query_request.messages[-1]
    logger.info("Answering query for user %s (message role=%s)", current_user.id, user_msg.role)

    payload = build_payload(user_msg)
    logger.debug(
        "Sending Grok payload for user %s (model=%s, tool_choice=%s, prompt_length=%d)",
        current_user.id,
        payload.get("model"),
        payload.get("tool_choice"),
        len(user_msg.content or ""),
    )

    try:
        response = client.chat.completions.create(**payload)
    except Exception as exc:
        logger.exception("Grok completion failed for user %s", current_user.id)
        raise HTTPException(status_code=502, detail="AI service unavailable") from exc

    if not response.choices:
        logger.warning("Grok returned no choices for user %s", current_user.id)
        raise HTTPException(status_code=502, detail="AI returned empty response")

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

        args_dict["query"] = args_dict.get("query") or ""
        args_dict["user_id"] = str(current_user.id)
        logger.info("Dispatching searchDiaryEntryTool for user %s", current_user.id)
        logger.debug("searchDiaryEntryTool args: %s", args_dict)
        tool_result = call_search_tool(args_dict)
        logger.info("searchDiaryEntryTool returned %d entries for user %s", len(tool_result or []), current_user.id)

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
        logger.debug(
            "Sending follow-up payload with tool result for user %s (messages=%d)",
            current_user.id,
            len(follow_up_payload["messages"]),
        )
        follow_up = client.chat.completions.create(**follow_up_payload)
        final_content = follow_up.choices[0].message.content or ""
        logger.info(
            "Appending assistant response after tool call (length=%d) for user %s",
            len(final_content),
            current_user.id,
        )
        logger.debug("Assistant final snippet: %s", final_content[:200])
        query_request.messages.append(AIMessage(role="assistant", content=final_content))
    else:
        plain_content = message.content or ""
        logger.info("Appending assistant direct response (length=%d) for user %s", len(plain_content), current_user.id)
        logger.debug("Assistant direct snippet: %s", plain_content[:200])
        query_request.messages.append(AIMessage(role="assistant", content=plain_content))

    return query_request
