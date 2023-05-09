FROM python:3.10-alpine

RUN apk update && apk add python3-dev \
                        gcc \
                        libc-dev
WORKDIR /usr/src/app
RUN addgroup -S --gid ${GID:-1000} django && adduser -S -g ${GID:-1000} -u ${UID:-1000} django 

# don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# don't buffer stdout, stderr
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /usr/src/app/data && \
        chown -R django:django /usr/src/app/data && \
        chmod -R 755 /usr/src/app/data
RUN mkdir -p /usr/src/app/staticfiles && \
        chown -R django:django /usr/src/app/staticfiles && \
        chmod -R 755 /usr/src/app/staticfiles

USER django
