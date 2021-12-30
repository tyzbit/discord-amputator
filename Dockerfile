FROM python:3.8-alpine
ARG BUILD_DATE
ARG SOURCE_COMMIT
ARG SOURCE_URL
ARG IMAGE_NAME

ENV BUILD_DATE=${BUILD_DATE}
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
ARG SOURCE_URL=${SOURCE_URL}
ARG IMAGE_NAME=${IMAGE_NAME}

ADD requirements.txt /requirements.txt
RUN apk add \
    musl-dev \
    gcc \
&&  pip install -r requirements.txt

# Uncomment for local development to bake in a config
# ADD config.json /config.json
ADD bot.py /bot.py

CMD ["python","bot.py"]