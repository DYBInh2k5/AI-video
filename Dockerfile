FROM python:3.10

# Create a non-root user for Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Switch to root to install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libsndfile1-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch back to non-root user
USER user

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Copy requirements and install
COPY --chown=user backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY --chown=user backend/ .

# Ensure upload/output directories exist with correct permissions
RUN mkdir -p uploads outputs temp_processing

# Hugging Face specific settings
ENV COQUI_TOS_AGREED=1
ENV PORT=7860
EXPOSE 7860

# Run the app
CMD ["python", "main.py"]
