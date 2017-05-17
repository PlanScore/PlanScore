FROM lambci/lambda:build-python3.6

# Install deps

RUN \
  touch /var/lib/rpm/* \
  && yum install -y \
    automake16 \
    libcurl-devel \
    libpng-devel

# Fetch PROJ.4

RUN \
  curl -L http://download.osgeo.org/proj/proj-4.9.3.tar.gz | tar zxf - -C /tmp

# Build and install PROJ.4

WORKDIR /tmp/proj-4.9.3

RUN \
  ./configure \
    --prefix=/var/task && \
  make -j $(nproc) && \
  make install

# Fetch GDAL

RUN \
  mkdir -p /tmp/gdal-dev && \
  curl -L https://github.com/OSGeo/gdal/archive/3288b145e6e966499a961c27636f2c9ea80157c2.tar.gz | tar zxf - -C /tmp/gdal-dev --strip-components=1

# Build + install GDAL

WORKDIR /tmp/gdal-dev/gdal

RUN \
  ./configure \
    --prefix=/var/task \
    --datarootdir=/var/task/share/gdal \
    --with-jpeg=internal \
    --without-qhull \
    --without-mrf \
    --without-grib \
    --without-pcraster \
    --without-png \
    --without-gif \
    --without-pcidsk && \
  make -j $(nproc) && \
  make install

# Add GDAL libs to the function zip

WORKDIR /var/task

RUN \
  strip lib/libgdal.so.20.1.0 && \
  strip lib/libproj.so.12.0.0

RUN \
  zip --symlinks \
    -r /tmp/task.zip \
    lib/libgdal.so* \
    lib/libproj.so* \
    share/gdal/

# Install Python deps in a virtualenv

RUN \
  pip install virtualenv && \
  virtualenv /tmp/virtualenv

ENV PATH /tmp/virtualenv/bin:/var/task/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

COPY . /var/gdalambda
WORKDIR /var/gdalambda

RUN \
  pip install -r requirements.txt

# Add Python deps to the function zip

WORKDIR /tmp/virtualenv/lib/python3.6/site-packages

# skip the zipping (above, too) and put it in a staging directory that can be copied to a volume or output via tar on stdout
# determined by copying the app in, touching start, exercising it, then using find /tmp/virtualenv/lib/python3.6/site-packages -type f -anewer start | sort
RUN \
  zip \
    -r /tmp/task.zip \
    gdalconst.py \
    ogr.py \
    osr.py \
    osgeo/*.so \
    osgeo/*.py \
    gdal.pyc \
    __pycache__/gdalconst.cpython-36.pyc \
    __pycache__/ogr.cpython-36.pyc \
    __pycache__/osr.cpython-36.pyc \
    osgeo/__pycache__/*.cpython-36.pyc \
    __pycache__/gdal.cpython-36.pyc
