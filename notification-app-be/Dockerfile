FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

COPY ./app ./notification_app_be/app

EXPOSE 8000

CMD ["uvicorn", "notification_app_be.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
