#!/usr/bin/env bash

# not sure if this is needed
add-apt-repository -y ppa:ubuntu-toolchain-r/test

# install packages and make sure we're fully upgraded
apt update
apt install -y build-essential libgoogle-glog-dev libgtest-dev libgmp-dev libgmp10
apt full-upgrade -y

# install numpy. Used for cfg/pda output.
pip3 install numpy
