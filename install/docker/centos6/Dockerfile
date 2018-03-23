# RAPD
#
# VERSION 2.0.0

FROM centos:6.7
MAINTAINER Frank Murphy <fmurphy@anl.gov>

# Needed to build Phenix
RUN yum -y install bzip2 \
                   gcc-c++ \
                   git \
                   make \
                   mesa-libGL-devel \
                   mesa-libGLU-devel \
                   ncurses-devel \
                   openssl-devel \
                   patch \
                   subversion \
                   tar \
                   wget
RUN adduser tester
# USER tester
# yum install http://opensource.wandisco.com/centos/6/git/x86_64/wandisco-git-release-6-1.noarch.rpm
WORKDIR /home/tester
# RUN git clone -b master https://github.com/RAPD/RAPD.git rapd
# WORKDIR /home/tester/rapd/install
# RUN ./install -mb > install.log
