FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt-get update && apt-get -y install
RUN apt install unixodbc -y
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "bot_start.py"]

EXPOSE 443