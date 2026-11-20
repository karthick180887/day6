FROM python:3.11-slim

LABEL maintainer="Day 6 AI/ML Training Team"
LABEL description="Turnkey JupyterLab environment for Day 6: ML Lifecycle, Pipelines, Validation, and Config Management"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    JUPYTER_ENABLE_LAB=yes

# Minimal OS packages needed for healthchecks and scientific wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for safe container execution and clean file permissions
ARG USERNAME=jovyan
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME}

WORKDIR /workspace

# Install Python dependencies as a cached Docker layer
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# Prepare mount point owned by the non-root user
RUN mkdir -p /workspace/notebooks \
    && chown -R ${USERNAME}:${USERNAME} /workspace

USER ${USERNAME}
WORKDIR /workspace/notebooks

EXPOSE 8888

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8888/api || exit 1

# Token defaults to 'day6-training' and can be overridden via .env / docker-compose.yml
CMD ["sh", "-c", "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --ServerApp.token=${JUPYTER_TOKEN:-day6-training} --ServerApp.root_dir=/workspace/notebooks"]
