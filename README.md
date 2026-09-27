<<<<<<< HEAD
# CropDoctor — AI Plant Disease Diagnosis

Photograph a crop leaf and an AI agronomist (**Qwen3-VL**, a pretrained
vision-language model — *no training, no dataset*) identifies the likely disease,
its severity, and gives treatment + prevention advice a farmer can act on. You can
then ask follow-up questions about the same plant.

**Stack:** FastAPI · Qwen3-VL (multimodal) · vanilla-JS report UI · Docker.

## How it works (no model training)

Instead of training a disease classifier, a carefully structured prompt turns a
general vision-language model into a crop advisor and forces it to return **strict
JSON** (disease, severity, symptoms, causes, treatment, prevention). The frontend
renders that JSON as a clean report. Swapping in a newer VLM is a one-line env change.

```
Browser ──► FastAPI /api/diagnose ──► model_backend.diagnose()
                                        ├─ api   → Hugging Face InferenceClient
                                        └─ local → transformers + torch on GPU
```

## Two modes (one image, switch by env var)

| Mode  | Runs on | Needs |
|-------|---------|-------|
| `api`   | Hugging Face hosted inference (Qwen3-VL-8B) | free HF token, no GPU |
| `local` | Qwen3-VL-4B in the container | NVIDIA GPU (8 GB ok) |

## Quick start (Docker)

**API mode (easiest, no GPU):**
1. Free HF token (read scope): https://huggingface.co/settings/tokens
2. `cp .env.example .env` and paste the token.
3. `docker compose --profile api up --build`
4. Open http://localhost:8000

**Local GPU mode (offline):** needs NVIDIA Container Toolkit on the host.
```
=======
<div align="center">

# 🌿 CropDoctor — AI Plant Disease Diagnosis

**Photograph a crop leaf and an AI agronomist tells you what's wrong, how severe it is, and what to do about it.**

[![Live Demo](https://img.shields.io/badge/🤗%20Hugging%20Face-Live%20Demo-yellow)](https://huggingface.co/spaces/zainab28/cropdoctor)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](#quick-start-docker)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

**[🚀 Try it live on Hugging Face Spaces](https://huggingface.co/spaces/zainab28/cropdoctor)** — no install needed

</div>

---

## 🌱 Overview

CropDoctor turns a general-purpose **vision-language model (Qwen3-VL)** into a crop advisor — **no dataset, no training, no fine-tuning**. Upload a photo of a leaf and it identifies whether the plant is healthy or suffering from a disease, deficiency, or pest, then returns a structured report: summary, severity, confidence, symptoms, causes, treatment, and prevention. You can also ask follow-up questions about the same plant, and it supports diagnosing frame-by-frame from a short video clip.

## ✨ Features

- 📸 **Image diagnosis** — upload a leaf photo, get a structured JSON report rendered as a clean UI
- 💬 **Follow-up Q&A** — ask a further question about the same plant/image, grounded in the prior diagnosis
- 🎞️ **Video diagnosis** — upload a short clip; it samples frames at a configurable interval and diagnoses each
- ⚙️ **Two swappable backends** — hosted Hugging Face inference (no GPU needed) or a local GPU model, toggled by one env var
- 🐳 **Dockerized** — one command to run either mode
- ⚠️ **Honest framing** — clearly presented as an advisory/triage tool, not a lab-certified diagnosis

## 🎬 Demo

https://drive.google.com/file/d/1bavC7pxRNE1iXtpHpGtJf9y5EQoEIAM2/view?usp=sharing

> Drag `crop_doctor_demo.mp4` directly into a new GitHub issue or the README editor on github.com — it'll host the file and give you an embeddable `user-attachments` link. Paste that link in place of the placeholder above (plain `.mp4` links don't render inline in Markdown).

## 🧠 How It Works

```
Browser ──► FastAPI /api/diagnose ──► model_backend.diagnose()
                                         ├─ api   → Hugging Face InferenceClient (Qwen3-VL-8B)
                                         └─ local → transformers + torch on GPU (Qwen3-VL-4B)
