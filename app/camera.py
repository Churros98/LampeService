import cv2
import asyncio

class Camera():
    ''' Camera device '''
    def __init__(self, bus=None, device = 0, fps = 5) -> None:
        self.capture = cv2.VideoCapture(device)
        self.fps = fps
        self.bus = bus
        if not self.capture.isOpened():
            raise IOError("Cannot open camera")

    async def snapshot(self) -> bytes:
        frame = self.capture.read()
        ret, jpeg = cv2.imencode('.jpg', frame[1])
        return jpeg.tobytes()

    async def read(self):
        ''' Camera frame stream '''
        while self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                yield frame
            else:
                raise IOError("Failed to grab frame") 

    async def update(self) -> None:
        ''' Update the camera feed '''
        if self.bus is None:
            return

        async for frame in self.read():
            self.bus.emit("camera_frame", frame)
            await asyncio.sleep(1/self.fps)

    def close(self) -> None:
        ''' Close the camera feed '''
        self.capture.release()