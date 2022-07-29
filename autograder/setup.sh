#!/usr/bin/env bash

apt-get install -y software-properties-common

add-apt-repository -y ppa:ubuntu-toolchain-r/test

apt-get update && apt-get install -y \
    libboost-dev \
	gcc-9 \
	jq \
	libc6-dev \
	libgmp-dev \
    libgmp10 \
    libgoogle-glog-dev \
	gnupg2 \
    libc++-9-dev \
    python3 \
    python3-pip

# install numpy. Used for cfg/pda output.
pip3 install numpy

# install bazel
curl https://bazel.build/bazel-release.pub.gpg | apt-key add -
echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list
apt update && apt install -y bazel
apt update && apt full-upgrade -y
