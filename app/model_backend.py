"""
Two interchangeable multimodal backends behind one interface.
The app calls `diagnose(image_bytes)` / `followup(...)` and never cares which
backend is active.
"""

import base64
import io
import json
import re
from functools import lru_cache

from . import config, prompts


# ---------------------------------------------------------------- helpers
def _extract_json(text: str) -> dict:
    """Models sometimes wrap JSON in prose or code fences. Recover it safely."""
    text = text.strip()
    # strip ``` fences if present
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    # grab the outermost {...}
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except Exception:
        # last resort: return a minimal object so the UI still shows something
        return {
            "is_plant": True, "healthy": False, "crop": "uncertain",
            "diagnosis": "Could not parse a structured result",
            "confidence": "low", "severity": "none",
            "symptoms": [], "causes": [], "treatment": [], "prevention": [],
            "summary": text[:400] or "No response.",
        }


# ---------------------------------------------------------------- API backend
def _api_client():
    from huggingface_hub import InferenceClient
    if not config.HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is not set. Add a free Hugging Face token to use API mode "
            "(https://huggingface.co/settings/tokens)."
        )
    return InferenceClient(api_key=config.HF_TOKEN)


def _data_url(image_bytes: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode()


def _api_chat(messages) -> str:
    client = _api_client()
    completion = client.chat.completions.create(
        model=config.HF_API_MODEL, messages=messages,
        max_tokens=config.MAX_NEW_TOKENS,
    )
    return completion.choices[0].message.content.strip()


def _api_image_ref(image_bytes):
    return {"type": "image_url", "image_url": {"url": _data_url(image_bytes)}}


# ---------------------------------------------------------------- local backend
@lru_cache(maxsize=1)
def _load_local():
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    mid = config.LOCAL_MODEL
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = AutoProcessor.from_pretrained(mid)
    model = AutoModelForImageTextToText.from_pretrained(mid, torch_dtype=dtype, device_map=device)
    return proc, model, device


def _local_chat(messages, image) -> str:
    import torch
    proc, model, device = _load_local()
    # replace the placeholder image ref with a real PIL image in the messages
    for m in messages:
        if isinstance(m["content"], list):
            for part in m["content"]:
                if part.get("type") == "image":
                    part["image"] = image
    inputs = proc.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    ).to(device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=config.MAX_NEW_TOKENS)
    trimmed = out[0][inputs["input_ids"].shape[1]:]
    return proc.decode(trimmed, skip_special_tokens=True).strip()


def _local_image_ref():
    return {"type": "image", "image": None}   # filled in _local_chat


# ---------------------------------------------------------------- public API
def diagnose(image_bytes: bytes) -> dict:
    if config.MODEL_BACKEND == "local":
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        msgs = prompts.diagnosis_messages(_local_image_ref())
        raw = _local_chat(msgs, img)
    else:
        msgs = prompts.diagnosis_messages(_api_image_ref(image_bytes))
        raw = _api_chat(msgs)
    return _extract_json(raw)


def followup(image_bytes: bytes, question: str, prior_summary: str) -> str:
    if config.MODEL_BACKEND == "local":
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        msgs = prompts.followup_messages(_local_image_ref(), question, prior_summary)
        return _local_chat(msgs, img)
    msgs = prompts.followup_messages(_api_image_ref(image_bytes), question, prior_summary)
    return _api_chat(msgs)


def backend_info() -> dict:
    return {
        "backend": config.MODEL_BACKEND,
        "model": (config.LOCAL_MODEL if config.MODEL_BACKEND == "local"
                  else config.HF_API_MODEL),
    }
