# --- FRONTEND STAGE ---
FROM node:20 AS frontend

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build

# --- BACKEND STAGE ---
FROM python:3.11-slim AS backend

# OS Essentials
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend
COPY backend ./backend

# Copy from FE to static
COPY --from=frontend /app/frontend/dist /app/backend/static

WORKDIR /app/backend

# Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Flask configuratrions
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

CMD ["flask", "run"]
