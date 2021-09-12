print('Import io')
import io
print('Import os')
import os
print('Import cv2')
import cv2
print('Import json')
import json
print('Import time')
import time
print('Import queue')
import queue
print('Import PiCamera')
import picamera

print('Import threading')
from threading import Condition
print('Import flask')
from flask import Flask, send_from_directory, request, Response
print('Import flask_restful')
from flask_restful import Api, Resource
print('Import waitress')
from waitress import serve

print('Import StreamCamera')
from camera import StreamCamera


class Page(Resource):

    def post(self):
        json_body = json.loads(request.data.decode())
        print(json.dumps(json_body, indent=4))
        return


if __name__ == '__main__':

    app = Flask(__name__, static_folder="./html")
    api = Api(app)
    
    q = queue.Queue()
    sc = StreamCamera(
        {"framerate": 4},
        q
    )

    sc.initialize_camera()
    sc.start_capture()

    streaming = True

    api.add_resource(Page, "/image-click")

    @app.route('/camera-follow')
    def camera_follow():
        return send_from_directory(app.static_folder, 'index.html')
    
    def gen():

        while not q.empty():
            q.get()

        while streaming:
            image = q.get()
            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @app.route('/video_feed')
    def video_feed():
        resp = Response(
            response=gen(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

        return resp

    @app.route('/mouse-click.js')
    def mouse_click():
        return send_from_directory(app.static_folder, 'mouse-click.js')

    try:
        app.run('0.0.0.0', port=8000)
        serve(app)
    finally:
        streaming = False
        sc.stop_capture()
        time.sleep(2)
