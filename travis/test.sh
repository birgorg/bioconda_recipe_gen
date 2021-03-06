#!/bin/bash
##### Constants
# The TRAVIS_BUILD_DIR is specified by travis itself
DATA_PATH=$TRAVIS_BUILD_DIR/travis/data

##### functions

build_htstream()
{
    data=$DATA_PATH/htstream
    birg build $data cmake
}

build_qfilt()
{
    data=$DATA_PATH/qfilt
    birg build $data cmake
}

build_libdivsufsort()
{
    data=$DATA_PATH/libdivsufsort
    birg build $data cmake
}

build_lambda()
{
    data=$DATA_PATH/lambda
    birg build $data cmake -d
}

build_fuma()
{
    data=$DATA_PATH/fuma
    yes | birg build $data python2 -d
}

build_crossmap()
{
    data=$DATA_PATH/crossmap
    yes | birg build $data python3
}


##### Choose package to build
package=$1
case $package in
    # Cmake and Make packages
    htstream)           build_htstream;;
    qfilt)              build_qfilt;;
    libdivsufsort)      build_libdivsufsort;;
    lambda)             build_lambda;;
    fuma)               build_fuma;;
    crossmap)           build_crossmap;;
esac
