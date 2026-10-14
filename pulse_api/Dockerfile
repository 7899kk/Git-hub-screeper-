FROM python:3.12-slim
WORKDIR /app
COPY pulse_api/requirements.lock /app/requirements.lock
COPY pulse_api/vendor /app/wheels
RUN if ls /app/wheels/*.whl >/dev/null 2>&1; then pip install --no-index --find-links=/app/wheels -r requirements.lock; else pip install --no-cache-dir -r requirements.lock; fi
RUN useradd --uid 10001 --create-home pulse && mkdir -p /app/data && chown pulse /app/data
COPY --chown=pulse:pulse pulse_api /app/pulse_api
COPY --chown=pulse:pulse backend /app/backend
USER pulse
EXPOSE 8010
CMD ["sh", "-c", "alembic -c pulse_api/alembic.ini upgrade head && uvicorn pulse_api.app:app --host 0.0.0.0 --port 8010"]
