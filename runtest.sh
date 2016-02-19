#!/bin/bash

pushd imp
python server.py &> test_server.log &
popd
echo $! > test.pid
sleep 0.1
casperjs test tests/
kill %%
