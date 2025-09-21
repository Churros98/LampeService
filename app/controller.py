import asyncio
from app.world import inverse
from app.models import Angle, Constraint, EncodedAngle, Normalized, Position
from app.motor import Motor
from typing import List
from STservo_sdk import sts, PortHandler
from app.eventbus import bus

class ControllerExeption(BaseException):
    pass

class Controller():
    ''' Motors controller (UART) device '''
    handler: sts
    motors: dict[str, Motor]

    def __init__(self, motor_device = "/dev/ttyS0", baudrate = 10000000, bus=None):
        self.motors = {}
        self.bus = bus

        port = PortHandler(motor_device)
        port.setBaudRate(baudrate)
        if not port.openPort():
            raise ControllerExeption()

        self.handler = sts(port)

        if self.bus:
            self.bus.subscribe("controller_move_angles")(self.on_move_angles)
            self.bus.subscribe("controller_move_encodeds")(self.on_move_encodeds)
            self.bus.subscribe("controller_move_position")(self.on_move_position)
            self.bus.subscribe("controller_move_tracking")(self.on_move_tracking)
            self.bus.subscribe("controller_torque")(self.on_set_torque)

    def add_motor(self, name: str, sts_id: int, offset: Angle, constraint: Constraint, is_reverse = False) -> Motor:
        ''' Add a motor on the controls system'''
        self.motors[name] = Motor(self.handler, sts_id, name, constraint, offset, is_reverse)
        return self.motors[name]

    def remove_motor(self, name: str):
        ''' Remove a motor on the controls system'''
        motor = self.motors.get(name)
        if motor == None:
            raise ControllerExeption(f'Motor {name} doesnt exist.')

        del motor

    def motor(self, name: str) -> Motor:
        ''' Get a motor from the controls system'''
        motor = self.motors.get(name)
        if motor == None:
            raise ControllerExeption(f'Motor {name} doesnt exist.')
        return motor
    
    async def read(self):
        ''' Stream motors world angles '''
        while self.handler.portHandler.is_open:
            angles: dict[str, Angle] = {}
            for name, motor in self.motors.items():
                angles[name] = motor.get_world_angle()

            yield angles

    async def update(self):
        ''' Update '''
        if self.bus is None:
            return

        async for angles in self.read():
            self.bus.emit("controller_angles", angles)
            await asyncio.sleep(0.5)

    def unlock_all_motors(self) -> None:
        ''' Unlock all motors '''
        for name, motor in self.motors.items():
            motor.set_torque(False)

    def lock_all_motors(self) -> None:
        ''' Unlock all motors '''
        for name, motor in self.motors.items():
            motor.set_torque(True)

    def check_all_motors(self) -> dict[str, Motor]:
        ''' Checkup all motors. '''
        checkup = {}
        for name, motor in self.motors.items():
            if not motor.check_motor():
                print(f"Motor {name} : NO GO")
                checkup[name] = False
            else:
                checkup[name] = True

        return checkup
    
    def close(self):
        ''' Close the motor system '''
        self.unlock_all_motors()
        self.handler.portHandler.closePort()

    async def on_move_angles(self, angles: dict[str, Angle]) -> None:
        ''' Move a group of motor using angles '''
        for name, angle in angles.items():
            try:
                self.motor(name).set_world_angle(angle)
                print(f"Moving {name} to angle {angle.deg}°.")
            except:
                pass

    async def on_move_encodeds(self, encodeds: dict[str, EncodedAngle]) -> None:
        ''' Move a group of motors using encoded angles (Constraint not checked)'''
        for name, encoded in encodeds.items():
            try:
                self.motor(name).set_encoded_angle(encoded)
                print(f"Moving {name} to encoded angle {encoded.enc}.")
            except:
                pass

    async def on_move_position(self, position: Position) -> None:
        ''' Move to a position using motors '''
        print(f"Moving to position {position}")
        angles = inverse(position)
        await self.on_move_angles(angles)

    async def on_move_tracking(self, moving_norm: Normalized) -> None:
        ''' Move motors for tracking '''
        # It will be complex
        print(f"Tracking: {moving_norm}")
        return

    async def on_set_torque(self, enable: bool) -> None:
        ''' Set the torque for all motors '''
        for _, motor in self.motors.items():
            motor.set_torque(enable)