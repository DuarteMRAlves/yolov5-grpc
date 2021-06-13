import concurrent.futures as futures
import io
import logging
import time

import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

import visualization_service_pb2 as vis
import visualization_service_pb2_grpc as vis_grpc

_MAX_WORKERS = 10
_SERVICE_NAME = 'VisualizationService'
_PORT = 8061
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

_WIDTH = 300
_HEIGHT = 300
_LEGEND_BORDER_SIZE = 2


def colour_generator():
    while True:
        yield from ['red', 'green', 'blue', 'cyan', 'yellow']


class ObjectFrameDrawer:

    def __init__(self, overlay):
        self.__draw = PIL.ImageDraw.Draw(overlay)
        self.__width = overlay.width
        self.__height = overlay.height
        self.__colour_gen = colour_generator()
        self.__font = PIL.ImageFont.load_default()

    def __call__(self, obj: vis.DetectedObject):
        x_min, y_min = self.__point_coords(obj.p1)
        x_max, y_max = self.__point_coords(obj.p2)

        outline_colour = next(self.__colour_gen)

        self.__draw.rectangle(
            (x_min, y_min, x_max, y_max),
            outline=outline_colour,
            width=2)

        legend_text = f'{obj.class_name} ({int(obj.conf * 100)}%)'
        legend_width, legend_height = self.__font.getsize(legend_text)
        legend_bbox_pos = (
            x_min,
            y_min - legend_height - 2 * _LEGEND_BORDER_SIZE,
            x_min + legend_width + 2 * _LEGEND_BORDER_SIZE,
            y_min
        )
        legend_pos = (
            x_min + _LEGEND_BORDER_SIZE,
            y_min - legend_height - _LEGEND_BORDER_SIZE
        )

        self.__draw.rectangle(
            legend_bbox_pos,
            fill=(0, 0, 0, 128),
            outline=outline_colour,
            width=2
        )

        self.__draw.text(
            legend_pos,
            legend_text,
            (255, 255, 255),
            font=self.__font
        )

    def __point_coords(self, point: vis.Point):
        return point.x * self.__width, point.y * self.__height


class VisualizationService(vis_grpc.VisualizationServiceServicer):
    """
    gRPC service to receive and process the received image
    It resizes the images and adds the categories and attributes
    so that they can be displayed
    """

    def __init__(self, current_image):
        self.__current_img = current_image

    def Visualize(self, request: vis.Image, context):
        image_bytes = request.image.data
        detected_objects = request.objects.objects

        img = PIL.Image.open(io.BytesIO(image_bytes))
        img = img.resize((_WIDTH, _HEIGHT))
        img = img.convert('RGBA')

        overlay = PIL.Image.new('RGBA', img.size, (0, 0, 0, 0))
        drawer = ObjectFrameDrawer(overlay)
        for obj in detected_objects:
            drawer(obj)

        # Save image to bytes
        img = PIL.Image.alpha_composite(img, overlay)
        img = img.convert("RGB")

        image_bytes = io.BytesIO()
        img.save(image_bytes, format='jpeg')
        image_bytes = image_bytes.getvalue()
        self.__current_img.bytes = image_bytes
        return vis.Empty()


def run_server(shared_img):
    """
    Runs the gRPC server that receives the requests
    and updates the shared image with the most recent request

    Args:
        shared_img: shared image that should be updated by
                    the server with the most recent request

    """
    logging.basicConfig(level=logging.DEBUG)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    vis_grpc.add_VisualizationServiceServicer_to_server(
        VisualizationService(shared_img), server)
    service_names = (
        vis.DESCRIPTOR.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(service_names, server)
    server.add_insecure_port(f'[::]:{_PORT}')
    server.start()
    logging.info('Server started at [::]:%s', _PORT)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
