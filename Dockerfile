FROM python:3.12-slim
WORKDIR /app
COPY backend backend
COPY frontend frontend
RUN useradd --uid 10001 --create-home pricepulse && mkdir -p /app/data && chown pricepulse /app/data
USER pricepulse
EXPOSE 8000
CMD ["python", "-m", "backend.server", "--host", "0.0.0.0", "--db", "/app/data/pricepulse.db"]
