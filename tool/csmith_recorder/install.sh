#!/bin/bash
for ((i=2;i<=5;i++))
do
    PWDPATH=$(pwd)
    cp -r csmith_record_2.3.0_t1 csmith_record_2.3.0_t$i
    sed -i -e 's/training_prob_t1/training_prob_t$i' csmith_record_2.3.0_t$i/src/Record.cpp
    cd ${PWDPATH}/csmith_record_2.3.0_t$i/build
    ../configure --prefix=${PWDPATH}/csmith_record_2.3.0_t$i/install_files
    make -j4 && make install
done
