FROM python:3.12-slim-bookworm

ARG TZ=Asia/Shanghai
ENV TZ=${TZ}
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/telegram-signer-src
COPY pyproject.toml README.md ./
COPY telegram_signer ./telegram_signer
RUN pip install --no-cache-dir . && \
    cd / && rm -rf /tmp/telegram-signer-src

WORKDIR /opt/telegram-signer
