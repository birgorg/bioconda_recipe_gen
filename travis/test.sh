#!/bin/bash
##### Constants

BR_PATH=./bioconda-recipes
DATA_PATH=./travis/data

##### functions

build_kallisto()
{
    name=kallisto2
    url=https://github.com/pachterlab/kallisto/archive/v0.45.0.tar.gz
    sha=b32c74cdc0349c2fe0847b3464a3698da89212a507332a06291b6fc27b4e2305 
    tests=$DATA_PATH/kallisto 
    version=0.45.0
    commands="kallisto version"
    bioconda-recipe-gen $BR_PATH -n $name -u $url --tests $tests -s $sha -v $version --debug --commands $commands
}

build_htstream()
{
    name=htstream2 
    url=https://github.com/ibest/HTStream/archive/v1.0.0-release.tar.gz 
    sha=4cf9ea61be427ea71c346e438ad2871cf0c7671948819647ef8f182d54e955fe
    version=1.0.1
    commands="hts_Stats --help" "hts_AdapterTrimmer --help" "hts_CutTrim --help" "hts_NTrimmer --help" "hts_Overlapper --help" "hts_PolyATTrim --help" "hts_QWindowTrim --help" "hts_SeqScreener --help" "hts_SuperDeduper --help" 
    patches=$DATA_PATH/htstream
    bioconda-recipe-gen $BR_PATH -n $name -u $url -s $sha -v $version --test-commands $commands --patches $patches
}

build_qfilt()
{
    name=qfilt2
    url=https://github.com/veg/qfilt/archive/0.0.1.tar.gz
    sha=b0ada01c44c98b1a8bebf88c72a845b24f91a7cc63687e228b1ad872681adc09
    version=0.0.1
    commands="qfilt -h 2>&1 | grep 'filter sequencing data using some simple heuristics' > /dev/null"
    bioconda-recipe-gen $BR_PATH -n $name -u $url -s $sha -v $version --test-commands "$commands"
}

##### Choose package to build

package=$1
case $package in
    # Cmake and Make packages
    kallisto)           build_kallisto;;
    htstream)           build_htstream;;
    qfilt)              build_qfilt;;
esac
