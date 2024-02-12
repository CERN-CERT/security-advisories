FROM python:3.11.8 AS BUILDER

WORKDIR /app
COPY . /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip3 install -U pip &&  \
    python3 -m venv .venv && \
    /app/.venv/bin/pip3 install -r requirements.txt

FROM python:3.11.8-slim
COPY --from=BUILDER /app /app
WORKDIR /app

RUN apt update && \
    apt install -y curl && \
    mkdir -p /config

COPY config.ini /config/config.ini
ENV PATH="/app/.venv/bin:$PATH"
