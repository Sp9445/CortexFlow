from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
import os
from app.config.settings import settings
from app.schemas.diary_entry import (
    DiaryEntryCreate,
    DiaryEntryUpdate,   
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)

system_message = {
    "role": "system",
    "content": (
        "You are an AI writing assistant specialized in improving personal diary entries. "
        "Your task is to refine the user's raw text by improving clarity, grammar, and sentence flow, "
        "while making the text more structured, formatted, and reading-friendly. "
        "Break long paragraphs into natural sections where appropriate. "
        "Strictly preserve the original emotional tone and personal voice. "
        "Do not add new facts, do not change the meaning, and do not make it sound formal, academic, or like an essay. "
        "Keep the improved version natural, as if the user themselves thoughtfully revised it. "
        "Use short, natural paragraphs and improve sentence rhythm and readability. "
        "Return only the improved diary entry."
    )
}

@router.post(
    "/improve",
    response_model=DiaryEntryUpdate,
    status_code=201
)
def improve_note(entry_data: DiaryEntryCreate):
    client = OpenAI(
        api_key=settings.GROK_API_KEY,
        base_url=settings.GROK_BASE_URL,
    )

    chat_completion = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[
            system_message,
            {"role": "user", "content": f"Improve this diary entry:\n\n{entry_data.raw_text}"}
        ],
        temperature=0.7,
        max_tokens=500
    )

    new_entry = DiaryEntryUpdate(
        raw_text=entry_data.raw_text,
        improved_text= chat_completion.choices[0].message.content,
        is_improved=True
    ) 

    return new_entry
