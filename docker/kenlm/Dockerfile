FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04 AS builder

RUN apt update && apt install -y \
    build-essential \
    cmake \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-program-options-dev \
    libboost-test-dev \
    libeigen3-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    curl
RUN mkdir -p /src/working
WORKDIR /src/working/
RUN curl -L -o kenlm.tar.gz https://github.com/kpu/kenlm/archive/master.tar.gz
RUN tar -zxf kenlm.tar.gz
RUN mkdir -p /src/working/kenlm-master/build
WORKDIR /src/working/kenlm-master/build
RUN cmake ..
RUN make -j 4

FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04
WORKDIR /src/working
RUN apt update && apt install -y \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-program-options-dev
COPY --from=0 /src/working/kenlm-master/build/bin /src/kenlm
ENV KENLM_BIN=/src/kenlm
