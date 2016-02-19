#!/bin/bash

DBNAME="db/test/$(date -Ins).db"
pushd imp
python server.py -d "$DBNAME" &> test_server.log &
popd
echo $! > test.pid
sleep 0.5
casperjs test tests/
kill %%
