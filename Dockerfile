FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# --- 修正後的安裝步驟 ---
# 1. 先安裝 curl, gnupg, ca-certificates (下載金鑰必備)
# 2. 下載 Microsoft 金鑰 -> 轉成二進位格式 (dearmor) -> 存放到 /usr/share/keyrings/
# 3. 手動建立 sources.list，並加入 [signed-by=...] 屬性，明確指定金鑰位置
# 4. 執行 apt-get update 並安裝驅動
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    build-essential \
    # --- 關鍵修正開始 ---
    # 下載並轉換金鑰
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    # 寫入 Repository 設定，明確指定 signed-by
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    # --- 關鍵修正結束 ---
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libltdl7 \
        libkrb5-3 \
        libgssapi-krb5-2 \
        msodbcsql18 \
        unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# --- 安裝 Python 依賴 ---
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install langchain-openai
# --- 安裝 Playwright ---
RUN playwright install --with-deps chromium

COPY . .
EXPOSE 8000
CMD ["python", "crawler_app.py"]