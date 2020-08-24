FROM python:3.8-alpine
RUN apk add build-base
RUN apk add --update python3
RUN apk add python3-dev
RUN apk add --update py3-pip
RUN apk add ffmpeg
COPY . /app
WORKDIR /app
ENV FLASK_ENV development
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .

CMD = ["flask", "run"]
