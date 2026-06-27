from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router

app = FastAPI(
    title="Chungbuk Travel AI API",
    description="충북 여행자를 위한 AI 기반 여행 정보 및 옷차림 추천 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://여기에_Amplify주소.amplifyapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}