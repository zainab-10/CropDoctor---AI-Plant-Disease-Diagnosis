"""
Video diagnosis for CropDoctor.

A vision-language model is FAR too slow to run on every frame (several seconds
each), so we sample frames at an interval, diagnose each sampled frame, draw the
result onto the frames that follow it, and stitch an annotated output video.

This runs in a background thread with a job/poll API because it is long-running.
"""

import os
import subprocess
import threading
import uuid

import cv2

from . import model_backend

VIDEO_JOBS = {}   # job_id -> status dict


def _encode_h264(src, dst):
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                        "-vcodec", "libx264", "-pix_fmt", "yuv420p", dst], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        import shutil
        shutil.copy(src, dst)


def _wrap(text, width):
    """Naive word-wrap for the overlay caption."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_panel(frame, diag, frame_idx):
    """Draw the latest diagnosis as a caption panel on the frame."""
    h, w = frame.shape[:2]
    healthy = diag.get("healthy") is True
    is_plant = diag.get("is_plant", True)
    if not is_plant:
        title = "Not a plant"
        color = (150, 150, 150)
    elif healthy:
        title = "Healthy"
        color = (90, 210, 90)
    else:
        title = diag.get("diagnosis", "Diagnosis")
        sev = (diag.get("severity") or "").lower()
        color = {"mild": (120, 210, 120), "moderate": (60, 180, 240),
                 "severe": (60, 60, 235)}.get(sev, (60, 180, 240))

    sev_txt = (diag.get("severity") or "").upper()
    conf_txt = (diag.get("confidence") or "").upper()
    sub = " | ".join(x for x in [sev_txt and f"SEVERITY {sev_txt}",
                                 conf_txt and f"CONF {conf_txt}"] if x)

    # translucent panel at the bottom
    ph = 96
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - ph), (w, h), (12, 16, 12), -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
    cv2.rectangle(frame, (0, h - ph), (6, h), color, -1)   # accent bar

    cv2.putText(frame, title[:60], (16, h - ph + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    if sub:
        cv2.putText(frame, sub, (16, h - ph + 56),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 210, 200), 1, cv2.LINE_AA)
    # first line of summary
    summ = diag.get("summary", "")
    if summ:
        line = _wrap(summ, max(30, w // 12))[:1]
        if line:
            cv2.putText(frame, line[0], (16, h - 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (225, 232, 225), 1, cv2.LINE_AA)
    return frame


def _process(job_id, in_path, out_name, out_dir, every_sec):
    try:
        VIDEO_JOBS[job_id]["status"] = "processing"
        cap = cv2.VideoCapture(in_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        step = max(1, int(fps * every_sec))   # diagnose one frame every `every_sec`

        raw = os.path.join(out_dir, f"{job_id}_raw.mp4")
        writer = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

        idx = 0
        last_diag = {"is_plant": True, "healthy": None,
                     "diagnosis": "Analyzing...", "summary": ""}
        samples = []

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                # diagnose this sampled frame
                ok2, buf = cv2.imencode(".jpg", frame)
                if ok2:
                    try:
                        last_diag = model_backend.diagnose(buf.tobytes())
                        samples.append({
                            "t": round(idx / fps, 1),
                            "diagnosis": last_diag.get("diagnosis", ""),
                            "severity": last_diag.get("severity", ""),
                            "healthy": last_diag.get("healthy"),
                        })
                    except Exception as e:
                        last_diag = {"is_plant": True, "healthy": None,
                                     "diagnosis": "Error", "summary": str(e)[:80]}
                VIDEO_JOBS[job_id]["progress"] = round(100 * idx / total)
            writer.write(_draw_panel(frame, last_diag, idx))
            idx += 1

        cap.release(); writer.release()
        final = os.path.join(out_dir, out_name)
        _encode_h264(raw, final)
        try: os.remove(raw)
        except OSError: pass

        VIDEO_JOBS[job_id].update(status="done", output=out_name,
                                  samples=samples, progress=100)
    except Exception as e:
        VIDEO_JOBS[job_id].update(status="error", error=str(e))


def start_job(in_path, out_dir, every_sec=2.0):
    job_id = uuid.uuid4().hex[:12]
    out_name = f"{job_id}_diagnosed.mp4"
    VIDEO_JOBS[job_id] = {"status": "queued", "progress": 0}
    threading.Thread(target=_process,
                     args=(job_id, in_path, out_name, out_dir, every_sec)).start()
    return job_id


def job_status(job_id):
    return VIDEO_JOBS.get(job_id)
