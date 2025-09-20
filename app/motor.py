from STservo_sdk import sts, COMM_SUCCESS, STS_TORQUE_ENABLE
from app.models import Angle, Constraint, EncodedAngle

class MotorExeption():
    pass

class Motor:
    ''' Motor wrapper '''
    id: int
    constraint: Constraint
    offset: Angle
    handler: sts
    is_reverse: bool

    def __init__(self, handler: sts, sts_id: int, name: str, constraint: Constraint, offset: Angle, is_reverse=False):
        self.handler = handler
        self.id = sts_id
        self.name = name
        self.constraint = constraint
        self.offset = offset
        self.is_reverse = is_reverse

    def set_constraint(self, constraint: Constraint) -> None:
        ''' Change the motor constraint '''
        self.constraint = constraint

    def set_offset(self, offset: Angle) -> None:
        ''' Change the motor offset '''
        self.offset = offset

    def check_motor(self) -> bool:
        ''' Check if the motor is available in the bus and in the good mode'''
        _model, result, error = self.handler.ping(self.id)
        if result != COMM_SUCCESS:
            return False
        if error != 0:
            return False

        mode = self.handler.read1ByteTxRx(self.id, 33)
        return mode == 0

    def get_encoded_angle(self) -> EncodedAngle:
        ''' Get the absolute (encoded) angle'''
        pos, result, error = self.handler.ReadPos(self.id)
        if result != COMM_SUCCESS or error != 0:
            return EncodedAngle(enc=0)

        return EncodedAngle(enc=pos)

    def set_encoded_angle(self, angle: EncodedAngle) -> None:
        ''' Set absolute (encoded) angle to the motor (Constraint not checked) '''

        self.handler.RegWritePosEx(self.id, angle.enc, 300, 20)
        self.handler.RegAction()

    def get_world_angle(self) -> Angle:
        ''' Get the absolute world (with offset) angle.'''
        angle = self.get_encoded_angle().toAngle()

        if self.is_reverse:
            angle.deg *= -1

        angle.deg -= self.offset.deg

        return angle

    def set_world_angle(self, angle: Angle) -> None:
        ''' Set the absolute world (with offset) angle'''
        if self.is_reverse:
            angle.deg *= -1

        angle.deg += self.offset.deg

        if angle.deg < self.constraint.max and angle.deg > self.constraint.min:
            self.set_encoded_angle(angle.toEncodedAngle())
        else:
            raise MotorExeption(f"Motor {self.name} cancel world angle command {angle.deg}° : Constraint")

    def set_torque(self, enable: bool) -> None:
        ''' Set the torque (lock/unlock motor)  '''
        self.handler.write1ByteTxRx(self.id, STS_TORQUE_ENABLE, 1 if enable else 0)