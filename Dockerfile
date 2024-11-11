FROM python:3.10-slim

ENV LANG=en_US.UTF-8
ENV LANGUAGE en_US:en
ENV TZ=Asia/Shanghai
# 设置时区和OS默认字符编码，避免时间戳转换时默认字符格式不对
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#RUN sed -i 's/http:\/\/deb.debian.org/https:\/\/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
#    && apt-get update  \
#    && apt-get -y install net-tools lsof libgdiplus libc6-dev libicu-dev fontconfig poppler-utils

# pip配置
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

RUN mkdir -p /opt/app
COPY requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt --default-timeout=1200
COPY app /opt/app

RUN useradd dota
ENV PYTHONPATH /opt
WORKDIR /opt/app
EXPOSE 3000
CMD ["python3", "main.py"]
