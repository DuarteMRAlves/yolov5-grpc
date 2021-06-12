#!/bin/bash

# By default output to src
if [[ $# -eq 0 ]]; then
  OUTPUT=yolov5/
else
  OUTPUT=$1
fi

python -m grpc_tools.protoc -I. \
  --proto_path=protos/ \
  --python_out=$OUTPUT \
  --grpc_python_out=$OUTPUT \
  yolov5_service.proto