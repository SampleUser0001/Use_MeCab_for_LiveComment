# 任意のイメージを取得
FROM python:3.10-rc-slim-buster

WORKDIR /app

COPY app /app
COPY start.sh /start.sh

RUN chmod 755 /start.sh

RUN python --version

CMD [ "/start.sh" ]
