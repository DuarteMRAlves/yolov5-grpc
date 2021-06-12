import argparse
import grpc
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import PIL.Image

import yolov5_service_pb2 as yolov5_service
import yolov5_service_pb2_grpc as yolov5_service_grpc


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


def detect_objects(stub, image_path):
    """
    Detects the objects in a single image
    by calling the server

    Returns:
        The DetectedPoses proto message with the
        estimated poses

    """
    print(f'Estimating image: \'{image_path}\'')
    with open(image_path, 'rb') as fp:
        image_bytes = fp.read()
    request = yolov5_service.Image(data=image_bytes)
    return stub.detect(request)


def get_point_coords(point, width, height):
    """
    Computes the absolute coordinates of the given point
    from the relative coordinates and the given width and height

    Args:
        point: point with the relative coordinates of the point
        width: width of the original image
        height: height of the original image

    Returns:
        Tuple in the form (absolute x coord, absolute y coord)

    """
    return point.x * width, point.y * height


def next_colour():
    while True:
        yield from ['r', 'g', 'b', 'c', 'y']


def display_object(ax, obj, width, height, colour):
    """
    Displays the box of the detected object in a matplotlib ax

    Args:
        ax: ax to draw the box
        obj: detected object to display
        width: width of the original image
        height: height of the original image
        colour: colour for the object box

    Returns:

    """
    x_min, y_max = get_point_coords(obj.p1, width, height)
    x_max, y_min = get_point_coords(obj.p2, width, height)

    rect_origin = (x_min, y_min)
    rect_width = x_max - x_min
    rect_height = y_max - y_min

    rect = patches.Rectangle(
        rect_origin,
        rect_width,
        rect_height,
        linewidth=1,
        edgecolor=colour,
        facecolor='none')

    ax.add_patch(rect)

    obj_class = obj.class_name
    obj_conf = obj.conf
    # Add text on top of image
    ax.text(
        x_min + 1,
        y_max - 5,
        f'{obj_class} ({int(obj_conf * 100)}%)',
        color='w',
        fontsize=8,
        bbox=dict(facecolor=colour, linewidth=0, boxstyle='square,pad=0.1'))


def display_objects(image_path, detected_objects):
    """
    Displays the objects using matplotlib

    Args:
        image_path: path for the original image sent for detection
        detected_objects: DetectedObjects proto message sent by the server

    Returns:

    """
    img = PIL.Image.open(image_path)
    width = img.width
    height = img.height
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(img)
    colour_gen = next_colour()
    for obj in detected_objects.objects:
        display_object(ax, obj, width, height, next(colour_gen))
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)
    plt.show()


def main():
    args = parse_args()
    image_path = args.image
    target = 'localhost:8061'
    with grpc.insecure_channel(target) as channel:
        stub = yolov5_service_grpc.YoloV5Stub(channel)
        try:
            detected_objects = detect_objects(stub, image_path)
            display_objects(image_path, detected_objects)
        except grpc.RpcError as rpc_error:
            print('An error has occurred:')
            print(f'  Error Code: {rpc_error.code()}')
            print(f'  Details: {rpc_error.details()}')


if __name__ == '__main__':
    main()
