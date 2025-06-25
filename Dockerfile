FROM python:3.12

# 更新・日本語化
RUN apt-get update && apt-get -y install locales && apt-get -y upgrade && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm

# 作業ディレクトリを /bot に設定
WORKDIR /bot

# requirements.txt のコピーと pip アップグレード＋インストール
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# アプリコードのコピー
COPY . .

# ポート開放（必要に応じて）
EXPOSE 8080

# 実行コマンド
CMD ["python", "app/main.py"]
