# Client/Testing dockerfile for DeepSpeech
FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04

ARG UID=1000
# GID 44 ubuntu
ARG GID=44

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
RUN chown ${UID} /src/working

# Download the deepspeech released models to the models/ directory
ADD model/deepspeech-0.7* /src/models/
# Pull in current DeepSpeech release
RUN pip3 install tensorflow-gpu 'DeepSpeech>=0.7' ipython ipdb

# Create user with username and password `deepspeech`
RUN useradd \
    -u ${UID} \
    -g ${GID} \
    -d /src/home \
    -s /bin/bash \
    -p '$6$m6HrZ49I.nlELRt2$u7acJKMqz2NqAE8cmv848KpJeCbZk4qX0F3s9imBVVikidGW6Ssced8bJPbyPXb3g/gZ6/CPbttsqjSBuVyoE/' \
    deepspeech
RUN chown -R deepspeech /src/
RUN pip3 install webrtcvad
WORKDIR /src/home

CMD ["/src/home/working/recogpipe.py"]