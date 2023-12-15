#!/bin/bash -l

PYTHON=$(which python3.10)
echo "PYTHON=${PYTHON}"

$PYTHON /check_changelog.py
