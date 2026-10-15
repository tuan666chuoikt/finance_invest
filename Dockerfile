FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY services services
COPY apps apps
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
