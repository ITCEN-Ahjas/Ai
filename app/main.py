from fastapi import FastAPI
from app.api.v1.router import router

app = FastAPI(title="Travel AI API")
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
