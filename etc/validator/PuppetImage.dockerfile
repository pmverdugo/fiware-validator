# Dockerfile to deploy a valid puppet self-service container
# tag: pmverdugo/trusty-puppet-self-service

FROM ubuntu:14.04
MAINTAINER Pedro Verdugo <pmverdugo 'at' dit.upm.es>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y wget && \
    wget http://apt.puppetlabs.com/puppetlabs-release-trusty.deb && \
    dpkg -i puppetlabs-release-trusty.deb && \
    rm puppetlabs-release-trusty.deb && \
    apt-get clean

WORKDIR '/etc/puppet'