FROM nvidia/cuda:11.4.0-devel-ubuntu20.04

MAINTAINER Antoni Oliver <aoliverg@uoc.edu>
LABEL description="MTUOC-server from local files."

COPY . /
RUN chmod +x start
RUN chmod +x stop
RUN chmod +x marian-server-GPU
