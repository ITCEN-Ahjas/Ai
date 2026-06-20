# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Travel AI API")

@app.get("/health")
def health():
    return {"status": "ok"}