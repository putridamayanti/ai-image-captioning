# api_gateway/main.py
from fastapi import FastAPI
from pydantic import BaseModel

from celery_app import celery

app = FastAPI()

class CaptionRequest(BaseModel):
    image_url: str

@app.post("/caption")
def create_caption(req: CaptionRequest):
    task = celery.send_task(
        "caption.generate",
        args=[req.image_url],
    )
    return {"task_id": task.id}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = celery.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"state": "PENDING"}

    if result.state == "SUCCESS":
        return {"state": "SUCCESS", "result": result.result}

    return {"state": result.state}
