FROM python:3.14.8-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /home/app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p media staticfiles logs && chown -R app:app /home/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check
COPY --chown=app:app . .
USER app
EXPOSE 8000
ENTRYPOINT ["python", "/home/app/scripts/start.py"]
CMD ["gunicorn", "-c", "gunicorn/gunicorn_config.py", "config.wsgi:application"]