```

Rather than training a disease classifier, a carefully engineered prompt (`app/prompts.py`) constrains the vision-language model to reason like an agronomist and return **strict JSON**. The frontend renders that JSON as a report. Swapping in a newer VLM later is a one-line config change — no retraining.

| Mode | Runs on | Needs |
|---|---|---|
| `api` | Hugging Face hosted inference (Qwen3-VL-8B) | Free HF token, no GPU |
| `local` | Qwen3-VL-4B inside the container | NVIDIA GPU (8 GB+) |

## 🧩 Tech Stack

- **Backend:** FastAPI
- **Model:** Qwen3-VL (multimodal vision-language model), via Hugging Face Inference API or local `transformers`/`torch`
- **Frontend:** Vanilla JS report UI (`app/templates/index.html`)
- **Deployment:** Docker + Docker Compose, live on Hugging Face Spaces

## ⚡ Quick Start (Docker)

**API mode — easiest, no GPU required:**
```bash
git clone https://github.com/<your-username>/cropdoctor.git
cd cropdoctor
cp .env.example .env
```
Then edit `.env` and paste in a free [Hugging Face token](https://huggingface.co/settings/tokens) (read scope):
```
HF_TOKEN=hf_your_token_here
```
```bash
docker compose --profile api up --build
```
Open **http://localhost:8000**.

**Local GPU mode — fully offline:** requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on the host.
```bash
>>>>>>> 8dc34ea905c1bba5abd34de0ed4813a03690b3d5
docker compose --profile local up --build
```
First run downloads Qwen3-VL-4B (~8 GB) into `./models`.

<<<<<<< HEAD
## Run without Docker (dev)
```
=======
## 🛠 Run Without Docker (dev)

```bash
>>>>>>> 8dc34ea905c1bba5abd34de0ed4813a03690b3d5
pip install -r requirements.txt          # + requirements-local.txt for local mode
export MODEL_BACKEND=api                  # or local
export HF_TOKEN=hf_xxx                     # api mode only
uvicorn app.main:app --reload --port 8000
```
<<<<<<< HEAD
(PowerShell: `$env:MODEL_BACKEND="api"`, etc.)

## API
- `POST /api/diagnose` — `image` file → structured diagnosis JSON
- `POST /api/followup` — `image` + `question` + `prior_summary` → text answer
- `GET  /api/health` — active backend + model

## Layout
```
cropdoctor/
├── app/
│   ├── main.py           # FastAPI routes
│   ├── model_backend.py  # api/local inference + JSON recovery
│   ├── prompts.py        # the domain prompt (turns a VLM into a crop doctor)
│   ├── config.py
│   └── templates/index.html
├── requirements.txt / requirements-local.txt
├── Dockerfile / docker-compose.yml / .env.example
```

## Honest note
A VLM's plant-disease advice is knowledgeable but not lab-certified — this is an
advisory/triage tool. The UI shows a disclaimer to confirm critical decisions with
a local expert. That framing is deliberate and part of responsible design.
=======
PowerShell: `$env:MODEL_BACKEND="api"`, `$env:HF_TOKEN="hf_xxx"`

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Web UI |
| `/api/health` | GET | Active backend + model info |
| `/api/diagnose` | POST | `image` file → structured diagnosis JSON |
| `/api/followup` | POST | `image` + `question` + `prior_summary` → text answer |
| `/api/diagnose_video` | POST | `video_file` + `every_sec` → starts an async diagnosis job, returns `job_id` |
| `/api/video_status/{job_id}` | GET | Poll job status; includes `video_url` when done |
| `/api/video_result/{filename}` | GET | Fetch the processed result video |

## 📁 Project Structure
```
cropdoctor/
├── app/
│   ├── main.py            # FastAPI routes (image, follow-up, video)
│   ├── model_backend.py   # api/local inference + JSON recovery
│   ├── prompts.py         # the domain prompt — turns a VLM into a crop doctor
│   ├── video.py            # frame sampling + async video job handling
│   ├── config.py
│   └── templates/index.html
├── requirements.txt / requirements-local.txt
├── Dockerfile / docker-compose.yml
├── .env.example             # copy to .env — never commit .env itself
```

## 🔐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_BACKEND` | `api` | `api` (hosted inference) or `local` (in-container GPU model) |
| `HF_TOKEN` | — | Required for `api` mode — [get a free token](https://huggingface.co/settings/tokens) |
| `HF_API_MODEL` | `Qwen/Qwen3-VL-8B-Instruct` | Model used in API mode |
| `LOCAL_MODEL` | `Qwen/Qwen3-VL-4B-Instruct` | Model used in local GPU mode |
| `MAX_NEW_TOKENS` | `900` | Generation length cap |
| `MAX_UPLOAD_MB` | `15` | Max image upload size |

> ⚠️ **Never commit `.env`.** It's already excluded in `.dockerignore` — add a matching `.gitignore` entry before your first commit so it's excluded from git too. Only `.env.example` (with a placeholder, not a real token) should ever be pushed.

## ⚠️ Honest Note

A vision-language model's plant-disease advice is knowledgeable but **not lab-certified**. CropDoctor is an advisory/triage tool — the UI includes a disclaimer to confirm critical decisions with a local agronomy expert. That framing is deliberate and part of responsible design, not boilerplate.

## 📄 License
Released under the [MIT License](LICENSE).

## 🙏 Acknowledgements
- [Qwen3-VL](https://huggingface.co/Qwen) for the underlying vision-language model
- [Hugging Face](https://huggingface.co/) for free hosted inference and Spaces deployment
