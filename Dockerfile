# CropDoctor — one Dockerfile, two modes via the BACKEND build-arg.
#   docker build -t cropdoctor:api .
#   docker build -t cropdoctor:local --build-arg BACKEND=local .
FROM python:3.12-slim
ARG BACKEND=api
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/models
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo libpng16-16 libgl1 libglib2.0-0 ffmpeg git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY requirements-local.txt .
RUN if [ "$BACKEND" = "local" ]; then pip install -r requirements-local.txt; fi
COPY app ./app
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
