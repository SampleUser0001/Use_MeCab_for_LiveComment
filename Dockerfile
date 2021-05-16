# 任意のイメージを取得
FROM python

RUN pip install python-dotenv

WORKDIR /app

COPY app /app
COPY start.sh /start.sh

RUN chmod 755 /start.sh

RUN python --version

CMD [ "/start.sh" ]
