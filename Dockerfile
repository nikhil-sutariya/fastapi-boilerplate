FROM python:3.10-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/

# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

COPY . /app/

FROM python:3.10-alpine

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

EXPOSE 8000

CMD ["fastapi", "run",  "--host", "0.0.0.0", "--port", "8000"]
