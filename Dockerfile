FROM python:slim-buster

# fixes debconf warnings/errors, see https://github.com/phusion/baseimage-docker/issues/58
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y redis libgeos-dev

# Port setup
ENV PORT 5000
EXPOSE $PORT

# Copy files
COPY . /app

# Install python requirements
RUN cd /app && pip install -r requirements.txt

WORKDIR /app/api
