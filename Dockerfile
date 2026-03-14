FROM python:3.10-slim
RUN apt-get update && apt-get install -y build-essential curl
WORKDIR /work

COPY requirements.txt .
# ⚡ ここでuvを使って爆速インストール！
RUN pip install uv && uv pip install --system -r requirements.txt

EXPOSE 8501