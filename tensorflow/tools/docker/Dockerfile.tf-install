FROM deepgnosis/tensorflow-build

RUN source activate keras && \
    bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/pip && \
    pip install /tmp/pip/tensorflow-*.whl
