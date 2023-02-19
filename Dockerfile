FROM python:3.11-slim

RUN useradd --user-group --system --create-home --no-log-init --shell /bin/bash app
USER app
WORKDIR /home/app

COPY --chown=app:app . .

RUN pip install -U pip && pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "app/main.py", "--port", "8080", "--verbose"]