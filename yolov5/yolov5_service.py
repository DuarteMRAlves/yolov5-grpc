import concurrent.futures as futures
import io
import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import logging
import torch
import PIL.Image

import yolov5_service_pb2 as yolov5_service
import yolov5_service_pb2_grpc as yolov5_service_grpc


_SERVICE_NAME = 'YoloV5'
_MODEL_REPO = 'ultralytics/yolov5'
_MODEL_VERSION = 'yolov5s'
_PORT = 8061


class YoloV5Service(yolov5_service_grpc.YoloV5Servicer):

    def __init__(self):
        # Model for file/URI/PIL/cv2/np inputs and NMS
        self.__model = torch.hub.load(_MODEL_REPO, _MODEL_VERSION, pretrained=True)

    def detect(self, request, context):
        """
        Receives a request to detect objects and
        replies with all the detected objects in the image

        Args:
            request: Request with the bytes of the image to process
            context: Context for the gRPC call

        Returns:
            The DetectedObjects protobuf message with the objects
            detected in the image

        """
        img_bytes = request.data
        img = PIL.Image.open(io.BytesIO(img_bytes))
        # Fix for PIL Images need file name in model
        img.filename = "file"
        with torch.no_grad():
            results = self.__model(img, size=640)
        return self.__build_detected_objects(results)

    def __build_detected_objects(self, results):
        # Only one image in each prediction so we can access predictions with [0]
        # Get normalized values with xyxyn
        objects = (self.__build_detected_object(line, results.names) for line in results.xyxyn[0])
        return yolov5_service.DetectedObjects(objects=objects)

    def __build_detected_object(self, obj, names):
        p1 = self.__build_point_from_2x1tensor(obj[:2])
        p2 = self.__build_point_from_2x1tensor(obj[2:4])
        conf = obj[-2]
        class_idx = int(obj[-1])
        class_name = names[class_idx]
        return yolov5_service.DetectedObject(
            class_name=class_name,
            class_idx=class_idx,
            p1=p1,
            p2=p2,
            conf=conf
        )

    @staticmethod
    def __build_point_from_2x1tensor(tensor):
        return yolov5_service.Point(x=tensor[0], y=tensor[1])


def main():
    """
    Runs the server and waits for its termination
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    yolov5_service_grpc.add_YoloV5Servicer_to_server(
        YoloV5Service(),
        server
    )
    service_names = (
        yolov5_service.DESCRIPTOR.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(service_names, server)
    target = f'[::]:{_PORT}'
    server.add_insecure_port(target)
    logging.info('Starting YoloV5 server at %s', target)
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(
        format='[ %(levelname)s ] %(asctime)s (%(module)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)
    main()
