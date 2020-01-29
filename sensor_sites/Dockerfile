FROM alpine:3.8
MAINTAINER Jorge S. Mendes de Jesus <jorge.dejesus@protonmail.com>

# Not used as of 17/01/2020 - David - too many dependency problems caused by recent updates in Alpine repos

ARG GDAL_VERSION=2.4.0
ARG XERCES_VERSION=3.2.2
ARG PROCESSOR_N=4
ARG FLASK_GIT=https://github.com/jorgejesus/pywps-flask.git
ARG FLASK_BRANCH=pywps_4.2

RUN apk update && apk add --no-cache \
    git \
    gcc \
    bash \
    openssh \
    musl-dev  \
    python3 \
    python3-dev \
    libxml2-dev  \
    libxslt-dev \
    linux-headers \
    expat \
    expat-dev \
    g++ \
    libstdc++ \
    make \
    swig

RUN apk add --no-cache \
    --repositories http://dl-cdn.alpinelinux.org/alpine/edge/community \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/community \
    proj \
    proj-dev \
    geos \
    geos-dev
    
# Compiling Xerces
RUN wget http://www.apache.org/dist/xerces/c/3/sources/xerces-c-$XERCES_VERSION.tar.gz -O /tmp/xerces-c-$XERCES_VERSION.tar.gz && \
    tar xvf /tmp/xerces-c-$XERCES_VERSION.tar.gz -C /tmp && \
    cd /tmp/xerces-c-$XERCES_VERSION && \
    LDFLAGS="-s" ./configure --prefix=/usr/local/src/xerces && \
    make -j $PROCESSOR_N install

# Install GDAL
# 17/01/2020 - this takes absolutely ages and thrashes the CPU fan mercilessly! David
# This is installing a very old version of gdal from source - the binary available on the 
# Alpine apk site is 3.0.2, but it has dependency problems, as does the Xerces binary above
RUN wget http://download.osgeo.org/gdal/$GDAL_VERSION/gdal-$GDAL_VERSION.tar.gz -O /tmp/gdal.tar.gz && \
	tar xzf /tmp/gdal.tar.gz -C /tmp && \
	cd /tmp/gdal-$GDAL_VERSION && \
        LDFLAGS="-s"  ./configure --with-expat=yes --with-xerces=/opt/xerces --with-geos=yes \
	&& make -j $PROCESSOR_N && make install

RUN cd /tmp/gdal-$GDAL_VERSION/swig/python \
	&& python3 setup.py install

RUN rm -rf /var/cache/apk/*

RUN git clone $FLASK_GIT -b $FLASK_BRANCH --single-branch 
WORKDIR /pywps-flask
# Upgrade pip to 19.x otherwise we get a pyproj error later
RUN pip3 install --upgrade pip
# Fails with inability to find PROJ for some reason - David 17/01/2020
RUN pip3 install -r requirements.txt

ENTRYPOINT ["/usr/bin/python3", "demo.py","-a"]

#docker build -t pywps/flask-alpine . 
#docker run -p 5000:5000 pywps/flask-alpine:latest
#http://localhost:5000/wps?request=GetCapabilities&service=WPS
#http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0