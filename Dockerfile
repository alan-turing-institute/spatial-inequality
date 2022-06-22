FROM mambaorg/micromamba

# fixes debconf warnings/errors, see https://github.com/phusion/baseimage-docker/issues/58
#RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

USER root

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git redis libgeos-dev && \
    rm -rf /var/cache/apt/lists

# Port setup
ENV PORT 5000
EXPOSE $PORT

# Copy files
COPY api /app/api
COPY data/processed /app/data/processed
COPY spineq /app/spineq
COPY .env environment.yml pyproject.toml poetry.lock /app/

# Install python requirements
RUN cd /app && \
    micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes

# needed to activate env in dockerfile
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# download data
RUN python /app/spineq/data_fetcher.py --lad20cd E08000021

WORKDIR /app/api
