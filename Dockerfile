FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY candidate_package ./candidate_package
COPY README.md ./README.md
COPY REPORT.md ./REPORT.md

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["sh", "-c", "python -m app.etl && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
