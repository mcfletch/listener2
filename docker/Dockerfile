# Client/Testing dockerfile for DeepSpeech
FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04

RUN apt update && apt install -y \
    python3 \
    python3-pip \
    python3-numpy \
    libsox-dev \
    bash-completion \
    unzip \
    sox

RUN mkdir -p /src/working
RUN mkdir -p /src/models

# tensorflow-gpu is a huge package, so separate
# from the (tiny) deepspeech install
RUN pip3 install tensorflow-gpu 
# Pull in current DeepSpeech release
ARG DEEPSPEECH_VERSION=0.7.3
ENV DEEPSPEECH_VERSION=${DEEPSPEECH_VERSION}
RUN pip3 install "DeepSpeech==${DEEPSPEECH_VERSION}" webrtcvad ipython ipdb
# Create user with username and password `deepspeech` matching the running
# user's id, note that this is meh as it requires each user to have their
# own docker image... so... meh
ARG UID=1000
RUN useradd \
    -u ${UID} \
    -G adm,sudo,video \
    -d /src/home \
    -s /bin/bash \
    -p '$6$m6HrZ49I.nlELRt2$u7acJKMqz2NqAE8cmv848KpJeCbZk4qX0F3s9imBVVikidGW6Ssced8bJPbyPXb3g/gZ6/CPbttsqjSBuVyoE/' \
    deepspeech
RUN chown -R deepspeech /src/
RUN mkdir -p /src/working
WORKDIR /src/working

CMD ["/src/working/scripts/docker-startup.py"]
