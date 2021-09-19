print('Import io')
import io
print('Import os')
import os
print('Import base64')
import base64
print('Import cv2')
import cv2
print('Import json')
import json
print('Import time')
import time
print('Import queue')
import queue
print('Import threading')
import threading

print('Import flask')
from flask import Flask, send_from_directory, request, Response
print('Import flask_sock')
from flask_sock import Sock
print('Import Simple PID')
from simple_pid import PID

print('Import StreamCamera')
from camera import StreamCamera

print('Import EmotimoSerial')
from emotimo_serial import EmotimoSerial

print('Import adb module')
from adb_android import ADBControl

print('Import Serial')
import serial.tools.list_ports as list_ports


# Get Camera Ready
streamingQ = queue.Queue()
controlQ = queue.Queue()
sc = StreamCamera(
    {"framerate": 10},
    streamingQ,
    controlQ
)

sc.initialize_camera()
sc.start_capture()

streaming = True


# Android Debug Bridge Setup
adb = ADBControl({})

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
    -50000,
    50000
)

tilt_limits = (
    -20000,
    30000
)

pid_x = PID(
    20,
    0,
    0,
    0
)

pid_y = PID(
    20,
    0,
    0,
    0
)

enable_pts_move = False
control_loop_enabled = True
camera_shooting = False
pts_interval = 1

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

    # Enforce Limits
    if pan < 0:
        pan = max(pan, pan_limits[0])
    if pan > 0:
        pan = min(pan, pan_limits[1])

    if tilt < 0:
        tilt = max(tilt, tilt_limits[0])
    if tilt > 0:
        tilt = min(tilt, tilt_limits[1])

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


def emotimo_move(pts, direction, pan_increment=1000, tilt_increment=1000, slide_increment=10000):

    global em_ready
    global em_status

    if not em_ready:
        print("Em Unavailable")
        return

    em_ready = False

    if pts == 'tilt' and direction == 'up':
        cur_value = em_status['tilt']
        cur_value += tilt_increment
        print('Set Tilt: %s' % str(cur_value))
        em.set_tilt(cur_value)
        em_status['tilt'] = cur_value
        em_ready = True

    if pts == 'tilt' and direction == 'down':
        cur_value = em_status['tilt']
        cur_value -= tilt_increment
        print('Set Tilt: %s' % str(cur_value))
        em.set_tilt(cur_value)
        em_status['tilt'] = cur_value
        em_ready = True

    if pts == 'pan' and direction == 'left':
        cur_value = em_status['pan']
        cur_value -= pan_increment
        print('Set Pan: %s' % str(cur_value))
        em.set_pan(cur_value)
        em_status['pan'] = cur_value
        em_ready = True


    if pts == 'pan' and direction == 'right':
        cur_value = em_status['pan']
        cur_value += pan_increment
        print('Set Pan: %s' % str(cur_value))
        em.set_pan(cur_value)
        em_status['pan'] = cur_value
        em_ready = True

    if pts == 'slide' and direction == 'left':
        cur_value = em_status['slide']
        cur_value -= slide_increment
        print('Set Slide: %s' % str(cur_value))
        em.set_slide(cur_value)
        em_status['slide'] = cur_value
        em_ready = True

    if pts == 'slide' and direction == 'right':
        cur_value = em_status['slide']
        cur_value += slide_increment
        print('Set Slide: %s' % str(cur_value))
        em.set_slide(cur_value)
        em_status['slide'] = cur_value
        em_ready = True

    if pts == 'all' and direction == 'origin':
        print('Set Pan: 0')
        print('Set Tilt: 0')
        print('Ignoring Slide')
        
        em.set_all({
            "pan": 0,
            "tilt": 0
        }, ignore_slide=True)

        em_status['pan'] = 0
        em_status['tilt'] = 0
        em_ready = True
        
    if pts == 'all' and direction == 'reset':
        print('Changing Pan: 0')
        print('Changing Tilt: 0')
        em.zero_all_motors()
        em_status['pan'] = 0
        em_status['tilt'] = 0
        em_ready = True

       
def process_diff(dx, dy):

    print('')
    print('DX: ', dx)
    print('DY: ', dy)

    dt = time.time()

    # delta_pan = dx
    delta_pan = -1 * pid_x(dx)
    pan = int(em_status['pan']) + int(delta_pan)

    # delta_tilt = dy
    delta_tilt = -1 * pid_y(dy)
    tilt = int(em_status['tilt']) + int(delta_tilt)

    print('Delta Pan: ', delta_pan)
    print('Delta Tilt: ', delta_tilt)

    # Enforce Limits
    if pan < 0:
        pan = max(pan, pan_limits[0])
    if pan > 0:
        pan = min(pan, pan_limits[1])

    if tilt < 0:
        tilt = max(tilt, tilt_limits[0])
    if tilt > 0:
        tilt = min(tilt, tilt_limits[1])

    print("Pan: ", pan)
    print("Tilt: ", tilt)

    emotimo_move_all(pan, tilt, 0)

 
