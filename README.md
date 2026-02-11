# AI Image Captioning

A minimal FastAPI + Celery project that generates captions for images using the BLIP model. Submit either a public image URL or upload an image file; the API queues caption jobs to a Celery worker backed by Redis, and you can poll for results.

## Project Structure
- **api/**: FastAPI gateway and Celery client
- **worker/**: Celery worker that downloads the image and produces a caption
- **frontend/**: Placeholder for a UI (currently empty)

## Tech Stack
- **FastAPI** (API gateway)
- **Celery** (task queue)
- **Redis** (broker + result backend)
- **Hugging Face Transformers** with **Salesforce/blip-image-captioning-base**
- **Python** 3.9+

## Prerequisites
- Python 3.9 or newer
- Redis running locally on default port 6379
  - Example (Docker):
    ```bash
    docker run -p 6379:6379 --name redis -d redis:7-alpine
    ```

## Setup
1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn celery redis requests pillow transformers torch
   ```

## Configuration
- By default, Celery is configured to use Redis at `redis://localhost:6379/0` (broker) and `redis://localhost:6379/1` (backend). See:
  - `api/celery_app.py`
  - `worker/celery_app.py`
- If you need to change Redis URLs, update those files accordingly or use environment variables and load them in those modules.

## Running the System
Open two terminals after Redis is running.

1) Start the API (FastAPI):
```bash
uvicorn api.main:app --reload --port 8000
```

2) Start the Celery worker:
```bash
celery -A worker.celery_app.celery worker --pool=solo --loglevel=info
```

## API Endpoints
Base URL: `http://localhost:8000`

- **POST** `/caption`
  - Queues a captioning task for the given image.
  - Provide exactly one of the following:
    - File upload via multipart: form field name `file`
    - Image URL via query string: `image_url`
  - Response:
    ```json
    { "task_id": "<celery_task_id>" }
    ```

- **GET** `/result/{task_id}`
  - Polls for the task result.
  - Possible responses:
    ```json
    { "state": "PENDING" }
    ```
    ```json
    { "state": "SUCCESS", "result": { "caption": "a caption...", "width": 123, "height": 456 } }
    ```
    Other Celery states may be returned as `{ "state": "<STATE>" }`.

## Usage Examples
- Create a captioning task (file upload):
  ```bash
  curl -X POST http://localhost:8000/caption \
       -H "Content-Type: multipart/form-data" \
       -F "file=@/path/to/local/image.jpg"
  ```
  Response:
  ```json
  { "task_id": "c9422f5e-..." }
  ```

- Create a captioning task (image URL via query):
  ```bash
  curl -X POST "http://localhost:8000/caption?image_url=https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e"
  ```
  Response:
  ```json
  { "task_id": "c9422f5e-..." }
  ```

- Poll for the result:
  ```bash
  curl http://localhost:8000/result/c9422f5e-...
  ```
  Example success response:
  ```json
  {
    "state": "SUCCESS",
    "result": {
      "caption": "a portrait of a woman with flowers",
      "width": 4000,
      "height": 6000
    }
  }
  ```

## Notes
- If you send a URL, the worker downloads the image; ensure the URL is publicly accessible and returns an image in a common format (JPEG/PNG).
- If you upload a file, it is transmitted as base64 to the worker internally.
- First inference will download model weights; the initial request may take longer.
- For production, consider setting timeouts, retries, and moving configuration to environment variables.
