FROM python:3.10

# Create a non-root user for Hugging Face
RUN useradd -m -u 1000 user
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Install torch separately to handle potential memory/cache issues
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ .

# Fix permissions for the non-root user
RUN mkdir -p uploads outputs temp_processing && \
    chown -R user:user /app && \
    chmod -R 777 /app

USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Hugging Face specific settings
ENV COQUI_TOS_AGREED=1
ENV PORT=7860
EXPOSE 7860

# Run the app
CMD ["python", "main.py"]
