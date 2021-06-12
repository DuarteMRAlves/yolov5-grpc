import argparse
import grpc

import visualization_service_pb2 as vis
import visualization_service_pb2_grpc as vis_grpc


def parse_args():
    """
    Parses the command line arguments for the test

    Returns:
        The arguments to be used

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'image',
        type=str,
        help='path to the image to send'
    )
    return parser.parse_args()


def gen_point(x, y):
    return vis.Point(x=x, y=y)


def gen_detected_object(name, x1, y1, x2, y2, conf):
    return vis.DetectedObject(
        class_name=name,
        class_idx=1,
        p1=gen_point(x1, y1),
        p2=gen_point(x2, y2),
        conf=conf
    )


def send_image(stub, image_path):
    with open(image_path, 'rb') as fd:
        image_bytes = fd.read()
    image = vis.Image(data=image_bytes)
    detected_objects = vis.DetectedObjects(
        objects=(
            gen_detected_object('Object 1', 0.1, 0.5, 0.5, 0.1, 0.05),
            gen_detected_object('Object 2', 0.6, 0.5, 0.7, 0.2, 0.98)
        )
    )
    request = vis.ImageWithObjects(
        image=image,
        objects=detected_objects
    )
    return stub.Visualize(request)


def main():
    args = parse_args()
    image_path = args.image
    target = 'localhost:8061'
    with grpc.insecure_channel(target) as channel:
        stub = vis_grpc.VisualizationServiceStub(channel)
        try:
            send_image(stub, image_path)
        except grpc.RpcError as rpc_error:
            print('An error has occurred:')
            print(f'  Error Code: {rpc_error.code()}')
            print(f'  Details: {rpc_error.details()}')


if __name__ == '__main__':
    main()
