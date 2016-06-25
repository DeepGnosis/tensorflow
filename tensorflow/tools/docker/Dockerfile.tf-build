FROM deepgnosis/tensorflow-fetch

# Build TensorFlow.

RUN source activate keras && \
    bazel build -c opt --config=cuda tensorflow/tools/pip_package:build_pip_package
