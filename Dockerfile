FROM python:slim-buster

# fixes debconf warnings/errors, see https://github.com/phusion/baseimage-docker/issues/58
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y redis libgeos-dev

# Port setup
EXPOSE 5000
ENV PORT 5000

# Copy files
COPY . /app
WORKDIR /app

# Install python requirements
RUN pip install -r requirements.txt

# Start Redis, worker and gunicorn
ENTRYPOINT cd api && bash start_services.sh
