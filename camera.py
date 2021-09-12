print("Import cv2")
import cv2
print("Import time")
import time
print("Import threading")
import threading

print("Import PiCamera")
from picamera import PiCamera
print("Import PiRGBArray")
from picamera.array import PiRGBArray


class StreamCamera:

	def __init__(self, config, queue):

		self.camera = PiCamera()
		self.resolution = config.get("resolution", (640, 480))
		self.framerate = config.get("framerate", 2)

		self.camera.resolution = self.resolution
		self.camera.framerate = self.framerate
		self.raw_capture = None
		self.push_frames = False

		self.queue = queue
		self.thread = None

	def initialize_camera(self):
		self.raw_capture = PiRGBArray(self.camera, size=self.resolution)
		time.sleep(0.5)

	def _capture_thread(self):
		if self.raw_capture is None:
			return

		time_last_capture = time.time()
		for frame in self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True):
			image = frame.array
			self.raw_capture.truncate(0)
			
			capture_send_threshold = time_last_capture + float(1) / float(self.framerate)
			dt = time.time()
			if dt > capture_send_threshold:
				self.queue.put(image)
				time_last_capture = dt

			if not self.push_frames:
				return
				
	def start_capture(self):
		
		if self.thread is not None:
			return

		self.push_frames = True
		self.thread = threading.Thread(
			target=self._capture_thread
			# args=(self,)
		)

		self.thread.start()

	def stop_capture(self):

		if self.thread is None:
			return

		self.push_frames = False
		self.thread.join()
		time.sleep(0.5)
		self.thread = None

	
if __name__ == '__main__':
	import queue

	q = queue.Queue()

	sc = StreamCamera(
		{
			"resolution": (640, 480),
			"framerate": 2
		},
		q
	)

	sc.initialize_camera()
	sc.start_capture()

	idx = 0
	while idx < 10:

		q.get()

		idx += 1

	sc.stop_capture()