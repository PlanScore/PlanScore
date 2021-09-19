FROM amazonlinux:2.0.20210813.1

# Install deps

RUN \
    touch /var/lib/rpm/* && \
    yum install -y \
        automake16 \
        bzip2 \
        bzip2-devel \
        curl \
        gzip \
        libffi-devel \
        libpng-devel \
        libtiff-devel \
        openssl-devel \
        sqlite-devel \
        tar \
        && \
    yum group install -y \
        "Development Tools"

# Fetch, build, and install Python 3.9

RUN \
    curl -L https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz | tar zxf - -C /tmp && \
    cd /tmp/Python-3.9.6 && \
    ./configure --enable-optimizations && \
    make -j $(nproc) && \
    make install && \
    rm -rf /tmp/Python-3.9.6

# Fetch, build, and install SQLite 3

RUN \
  curl -L https://www.sqlite.org/2021/sqlite-autoconf-3360000.tar.gz | tar zxf - -C /tmp && \
  cd /tmp/sqlite-autoconf-3360000 && \
  CFLAGS="-DSQLITE_ENABLE_COLUMN_METADATA=1" \
  ./configure \
    --prefix=/var/task && \
  make -j $(nproc) && \
  make install && \
    rm -rf /tmp/sqlite-autoconf-3360000

ENV PKG_CONFIG_PATH /var/task/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/share/pkgconfig:/usr/local/lib/pkgconfig

# Fetch, build, and install PROJ

RUN \
  curl -L http://download.osgeo.org/proj/proj-7.2.1.tar.gz | tar zxf - -C /tmp && \
  cd /tmp/proj-7.2.1 && \
  ./configure \
    --prefix=/var/task \
    --without-curl && \
  make -j $(nproc) && \
  make install && \
  rm -rf /tmp/proj-7.2.1

# Fetch, build, and install GEOS

RUN \
  curl -L http://download.osgeo.org/geos/geos-3.9.0.tar.bz2 | tar jxf - -C /tmp && \
  cd /tmp/geos-3.9.0 && \
  ./configure \
    --prefix=/var/task && \
  make -j $(nproc) && \
  make install && \
  rm -rf /tmp/geos-3.9.0

# Fetch, build, and install GDAL

RUN \
  mkdir -p /tmp/gdal-3.2.1 && \
  curl -L https://github.com/OSGeo/gdal/archive/tags/v3.2.1.tar.gz | tar zxf - -C /tmp/gdal-3.2.1 --strip-components=1 && \
  cd /tmp/gdal-3.2.1/gdal && \
  ./configure \
    --prefix=/var/task \
    --with-proj=/var/task \
    --with-geos=/var/task/bin/geos-config \
    --datarootdir=/var/task/share/gdal \
    --with-jpeg=internal \
    --with-sqlite3=/var/task \
    --without-curl \
    --without-qhull \
    --without-mrf \
    --without-grib \
    --without-pcraster \
    --without-gif \
    --without-pcidsk && \
  make -j $(nproc) && \
  make install && \
  rm -rf /tmp/gdal-3.2.1

# Install Python deps to /var/task

WORKDIR /var/task

ENV PATH /var/task/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH /var/task/lib

RUN pip3.9 install -t /var/task 'numpy == 1.21.2' 'GDAL == 3.2.1'

# So, did it work?
RUN \
  python3.9 -c 'import numpy' && \
  python3.9 -c 'import osgeo.ogr'

# Create the function tarball

RUN \
  ln -v /lib64/libpng*.so* lib/ && \
  ln -v /lib64/libtiff.so* lib/ && \
  ln -v /lib64/libjbig*.so* lib/ && \
  ln -v /lib64/libjpeg.so* lib/

RUN \
  strip lib/libpng15.so.15 && \
  strip lib/libtiff.so.5 && \
  strip lib/libjbig.so.2.0 && \
  strip lib/libjpeg.so.62 && \
  strip lib/libsqlite3.so.0.8.6 && \
  strip lib/libgdal.so.28.0.1 && \
  strip lib/libgeos_c.so.1.16.2 && \
  strip lib/libgeos-3.9.0.so && \
  strip lib/libproj.so.19.2.1

RUN \
  tar -czf \
    /tmp/task.tgz \
    lib/libpng*.so* \
    lib/libtiff.so* \
    lib/libjbig*.so* \
    lib/libjpeg.so* \
    lib/libsqlite3.so* \
    lib/libgdal.so* \
    lib/libgeos.so* \
    lib/libgeos_c.so* \
    lib/libgeos-3.9.0.so \
    lib/libproj.so* \
    share/gdal/ \
    share/proj/ \
    numpy \
    numpy-1.21.2.dist-info \
    numpy.libs \
    GDAL-3.2.1-py3.9.egg-info \
    osgeo
