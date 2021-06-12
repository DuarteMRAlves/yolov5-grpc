# Yolov5 gRPC

## Overview

This project provides a [gRPC](https://grpc.io) service that interfaces with the [YoloV5 model](https://github.com/ultralytics/yolov5) by [Ultralytics](https://github.com/ultralytics) for object detection.
It uses the YoloV5s model in order to detect the objects.

<p align="center">
    <img 
        src="assets/Bus-detection.png"
        alt="YoloV5 Bus Image Detection Demo"
        width="400">
</p>

## Usage

### Service Deployment

The service can be deployed as a docker image by executing the following command 
*(The first execution will take longer as the image will be downloaded)*:

```shell
$ docker run --rm -p 8061:8061 --ipc=host sipgisr/yolov5-grpc:latest
```

### Calling the service

You can call the service with the defined gRPC method. 
For an example, see the [test_yolo file](tests/test_yolo.py),
where we define a simple client that receives an image, calls the service and displays the results.

You can run the test file by executing the following steps:

* Ensure you have a working python installation with the packages grpcio, grpcio-tools, matplotlib and Pillow.

* Download the [test_yolo.py](tests/test_yolo.py) and the [yolov5_service.proto](protos/yolov5_service.proto) files into a single directory.

* Compile the protobuf code necessary to interact with the service:

```shell
$ python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. yolov5_service.proto
```

* Run the test script *(Ensure the docker image is running locally at 8061)*:

```shell
$ python test_yolo.py <path_to_some_image>
```

## Service interface

The interface for the gRPC service is defined in a [yolov5_service.proto](protos/yolov5_service.proto).
It receives an image and returns a list of detected objects, where each object is defined as:
```proto
message DetectedObject {
    string class_name = 1;
    uint32 class_idx = 2;
    Point p1 = 3;
    Point p2 = 4;
    double conf = 5;
}

message Point {
    double x = 1;
    double y = 2;
}
```

Here, class name and index specify the predicted class for the object, 
and the index of that class in the classes list.

The points specify relative coordinates of a rectangular boundary box that identifies the position of the object,
and conf indicates the model confidence in the prediction.
