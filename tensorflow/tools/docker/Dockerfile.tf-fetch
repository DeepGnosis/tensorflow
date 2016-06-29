FROM deepgnosis/tensorflow-bazel

# Download and build TensorFlow.

RUN git clone --recurse-submodules https://github.com/tensorflow/tensorflow.git && \
    cd tensorflow && \
    git checkout r0.9 && \
    git submodule update --init
WORKDIR /tensorflow

# Configure the build for our CUDA configuration.
ENV CUDA_TOOLKIT_PATH /usr/local/cuda
ENV CUDNN_INSTALL_PATH /usr/local/cuda
ENV TF_NEED_CUDA 1

RUN source activate keras && \
    ./configure && \
    bazel fetch tensorflow/tools/pip_package:build_pip_package
