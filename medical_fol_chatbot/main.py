from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import json
from logic import InferenceEngine

app = FastAPI()

# Load Knowledge Base
with open("kb.json", "r", encoding="utf-8") as f:
    kb_data = json.load(f)

engine = InferenceEngine(kb_data)

templates = Jinja2Templates(directory="templates")

class DiagnosisRequest(BaseModel):
    symptoms: List[str]
    mode: str = "forward"
    goal: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/diagnose")
async def diagnose(request: DiagnosisRequest):
    if request.mode == "forward":
        results = engine.forward_chaining(request.symptoms)
        return {"results": results}
    else:
        if not request.goal:
            raise HTTPException(status_code=400, detail="Goal required for backward")
        result = engine.backward_chaining(request.symptoms, request.goal)
        return {"results": [result]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
