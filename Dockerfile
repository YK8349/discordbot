FROM python:3.11-slim

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

# pip install
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリコードのコピー
COPY . .

# ポート開放
EXPOSE 8080

# 実行（WORKDIRが/botなのでその中のapp/main.pyを指定）
CMD ["python", "app/main.py"]
