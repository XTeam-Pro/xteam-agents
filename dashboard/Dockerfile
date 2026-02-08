FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    graphviz \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir watchdog[watchmedo]

COPY . .

EXPOSE 8501

# Enable Streamlit hot reload with logger debug mode
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.fileWatcherType=poll", \
     "--logger.level=debug", \
     "--client.toolbarMode=viewer"]
