from enum import Enum
from app.models import Normalized, TrackingModeEnum
from math import sqrt
from app.eventbus import bus
from time import time_ns
import cv2

class Tracking():
    def __init__(self, bus=None, distance = 0.5, speed = 1, debug = False) -> None:
        self.bus = bus
        self.debug = debug
        self.classifier = cv2.CascadeClassifier("app/data/haarcascade_frontalface_default.xml")
        self.tracking_mode = TrackingModeEnum.FACE
        self.distance = distance
        self.speed = speed
        self.last_normalized_point = None
        self.last_measurement = time_ns()

        if self.bus:
            self.bus.subscribe("camera_frame")(self.on_frame)

    def debug_frame(self, frame: bytes):
        if self.debug:
            h, w, _c = frame.shape
            cv2.ellipse(frame, (w//2, h//2), (round(self.distance * (w/2)), round(self.distance * (h/2))), 0, 0, 360, (255, 0, 255), 2)
            cv2.circle(frame, (w//2, h//2), 1, (0, 0, 200), -1)

            ''' Show the debug frame '''
            cv2.imshow("Tracking", frame)
            cv2.waitKey(1)

    def normal_tracking(self, frame: bytes, normal: Normalized):
        ''' Track a normal point on the frame '''
        h, w, _c = frame.shape
        distance_from_center = sqrt(normal.x**2 + normal.y**2)
        to_target = None

        # Moving speed
        measure_time = time_ns()
        speed = 0
        if self.last_normalized_point is not None:
            normal_speed_x = (normal.x - self.last_normalized_point.x) / ((time_ns() - self.last_measurement) / 1000000000)
            normal_speed_y = (normal.y - self.last_normalized_point.y) / ((time_ns() - self.last_measurement) / 1000000000)
            speed = sqrt(normal_speed_x**2 + normal_speed_y**2)

        self.last_measurement = measure_time
        self.last_normalized_point = normal

        # If outside of the circle in a resonable speed. Move to target.
        if distance_from_center > self.distance:
            xcenter = round(((w/2)*normal.x) + (w/2))
            ycenter = round(((h/2)*normal.y) + (h/2))

            if self.debug:
                print(f"Tracking point at ({normal.x}, {normal.y}) with speed {speed}")
                if speed < self.speed:
                    cv2.circle(frame, (xcenter, ycenter), 5, (0, 255, 0), -1)
                else:
                    cv2.circle(frame, (xcenter, ycenter), 5, (0, 0, 255), -1)

            if speed < self.speed:
                to_target = normal
                if self.bus:
                    self.bus.emit("move_tracking", to_target)

        self.debug_frame(frame)
        return to_target

    def lost_tracking(self, frame: bytes):
        self.last_normalized_point = None
        self.last_measurement = time_ns()
        self.debug_frame(frame)

    def face_tracking(self, frame: bytes):
        ''' Search for a face in the frame and track it '''
        h, w, _c = frame.shape

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.classifier.detectMultiScale(
		gray, scaleFactor=1.05, minNeighbors=5, minSize=(200, 200),
		flags=cv2.CASCADE_SCALE_IMAGE)

        if faces is not None and len(faces) > 0:
            (x, y, wf, hf) = faces[0]
            xcenter = round(x + wf / 2)
            ycenter = round(y + hf / 2)

            normal = Normalized(x=((2*xcenter)/w)-1, y=((2*ycenter)/h)-1)
            return self.normal_tracking(frame, normal)
        else:
            return self.lost_tracking(frame)

    def object_tracking(self, frame: bytes):
        ''' Search for an object in the frame and track it '''
        # Implement object tracking logic here
        return None

    async def on_change_tracking_mode(self, mode: TrackingModeEnum) -> None:
        '''  Change the tracking mode'''
        self.lost_tracking()
        self.tracking_mode = mode

    async def on_frame(self, frame):
        ''' Track on the frame  '''
        if self.tracking_mode == TrackingModeEnum.FACE:
            return self.face_tracking(frame)
        elif self.tracking_mode == TrackingModeEnum.OBJECT:
            return self.object_tracking(frame)