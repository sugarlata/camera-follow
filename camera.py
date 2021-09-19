print("Import cv2")
import cv2
print("Import time")
import time
print("Import threading")
import threading
print("Import numpy")
import numpy as np

print("Import PiCamera")
from picamera import PiCamera
print("Import PiRGBArray")
from picamera.array import PiRGBArray


lk_params = {
    'winSize': (4, 4),
    'maxLevel': 1,
    'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)

}


class StreamCamera:

	def __init__(self, config, streamingQueue, controlQueue):

		self.camera = PiCamera()
		self.resolution = config.get("resolution", (640, 480))
		self.framerate = config.get("framerate", 4)

		self.camera.resolution = self.resolution
		self.camera.framerate = self.framerate
		self.raw_capture = None

		self.streamingQueue = streamingQueue
		self.controlQueue = controlQueue
		self.thread = None

		self.orig_point = None
		self.point = None
		self.point_in_wait = None
		self.following = False

	def initialize_camera(self):
		self.raw_capture = PiRGBArray(self.camera, size=self.resolution)
		time.sleep(0.5)

	def set_point(self, x, y):
		self.orig_point = (int(x), int(y))
		self.point_in_wait = np.array([[x, y]], dtype = np.float32)

	def start_following(self):
		self.following = True

	def stop_following(self):
		self.following = False

	def _capture_thread(self):
		if self.raw_capture is None:
			return

		time_last_capture = time.time()
		last_gray_image = None
		for frame in self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True):
			image = frame.array
			image_height = image.shape[0]
			image_width = image.shape[1]
			gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			dx = 0
			dy = 0

			if self.point_in_wait is not None:
				self.point = self.point_in_wait
				self.point_in_wait = None

			if self.point is not None:
				cv2.circle(image, self.orig_point, 5, (0,0,255), 2)
			
			if self.following and last_gray_image is not None and self.point is not None:
				# print('Starting Calculation - Optical Flow')
				new_point, status, error = cv2.calcOpticalFlowPyrLK(
					last_gray_image,
					gray_image,
					self.point,
					None,
					**lk_params
				)
				# print('Finished Calculation')
				self.point = new_point
				x, y = new_point.ravel()

				dx = x - (image_width / 2)
				dy = (image_height / 2) - y
				cv2.circle(image, (int(x), int(y)), 5, (0,255,0), 3)

			self.raw_capture.truncate(0)
			
			capture_send_threshold = time_last_capture + float(1) / float(self.framerate)
			dt = time.time()
			if dt > capture_send_threshold:
				self.streamingQueue.put(image)
				self.controlQueue.put((dx, dy))
				time_last_capture = dt

			last_gray_image = gray_image.copy()

	def start_capture(self):
		
		if self.thread is not None:
			return

		self.thread = threading.Thread(
			target=self._capture_thread
			# args=(self,)
		)

		self.thread.start()

	def stop_capture(self):

		if self.thread is None:
			return

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