FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CAFESITO_DATABASE_PATH=/app/data/cafesito.db \
    CAFESITO_SALES_CSV_PATH=/app/data/raw/coffee_shop_sales.csv \
    CAFESITO_MODELS_DIR=/app/models \
    CAFESITO_HOST=0.0.0.0 \
    CAFESITO_PORT=8000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

COPY data/raw ./data/raw

RUN useradd --create-home appuser && mkdir -p /app/data /app/models && chown -R appuser /app
USER appuser

RUN python -m cafesito bootstrap

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"CAFESITO_PORT\",\"8000\")}/api/health')"

CMD ["python", "-m", "cafesito", "serve"]
