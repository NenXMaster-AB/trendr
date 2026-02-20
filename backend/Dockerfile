FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY trendr_api /app/trendr_api
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn trendr_api.main:app --host 0.0.0.0 --port 8000"]
