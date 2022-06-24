FROM mambaorg/micromamba

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
COPY spineq /app/spineq
COPY .env environment.yml pyproject.toml poetry.lock /app/

# Install python requirements
RUN cd /app && \
    micromamba install -y -n base -f environment.yml && \
    micromamba clean -afy

# needed to activate env in dockerfile
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# download data for a local authority (Newcastle by default)
ARG LAD20CD=E08000021 
ENV LAD20CD=$LAD20CD
RUN python /app/spineq/data_fetcher.py --lad20cd $LAD20CD

WORKDIR /app/api
