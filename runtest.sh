#!/bin/bash

# Killing the runtest script will kill all the children
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

(
cd imp/
DBNAME="db/test/$(date -Ins | sed 's|T|/|; s|,|/|').db"
python server.py -d "$DBNAME" &> test_server.log
) &

sleep 1

casperjs test tests/