def control_loop(controlQ, pixel_deadzone=0):

    global control_loop_enabled

    pts_last_time = 0

    while control_loop_enabled:
        
        dt = time.time()
        reset_dt = False

        if camera_shooting:
            
            if pts_last_time + pts_interval < dt:
                reset_dt = True
                camera_take_shot()

        if enable_pts_move:

            while not controlQ.empty():
                dx, dy = controlQ.get()
            
            if abs(dx) < pixel_deadzone:
                dx = 0

            if abs(dy) < pixel_deadzone:
                dy = 0


            if pts_last_time + pts_interval < dt:
                process_diff(dx, dy)
                reset_dt = True

        if reset_dt:
            pts_last_time = dt


def camera_take_shot():
    adb.take_photo()

def receive_serial(data):

    action = data.get('action')    

    if action == 'open':
        emotimo_open_serial()

    if action == 'ready':
        emotimo_ready_serial()

    if action == 'close':
        emotimo_close_serial()


def receive_pts(data):

    global enable_pts_move
    
    action = data.get('action')

    if action == 'move':

        detail = data.get('detail', {})
        pts = detail.get('pts')
        direction = detail.get('direction')
        emotimo_move(pts, direction)

    if action == 'reset-origin':

        detail = data.get('detail', {})
        pts = detail.get('pts')
        emotimo_move(pts, 'reset')

    if action == 'move-all':
        pan = data.get('detail', {}).get('pan', 0)
        tilt = data.get('detail', {}).get('tilt', 0)
        slide = data.get('detail', {}).get('slide', 0)
        emotimo_move_all(int(pan), int(tilt), slide)

    if action == 'follow':

        if data.get('detail') == 'enable':
            enable_pts_move = True

        if data.get('detail') == 'disable':
            enable_pts_move = False


def receive_obj_tracking(data):
    
    action = data.get('action')

    if action:
        sc.start_following()
    else:
        sc.stop_following()
    

def receive_click(data):
    
    action = data.get('action')

    if action == 'pos-update':

        x = data.get('position', {}).get('x', 0)
        y = data.get('position', {}).get('y', 0)

        sc.set_point(x, y)


def receive_camera(data):
    global pts_interval
    global camera_shooting
    
    action = data.get('action')
    print(action)

    if action == 'take-shot':
        camera_take_shot()

    if action == 'start-interval':
        camera_shooting = True

    if action == 'stop-interval':
        camera_shooting = False

    if action == 'set-interval':
        pts_interval = float(data.get('detail', {}).get('interval', 2))

    if action == 'modify-interval':
        print('Too Hard for the moment')




if __name__ == '__main__':

    # Initialize Flask
    app = Flask(__name__, static_folder="./html")

    # Add WebSockets
    sock = Sock(app)

    @sock.route('/control')
    def control(ws):

        socket_open = True
        while socket_open:
            
            resp_data = ws.receive()

            if resp_data == 'finish':
                socket_open = False
                continue

            data = json.loads(resp_data)

            module = data.get('module', '')

            if module == 'serial':
                receive_serial(data)

            if module == 'pts-move':
                receive_pts(data)

            if module == 'obj-track':
                receive_obj_tracking(data)

            if module == 'click-position':
                receive_click(data)

            if module == 'camera':
                receive_camera(data)

    @sock.route('/live')
    def live(ws):
        
        resp = ws.receive()

        if resp == 'begin':
            stream = True
        else:
            stream = False

        while stream:

            resp = ws.receive()
            if resp == 'finish':
                stream = False
                continue

            while not streamingQ.empty():
                image = streamingQ.get()
    
            _, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()

            send_data = base64.b64encode(frame).decode()
            ws.send(send_data)

        ws.close(1000, 'Closing WS Connection')
            
    @app.route('/camera-follow')
    def camera_follow():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favico.ico')
    
    @app.route('/camera-follow.js')
    def mouse_click():
        return send_from_directory(app.static_folder, 'camera-follow.js')

    # PTS  and Photo Taking Control Thread
    control_thread = threading.Thread(target=control_loop, args=(controlQ,))
    control_thread.start() 

    try:
        app.run('0.0.0.0', port=8000)
    finally:
        control_loop_enabled = False
        control_thread.join()
        streaming = False
        sc.stop_capture()
        em.close_connection()
        time.sleep(2)
