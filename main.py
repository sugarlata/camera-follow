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

print('Import EmotimoSerial')
from emotimo_serial import EmotimoSerial

print('Import Serial')
import serial.tools.list_ports as list_ports


# Get Camera Ready
q = queue.Queue()
sc = StreamCamera(
    {"framerate": 10},
    q
)

sc.initialize_camera()
sc.start_capture()

streaming = True


# Get Emotimo Ready
em = EmotimoSerial()
em_ready = False

em_status = {
    "pan": 0,
    "tilt": 0,
    "slide": 0
}


def emotimo_open_serial():
    print("Opening Em Connection")
    em.open_connection()


def emotimo_close_serial():
    print("Closing Em Connection")
    em.close_connection()

def emotimo_ready_serial():
    global em_ready
    
    print("Setting Pulse Rate")
    em.set_pulse_rate(1, 20000)
    em.set_pulse_rate(2, 20000)
    em.set_pulse_rate(3, 20000)

    print("Zeroing all Motors")
    em.zero_all_motors()
    em_ready = True
    print("Em Now Ready")


def emotimo_move_all(pan, tilt, slide, ignore_slide=True):

    global em_ready
    global em_status

    if not em_ready:
        print("Em Unavailable")
        return

    em_ready = False

    print('Set Pan: %s' % str(pan))
    print('Set Tilt: %s' % str(tilt))
    print('Set Slide: %s' % str(slide))
    em.set_all(
        {
            "pan": pan,
            "tilt": tilt,
            "slide": slide
        },
        ignore_slide
    )

    em_status["pan"] = pan
    em_status["tilt"] = tilt
    em_status["slide"] = slide

    em_ready = True



def emotimo_move(action, pan_increment=1000, tilt_increment=1000, slide_increment=10000):

    global em_ready
    global em_status

    if not em_ready:
        print("Em Unavailable")
        return

    em_ready = False

    if action == 'left':
        cur_value = em_status['pan']
        cur_value -= pan_increment
        print('Set Pan: %s' % str(cur_value))
        em.set_pan(cur_value)
        em_status['pan'] = cur_value
        em_ready = True


    if action == 'right':
        cur_value = em_status['pan']
        cur_value += pan_increment
        print('Set Pan: %s' % str(cur_value))
        em.set_pan(cur_value)
        em_status['pan'] = cur_value
        em_ready = True

    if action == 'slide_left':
        cur_value = em_status['slide']
        cur_value -= slide_increment
        print('Set Slide: %s' % str(cur_value))
        em.set_slide(cur_value)
        em_status['slide'] = cur_value
        em_ready = True

    if action == 'slide_right':
        cur_value = em_status['slide']
        cur_value += slide_increment
        print('Set Slide: %s' % str(cur_value))
        em.set_slide(cur_value)
        em_status['slide'] = cur_value
        em_ready = True

    if action == 'up':

        cur_value = em_status['tilt']
        cur_value += tilt_increment
        print('Set Tilt: %s' % str(cur_value))
        em.set_tilt(cur_value)
        em_status['tilt'] = cur_value
        em_ready = True

    if action == 'down':
        cur_value = em_status['tilt']
        cur_value -= tilt_increment
        print('Set Tilt: %s' % str(cur_value))
        em.set_tilt(cur_value)
        em_status['tilt'] = cur_value
        em_ready = True

    if action == 'reset':
        print('Set Pan: 0')
        print('Set Tilt: 0')
        em.set_all({
            "pan": 0,
            "tilt": 0
        })
        em_status['pan'] = 0
        em_status['tilt'] = 0
        em_ready = True
        
    if action == 'zero':
        print('Changing Pan: 0')
        print('Changing Tilt: 0')
        em.zero_all_motors()
        em_status['pan'] = 0
        em_status['tilt'] = 0
        em_ready = True

        


class ImageClick(Resource):

    def post(self):
        json_body = json.loads(request.data.decode())
        try:
            sc.set_point(json_body['x'], json_body['y'])
        except Exception as e:
            print(e)
        return


class CameraAPI(Resource):

    def post(self):
        json_body = json.loads(request.data.decode())
        
        if json_body.get('action') == 'start':
            sc.start_following()

        if json_body.get('action') == 'stop':
            sc.stop_following()
        
        return


class SerialClick(Resource):

    def post(self):
        json_body = json.loads(request.data.decode())

        action = json_body.get('action')

        if action == 'open':
            emotimo_open_serial()

        if action == 'ready':
            emotimo_ready_serial()

        if action == 'close':
            emotimo_close_serial()

        return



class MoveClick(Resource):

    def post(self):
        json_body = json.loads(request.data.decode())
        
        action = json_body.get('action')

        if action in [
            'up',
            'down',
            'left',
            'right',
            'reset',
            'zero'
        ]:
            emotimo_move(action)

        if action == 'moveAll':
            emotimo_move_all(
                int(json_body.get("pan", 0)),
                int(json_body.get("tilt", 0)),
                int(json_body.get("slide", 0))
            )

        return



if __name__ == '__main__':

    # Initialize Flask
    app = Flask(__name__, static_folder="./html")
    api = Api(app)
    
    # Get Flask Ready
    api.add_resource(ImageClick, "/image-click")
    api.add_resource(SerialClick, "/serial")
    api.add_resource(MoveClick, "/move")
    api.add_resource(CameraAPI, "/camera")

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

    @app.route('/serial.js')
    def serial():
        return send_from_directory(app.static_folder, 'serial.js')

    @app.route('/move.js')
    def move():
        return send_from_directory(app.static_folder, 'move.js')

    @app.route('/camera.js')
    def camera():
        return send_from_directory(app.static_folder, 'camera.js')

    try:
        app.run('0.0.0.0', port=8000)
        serve(app)
    finally:
        streaming = False
        sc.stop_capture()
        em.close_connection()
        time.sleep(2)
