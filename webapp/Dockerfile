FROM python:3.10-alpine

RUN apk update && apk add python3-dev \
                        gcc \
                        libc-dev
WORKDIR /usr/src/app

# don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# don't buffer stdout, stderr
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
