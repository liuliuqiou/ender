FROM alpine:3.19

RUN apk add --no-cache ca-certificates curl tzdata \
    && mkdir -p /etc/xray /var/log/xray

RUN curl -L -o /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip \
    && apk add --no-cache unzip \
    && unzip /tmp/xray.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/xray \
    && rm -rf /tmp/xray.zip

COPY config.json /etc/xray/config.json

EXPOSE 80

CMD ["xray", "-config", "/etc/xray/config.json"]
