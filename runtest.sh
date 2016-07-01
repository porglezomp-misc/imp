#!/bin/bash

# Killing the runtest script will kill all the children
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

(
cd imp/
server_path="db/test/$(date -Ins | sed 's|T|/|; s|,.*|/|')"
mkdir -p "${server_path}"
rm -rf db/test/latest
mkdir -p db/test/latest
dbname="${server_path}test.db"
logname="${server_path}server.log"
touch "${logname}" "${dbname}"
ln -f "${logname}" "$(pwd)/test_server.log"
ln -f "${logname}" "${dbname}" "$(pwd)/db/test/latest/"
python server.py -d "${dbname}" >"${logname}" 2>&1
) &

LOADED=false
for iter in {1..50}; do
    # If we successfully make a connection, we're done
    if curl localhost:8888 &> /dev/null; then
        LOADED=true
        break
    fi
    sleep 0.1
done

# If none of the connection attempts ever succeeded, then
# we should quit without attempting to run the test suite
if [ ! $LOADED ]; then
    echo "Connection to localhost:8888 failing after 5 seconds, giving up!"
    exit 1
fi

casperjs test tests/
