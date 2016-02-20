#!/bin/sh

cd imp/
TEST_DIR=db/test
if [ -z "$(ls $TEST_DIR)" ]; then
    echo "Nothing in imp/$TEST_DIR"
    exit 1
fi
TEST_DAY=$TEST_DIR/$(ls $TEST_DIR -1 | tail -1)
if [ -z "$(ls $TEST_DAY)" ]; then
    echo "Nothing in imp/$TEST_DAY"
    exit 1
fi
TEST=$TEST_DAY/$(ls $TEST_DAY -1 | tail -1)
if [ -z "$(ls $TEST)" ]; then
    echo "Nothing in imp/$TEST"
    exit 1
fi
DB=$(ls $TEST/*.db) 2> /dev/null
if [ -z "$DB" ]; then
    echo "No database found in imp/$TEST"
    exit 1
fi
echo "Running on database imp/$DB"
python server.py -d $DB


