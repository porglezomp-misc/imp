#!/bin/bash

(cd imp && python server.py &> test_server.log) &
sleep 1
casperjs test tests/
kill $!
