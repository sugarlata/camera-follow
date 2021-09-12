# import required modules
print("Starting Imports")
import time
from flask import Flask, render_template, Response
from picamera.array import PiRGBArray
from picamera import PiCamera
print("Starting CV2 Import")
import cv2
from camera import StreamCamera
import socket 
import io 
import queue
print("Finished Imports")

app = Flask(__name__)

q = queue.Queue()

sc = StreamCamera(
   {"framerate": 4},
   q
)

sc.initialize_camera()
sc.start_capture()

streaming = True


@app.route('/') 
def index(): 
   """Video streaming .""" 
   return render_template('index.html') 


def gen_frames():
   
   frame_count = 0
   
   while not q.empty():
      q.get()

   while streaming:
      image = q.get()

      print("Frame Count: %s" % str(frame_count))
      frame_count += 1
      # success, frame = camera.read()  # read the camera frame
      # if not success:
      #    break
      # else:
      ret, buffer = cv2.imencode('.jpg', image)
      image = buffer.tobytes()
      yield (b'--frame\r\n'
             b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')  # concat frame one by one and show result



@app.route('/video_feed') 
def video_feed(): 
   """Video streaming route. Put this in the src attribute of an img tag.""" 
   return Response(
      gen_frames(), 
      mimetype='multipart/x-mixed-replace; boundary=frame'
   ) 




if __name__ == '__main__': 
   try:
   	app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False) 
   finally:
      streaming = False
      sc.stop_capture()
