FROM lambci/lambda:build-python3.6

# Install deps

RUN \
  touch /var/lib/rpm/* \
  && yum install -y \
    automake16 \
    libcurl-devel \
    sqlite-devel \
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

# Fetch GEOS

RUN \
  curl -L http://download.osgeo.org/geos/geos-3.6.1.tar.bz2 | tar jxf - -C /tmp

# Build and install GEOS

WORKDIR /tmp/geos-3.6.1

RUN \
  ./configure \
    --prefix=/var/task && \
  make -j $(nproc) && \
  make install

# Fetch GDAL

RUN \
  mkdir -p /tmp/gdal-2.1.3 && \
  curl -L https://github.com/OSGeo/gdal/archive/tags/2.1.3.tar.gz | tar zxf - -C /tmp/gdal-2.1.3 --strip-components=1

# Build + install GDAL

WORKDIR /tmp/gdal-2.1.3/gdal

RUN \
  ./configure \
    --prefix=/var/task \
    --with-geos=/var/task/bin/geos-config \
    --datarootdir=/var/task/share/gdal \
    --with-jpeg=internal \
    --with-sqlite3 \
    --without-qhull \
    --without-mrf \
    --without-grib \
    --without-pcraster \
    --without-png \
    --without-gif \
    --without-pcidsk && \
  make -j $(nproc) && \
  make install

# Add GDAL libs to the function tarball

WORKDIR /var/task

RUN \
  strip lib/libgdal.so.20.1.3 && \
  strip lib/libgeos_c.so.1.10.1 && \
  strip lib/libgeos-3.6.1.so && \
  strip lib/libproj.so.12.0.0

RUN \
  tar -cvf \
    /tmp/task.tar \
    lib/libgdal.so* \
    lib/libgeos_c.so* \
    lib/libgeos-3.6.1.so \
    lib/libproj.so* \
    share/gdal/

# Install Python deps in a virtualenv

RUN \
  pip install virtualenv && \
  virtualenv /tmp/virtualenv

ENV PATH /tmp/virtualenv/bin:/var/task/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN pip install 'GDAL == 2.1.3'

# Add Python deps to the function tarball

WORKDIR /tmp/virtualenv/lib/python3.6/site-packages

RUN \
  tar -rvf \
    /tmp/task.tar \
    gdalconst.py \
    ogr.py \
    osr.py \
    osgeo/*.so \
    osgeo/*.py \
    gdal.py \
    __pycache__/gdalconst.cpython-36.pyc \
    __pycache__/ogr.cpython-36.pyc \
    __pycache__/osr.cpython-36.pyc \
    osgeo/__pycache__/*.cpython-36.pyc \
    __pycache__/gdal.cpython-36.pyc
