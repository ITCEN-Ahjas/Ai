from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, SuggestRequest, SuggestResponse
from app.services.chat_service import chat, suggest_questions

router = APIRouter()

@router.post("", response_model=ChatResponse)
def chat_endpoint(body: ChatRequest):
    try:
        reply = chat(body.message, body.history)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest", response_model=SuggestResponse)
def suggest_endpoint(body: SuggestRequest):
    try:
        questions = suggest_questions(body.message, body.reply)
        return SuggestResponse(questions=questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
