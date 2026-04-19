FROM alpine:3.19

RUN apk add --no-cache ca-certificates curl tzdata \
    && mkdir -p /etc/xray /var/log/xray

# 下载 xray
RUN curl -L -o /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip \
    && apk add --no-cache unzip \
    && unzip /tmp/xray.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/xray \
    && rm -rf /tmp/xray.zip

# 拷贝配置
COPY config.json /etc/xray/config.json

# Back4App 只要求 EXPOSE 一个 TCP 端口，这里用 80
EXPOSE 80

CMD ["xray", "-config", "/etc/xray/config.json"]
