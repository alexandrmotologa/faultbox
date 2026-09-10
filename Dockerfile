FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir dist/*.whl

FROM python:3.12-slim

WORKDIR /app

RUN useradd -u 10001 -m -s /bin/bash faultbox

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/faultbox /usr/local/bin/faultbox
COPY scenarios/ /app/scenarios/

USER faultbox

EXPOSE 8474 9000-9100

ENTRYPOINT ["faultbox"]
CMD ["run", "--api", "--host", "0.0.0.0", "--api-port", "8474"]
