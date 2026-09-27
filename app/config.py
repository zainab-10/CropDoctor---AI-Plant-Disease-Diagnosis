"""
CropDoctor configuration — all via environment variables so the same image
runs in two modes without code changes.

MODEL_BACKEND = "api"   -> Hugging Face hosted inference (tiny image, no GPU)
MODEL_BACKEND = "local" -> Qwen3-VL-4B loaded in the container (uses your GPU)
"""

import os

MODEL_BACKEND  = os.getenv("MODEL_BACKEND", "api").lower()
HF_TOKEN       = os.getenv("HF_TOKEN", "")

HF_API_MODEL   = os.getenv("HF_API_MODEL", "Qwen/Qwen3-VL-8B-Instruct")
LOCAL_MODEL    = os.getenv("LOCAL_MODEL", "Qwen/Qwen3-VL-4B-Instruct")

MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "900"))
MAX_UPLOAD_MB  = int(os.getenv("MAX_UPLOAD_MB", "15"))
