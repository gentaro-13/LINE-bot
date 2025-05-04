# 👉 ベースは軽量な Python 3.11
FROM python:3.11-slim

# 👉 作業ディレクトリ
WORKDIR /app

# 👉 依存ライブラリを先にコピー & インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 👉 残りのソースをコピー
COPY . .

# 👉 Cloud Run が見るポートを環境変数で宣言
ENV PORT=8080

# 👉 Uvicorn でアプリ起動
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8080"]
