import asyncio

from app.audio import Audio
from app.camera import Camera
from app.controller import Controller
from app.light import Light
from app.tracking import Tracking
from app.eventbus import bus
from app.models import Angle, EncodedAngle, Perc, Position

from typing import Annotated
from fastapi import FastAPI, Form, Response
from fastapi.encoders import jsonable_encoder

_tracking = Tracking(bus=bus)
camera = Camera(bus=bus, fps=5)
light = Light(bus=bus, min=20, max=100)
controller = Controller(motor_device="/dev/ttys006", baudrate=9600, bus=bus)
audio = Audio(bus=bus)

async def start_sensors():
    asyncio.create_task(camera.update())
    asyncio.create_task(controller.update())
    asyncio.create_task(audio.update())

async def stop_sensors():
    await camera.close()
    await light.close()
    await controller.close()
    await audio.close()

app = FastAPI(on_startup=[start_sensors], on_shutdown=[stop_sensors])

# Motors and positional control
@app.get("/health")
async def health():
    return jsonable_encoder(True)

@app.get("/lock")
async def lock_motors():
    # Replace with actual bus logic if available
    bus.emit("controller_torque", True)
    return None

@app.get("/unlock")
async def unlock_motors():
    bus.emit("controller_torque", False)
    return None

@app.get("/angle/{name}")
async def get_angle(name: str):
    return jsonable_encoder(controller.motor(name).get_angle())

@app.post("/angle/{name}")
async def set_angle(name: str, angle: Annotated[Angle, Form()]):
    bus.emit("controller_move_angles", {name: angle})
    return None

@app.get("/encoder/{name}")
async def get_encode(name: str):
    return jsonable_encoder(controller.motor(name).get_encoded_angle())

@app.post("/encoder/{name}")
async def set_encode(name: str, angle: Annotated[EncodedAngle, Form()]):
    bus.emit("controller_move_encodeds", {name: angle})
    return None

@app.post("/position")
async def set_position(position: Annotated[Position, Form()]):
    bus.emit("controller_move_position", position)
    return None

# Light control
@app.get("/light")
async def get_light():
    return jsonable_encoder(light.get_light())

@app.post("/light")
async def set_light(value: Annotated[Perc, Form()]):
    bus.emit("light_set", value)
    return None

# Utility (Audio / Camera testing)
@app.post("/tone")
async def tone(duration: Annotated[float, Form()]):
    return audio.tone(duration)

@app.post("/record")
async def record(duration: Annotated[float, Form()]):
    return Response(content=audio.record(duration), media_type="audio/wav")

@app.get("/snapshot")
async def snapshot():
    return Response(content=camera.snapshot(), media_type="image/jpeg")