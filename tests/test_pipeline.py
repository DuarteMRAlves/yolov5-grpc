import argparse
import grpc

import pipeline_pb2 as pipeline
import pipeline_pb2_grpc as pipeline_grpc


def parse_args():
    """
    Parses the command line arguments for the test

    Returns:
        The arguments to be used

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--yolo',
        default='localhost:8060',
        help='Location where the server with the yolo model is listening'
    )
    parser.add_argument(
        '--vis',
        default='localhost:8061',
        help='Location where the visualization server is listening'
    )
    parser.add_argument(
        'image',
        type=str,
        help='path to the image to send'
    )
    return parser.parse_args()


def send_image(yolo_stub, vis_stub, image_path):
    with open(image_path, 'rb') as fd:
        image_bytes = fd.read()
    image = pipeline.Image(data=image_bytes)
    detected_objects = yolo_stub.detect(image)
    request = pipeline.ImageWithObjects(
        image=image,
        objects=detected_objects
    )
    return vis_stub.Visualize(request)


def main():
    args = parse_args()
    image_path = args.image
    yolo_target = args.yolo
    vis_target = args.vis
    with grpc.insecure_channel(yolo_target) as yolo_channel, \
            grpc.insecure_channel(vis_target) as vis_channel:
        yolo_stub = pipeline_grpc.YoloV5Stub(yolo_channel)
        vis_stub = pipeline_grpc.VisualizationServiceStub(vis_channel)
        try:
            send_image(yolo_stub, vis_stub, image_path)
        except grpc.RpcError as rpc_error:
            print('An error has occurred:')
            print(f'  Error Code: {rpc_error.code()}')
            print(f'  Details: {rpc_error.details()}')


if __name__ == '__main__':
    main()
