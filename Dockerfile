FROM python:3.11-slim

WORKDIR /app

# Patches known CVEs in pip's bundled wheel/jaraco.context before anything
# else is installed.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY app.py .

CMD ["python", "app.py"]
