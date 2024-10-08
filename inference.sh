#!/bin/bash

cd $(dirname $0)

source .venv/bin/activate

cd tnktools/models

python -m server
