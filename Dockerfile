# 任意のイメージを取得
FROM python

RUN apt update && apt upgrade -y
RUN apt install -y wget gcc make g++ less

RUN git config --global ssh.postBuffer 524288000
RUN git config --global http.postBuffer 524288000

RUN ln -sf  /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# MeCabインストール
WORKDIR /root
RUN wget -O "mecab.tar.gz" "https://drive.google.com/uc?export=download&id=0B4y35FiV1wh7cENtOXlicTFaRUE"
RUN tar xvfz mecab.tar.gz
WORKDIR /root/mecab-0.996
RUN ./configure --enable-utf8-only --prefix=/usr/local/mecab && make && make install

ENV PATH=/usr/local/mecab/bin:$PATH

# 辞書インストール
WORKDIR /root
RUN wget -O "mecab-ipadic.tar.gz" "https://drive.google.com/uc?export=download&id=0B4y35FiV1wh7MWVlSDBCSXZMTXM"
RUN tar xvfz mecab-ipadic.tar.gz
WORKDIR /root/mecab-ipadic-2.7.0-20070801
RUN ./configure --prefix=/usr/local/mecab --with-mecab-config=/usr/local/mecab/bin/mecab-config --with-charset=utf8 && make && make install 

# 辞書インストール
WORKDIR /root
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
RUN ./mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -y
ENV MECABRC=/usr/local/mecab/etc/mecabrc

RUN python -m pip install --upgrade pip
RUN pip install mecab-python3 python-dotenv

WORKDIR /app

COPY app /app
COPY start.sh /start.sh

RUN chmod 755 /start.sh

CMD [ "/start.sh" ]