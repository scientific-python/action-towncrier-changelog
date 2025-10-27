#!/bin/bash -l

PYTHON=$(which python3)
echo "PYTHON=${PYTHON}"

$PYTHON /check_changelog.py
