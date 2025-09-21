from rpi_hardware_pwm import HardwarePWM
from app.models import Perc

class Light():
    def __init__(self, bus=None, min=0, max=100):
        ''' Light (PWM) device '''
        self.pwm = HardwarePWM(pwm_channel=0, hz=60, chip=0)
        self.min = min
        self.max = max
        self.bus = bus

        if self.bus:
            self.bus.subscribe("light_set")(self.set_light)

    def set_light(self, light: Perc):
        ''' Set the light '''
        d = self.max-self.min
        self.pwm.change_duty_cycle((d*light.val)+self.min)

    def get_light(self):
        ''' Get the light '''
        d = self.max-self.min
        return Perc(val = round(min(max(((self.pwm._duty_cycle-self.min) / d) * 100.0, 100.0), 0.0)))
    
    def close(self):
        ''' Close the light device '''
        self.pwm.stop()
