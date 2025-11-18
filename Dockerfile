# ================================
# 🐍 Base Image
# ================================
FROM python:3.10-slim

# Disable .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# ================================
# 📦 System Dependencies
# ================================
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libopenblas-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# ================================
# 📁 Copy Project Files
# ================================
COPY . /app

# ================================
# 🔧 Python Dependencies
# ================================
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ================================
# 🌐 Expose App Port
# ================================
EXPOSE 7860

# ================================
# 🚀 Run FastAPI App
# ================================
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]