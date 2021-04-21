FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system packages then clean up to minimize image size
RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      git \
      maven \
      npm \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN npm -g install svgo

RUN git clone https://github.com/phauer/svg-buddy.git /tmp/svg-buddy \
 && cd /tmp/svg-buddy \
 && ./mvnw package -Dquarkus.package.uber-jar=true

RUN cp /tmp/svg-buddy/target/svg-buddy-runner.jar /usr/local/share/svg-buddy-runner.jar
COPY run.sh /usr/local/bin/planscore-svg.sh
CMD planscore-svg.sh
