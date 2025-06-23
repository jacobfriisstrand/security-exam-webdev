FROM python:alpine

RUN apk add --no-cache mysql-client
RUN apk add --no-cache curl
RUN apk add --no-cache grep
RUN apk add --no-cache gcc musl-dev python3-dev

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/.
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN mkdir -p /app/images

COPY entrypoint.sh /app/.
COPY . /app/.

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["sh", "entrypoint.sh"]