FROM python:3.12-slim
WORKDIR /app
COPY monitor.py cfg.json ./
CMD ["python", "-u", "monitor.py"]
