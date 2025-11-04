FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install pymupdf requests --break-system-packages

COPY test.py .

CMD ["python", "test.py"]