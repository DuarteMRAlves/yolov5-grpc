#!/bin/bash

# By default output to src
if [[ $# -eq 0 ]]; then
  OUTPUT=tests/
else
  OUTPUT=$1
fi

python -m grpc_tools.protoc -I. \
  --proto_path=tests/ \
  --python_out=$OUTPUT \
  --grpc_python_out=$OUTPUT \
  pipeline.proto