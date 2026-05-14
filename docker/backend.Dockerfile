FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend /app
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 core.asgi:application"]
