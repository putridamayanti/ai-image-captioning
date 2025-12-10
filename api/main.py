# api_gateway/main.py
import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from celery_app import celery

app = FastAPI()

class CaptionRequest(BaseModel):
    image_url: str

@app.post("/caption")
async def create_caption(file: Optional[UploadFile] = File(None), image_url: Optional[str] = None):
    if not file and not image_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either file or image_url is required")

    target_arg = None

    if file:
        target_dir = Path("caption")
        target_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(file.filename).suffix
        filename = file.filename
        file_path = target_dir / filename

        content = await file.read()

        b64_image = base64.b64encode(content).decode()

        target_arg = b64_image
    else:
        target_arg = image_url


    task = celery.send_task(
        "caption.generate",
        args=[target_arg],
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
