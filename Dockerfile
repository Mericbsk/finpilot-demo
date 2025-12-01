FROM python:3.10-slim

WORKDIR /app

# Gerekli sistem paketlerini yükle (git gerekebilir)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY . .

# Streamlit portunu dışarı aç
EXPOSE 8501

# Sağlık kontrolü
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Uygulamayı başlat
ENTRYPOINT ["streamlit", "run", "panel_new.py", "--server.port=8501", "--server.address=0.0.0.0"]
