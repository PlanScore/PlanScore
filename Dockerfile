FROM --platform=linux/arm64 ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update -y \
 && apt install -y python3 python3-pip python3-gdal python3-numpy \
 && apt clean -y \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install 'awslambdaric==2.2.1'

RUN mkdir /tmp/src

COPY setup.py /tmp/src/
COPY planscore /tmp/src/planscore
RUN pip3 install '/tmp/src'

ENTRYPOINT [ "/usr/bin/python3", "-m", "awslambdaric" ]
CMD [ "planscore.authorizer.lambda_handler" ]
