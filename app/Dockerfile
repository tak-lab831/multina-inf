# 軽量なPythonイメージを使用
FROM python:3.12-slim

# 作業ディレクトリの設定
WORKDIR /app

# 必要なパッケージをインストール（Pandasのビルドに必要なライブラリ等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 依存ライブラリのコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# 実行権限の付与やディレクトリ作成
RUN mkdir -p uploads

# Gunicornで起動（Worker数はCPUコア数に合わせて調整）
CMD ["gunicorn", "-w", "3", "--bind", "0.0.0.0:8000", "wsgi:app"]
