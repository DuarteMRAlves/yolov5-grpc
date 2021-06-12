import flask
import logging
import threading
import time

import visualization_service


class SharedImage:
    """
    This class stores the bytes of an image shared
    among two threads
    It will be used as the last received image for display
    """

    def __init__(self):
        self.__bytes = None

    @property
    def bytes(self):
        return self.__bytes

    @bytes.setter
    def bytes(self, value):
        self.__bytes = value

    def __str__(self):
        return str(self.__bytes)


def run_grpc_server(current_image):
    """Start the gRPC Visualization Service and blocks"""
    visualization_service.run_server(current_image)


def generate_feed(current_image):
    """
    Generates a feed of frames that
    results in the multipart message
    Yields:
        byte stream with the frames
    """
    while True:
        if current_image.bytes:
            frame = b''.join(
                (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n',
                 current_image.bytes,
                 b'\r\n'))
            yield frame
        time.sleep(0.1)


def create_app():
    """
    Function to create the flask app.
    It also starts the gRPC server
    Returns:
        The flask app to be used
    """
    logging.basicConfig(
        format='[ %(levelname)s ] %(asctime)s (%(module)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)
    flask_app = flask.Flask(__name__)
    current_image = SharedImage()
    threading.Thread(
        target=run_grpc_server,
        args=(current_image,)).start()

    @flask_app.route('/')
    def index():
        """Video Streaming home page
        Returns:
            The html to render the homepage
        """
        return flask.render_template('index.html')

    @flask_app.route('/video_feed')
    def video_feed():
        """ Route for the video feed
        :return: Http multipart response with generator
                 creating frames as they arrive
        """
        logging.debug('Received Client Connection')
        return flask.Response(
            generate_feed(current_image),
            mimetype='multipart/x-mixed-replace; boundary=frame')

    return flask_app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8062, threaded=True)