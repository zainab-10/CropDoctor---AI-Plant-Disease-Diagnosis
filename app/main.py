"""
CropDoctor — FastAPI backend.

  GET  /               -> web UI
  GET  /api/health     -> backend + model info
  POST /api/diagnose   -> image -> structured diagnosis JSON
  POST /api/followup   -> image + question + prior_summary -> text answer
"""

import os
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

from . import config, model_backend, video

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE, "video_outputs")
UPLOAD_DIR = os.path.join(BASE, "video_uploads")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="CropDoctor", version="1.0")


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(BASE, "templates", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
def health():
    info = model_backend.backend_info()
    info["status"] = "ok"
    return info


def _read_image(image: UploadFile, data: bytes):
    max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(413, f"Image exceeds {config.MAX_UPLOAD_MB} MB limit.")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Please upload an image file.")


@app.post("/api/diagnose")
async def diagnose(image: UploadFile = File(...)):
    data = await image.read()
    _read_image(image, data)
    try:
        result = model_backend.diagnose(data)
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": str(e)})
    return {"result": result, **model_backend.backend_info()}


@app.post("/api/followup")
async def followup(image: UploadFile = File(...),
                   question: str = Form(...),
                   prior_summary: str = Form("")):
    if not question.strip():
        raise HTTPException(400, "Question is empty.")
    data = await image.read()
    _read_image(image, data)
    try:
        answer = model_backend.followup(data, question.strip(), prior_summary)
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": str(e)})
    return {"answer": answer}


# ---------------------------------------------------------------- video
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


@app.post("/api/diagnose_video")
async def diagnose_video(video_file: UploadFile = File(...),
                         every_sec: float = Form(2.0)):
    ext = os.path.splitext(video_file.filename)[1].lower()
    if ext not in VIDEO_EXT:
        raise HTTPException(400, "Please upload a video file (mp4, mov, avi, mkv, webm).")
    data = await video_file.read()
    if len(data) > 200 * 1024 * 1024:
        raise HTTPException(413, "Video exceeds 200 MB limit.")
    # clamp sampling interval to a sane range
    every_sec = max(0.5, min(10.0, float(every_sec)))

    in_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}{ext}")
    with open(in_path, "wb") as f:
        f.write(data)

    job_id = video.start_job(in_path, OUTPUT_DIR, every_sec=every_sec)
    return {"job_id": job_id}


@app.get("/api/video_status/{job_id}")
def video_status(job_id: str):
    job = video.job_status(job_id)
    if not job:
        raise HTTPException(404, "Unknown job")
    resp = dict(job)
    if job.get("status") == "done":
        resp["video_url"] = f"/api/video_result/{job['output']}"
    return resp


@app.get("/api/video_result/{filename}")
def video_result(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    return FileResponse(path, media_type="video/mp4")
