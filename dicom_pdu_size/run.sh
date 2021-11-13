#!/usr/bin/env bash

mkdir -p server_data
rm -rf server_data/*

export DICOM_FILE="1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.451.0.dcm"
export NUM_JOBS="${NUM_JOBS:-100}"
export TIMEFORMAT="%R"

export MAXIMUM_PDU_SIZE=16382
docker-compose up --detach --force-recreate
time (seq 1 "$NUM_JOBS" | xargs -I {} -P 10 python3 client.py "$DICOM_FILE" localhost 11112 --pdu-size 16832 2> /dev/null > 16KB.txt) 2> 16KB_time.txt

export MAXIMUM_PDU_SIZE=100000
docker-compose up --detach --force-recreate
time (seq 1 "$NUM_JOBS" | xargs -I {} -P 10 python3 client.py "$DICOM_FILE" localhost 11112 --pdu-size 100000 2> /dev/null > 100KB.txt) 2> 100KB_time.txt

export MAXIMUM_PDU_SIZE=500000
docker-compose up --detach --force-recreate
time (seq 1 "$NUM_JOBS" | xargs -I {} -P 10 python3 client.py "$DICOM_FILE" localhost 11112 --pdu-size 500000 2> /dev/null > 500KB.txt) 2> 500KB_time.txt

export MAXIMUM_PDU_SIZE=1000000
docker-compose up --detach --force-recreate
time (seq 1 "$NUM_JOBS" | xargs -I {} -P 10 python3 client.py "$DICOM_FILE" localhost 11112 --pdu-size 1000000 2> /dev/null > 1MB.txt) 2> 1MB_time.txt

export MAXIMUM_PDU_SIZE=10000000
docker-compose up --detach --force-recreate
time (seq 1 "$NUM_JOBS" | xargs -I {} -P 10 python3 client.py "$DICOM_FILE" localhost 11112 --pdu-size 10000000 2> /dev/null > 10MB.txt) 2> 10MB_time.txt

export MAXIMUM_PDU_SIZE=20000000
docker-compose up --detach --force-recreate
time (seq 1 "$NUM_JOBS" | xargs -I {} -P 10 python3 client.py "$DICOM_FILE" localhost 11112 --pdu-size 20000000 2> /dev/null > 20MB.txt) 2> 20MB_time.txt

docker-compose down
find . -name '*_time.txt' | xargs -I {} bash -c 'echo {} & cat {}'