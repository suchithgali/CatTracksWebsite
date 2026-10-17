FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=website.app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:5000/health').read()"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "website.app:app"]
