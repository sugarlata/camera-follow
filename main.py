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

print('Import threading')
from threading import Condition
print('Import flask')
from flask import Flask, send_from_directory, request, Response
print('Import flask_sock')
from flask_sock import Sock
print('Import waitress')
from waitress import serve
print('Import Simple PID')
from simple_pid import PID

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

# Camera Movement Control

pan_limits = (
    -41000,
    41000
)

tilt_limits = (
    -20000,
    30000
)

pid_x = PID(
    1,
    0.1,
    0.1,
    0
)

pid_y = PID(
    1,
    0.1,
    0.1,
    0
)

last_move = 0

enable_camera_move = False

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


def process_diff(diff, interval=2):

    dt = time.time()

    global last_move
    if last_move + interval > dt:
        return

    if not enable_camera_move:
        return

    dx, dy = diff

    delta_pan = pid_x(dx)
    pan = em_status['pan'] + delta_pan

    delta_tilt = pid_y(dy)
    tilt = em_status['tilt'] + delta_tilt

    # Enable Limits
    if pan < 0:
        pan = max(pan, pan_limits[0])
    if pan > 0:
        pan = min(pan, pan_limits[1])

    if tilt < 0:
        tilt = max(tilt, tilt_limits[0])
    if tilt > 0:
        tilt = min(tilt, tilt_limits[1])

    print("Pan ", pan)
    print("Tilt:", tilt)

    # emotimo_move_all(pan, tilt, 0)


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

        
def take_photo():

    print("Take Photo")


def receive_serial(data):
    print(data)


def receive_pts(data):
    print(data)


def receive_obj_tracking(data):
    print(data)


def receive_click(data):
    print(data)


def receive_camera(data):
    print(data)


class ImageClick:

    def post(self):
        json_body = json.loads(request.data.decode())
        try:
            sc.set_point(json_body['x'], json_body['y'])
        except Exception as e:
            print(e)
        return


# class CameraMove:

#     def post(self):
#         json_body = json.loads(request.data.decode())
#         try:
#             if json_body.get('action') == True:
#                 global enable_camera_move
#                 enable_camera_move = True
#             elif json_body.get('action') == False:
#                 global enable_camera_move
#                 enable_camera_move = False
#         except Exception as e:
#             print(e)
#         return


class CameraAPI:

    def post(self):
        json_body = json.loads(request.data.decode())
        
        if json_body.get('action') == 'start':
            sc.start_following()

        if json_body.get('action') == 'stop':
            sc.stop_following()
        
        return


class SerialClick:

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



class MoveClick:

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

    # Add WebSockets
    sock = Sock(app)

    @sock.route('/control')
    def control(ws):
        while True:
            data = ws.receive()


            print(data)

    @app.route('/camera-follow')
    def camera_follow():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favico.ico')
    
    def gen():
        while not q.empty():
            q.get()

        while streaming:
            image, diff = q.get()
            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            process_diff(diff)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @app.route('/video_feed')
    def video_feed():
        resp = Response(
            response=gen(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

        return resp

    @app.route('/camera-follow.js')
    def mouse_click():
        return send_from_directory(app.static_folder, 'camera-follow.js')

    try:
        app.run('0.0.0.0', port=8000)
        serve(app)
    finally:
        streaming = False
        sc.stop_capture()
        em.close_connection()
        time.sleep(2)
