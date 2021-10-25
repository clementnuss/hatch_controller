import pigpio
from dataclasses import dataclass

def mm_to_steps(mm_s: float):
    # steps_per_turn = 400 # 1/2 stepping -> 2 * 200 
    # mm_per_turn = 2
    # steps_per_mm = 400/2 = 200
    return int(200 * mm_s)

@dataclass
class Motor:
    direction_pin: int
    step: int
    en_not: int
    pi: pigpio.pi
    direct: int
            
    def is_enabled(self):
        return not self.pi.read(self.en_not)
        
    def enable(self):
        self.pi.write(self.en_not, 0)
        
    def disable(self):
        self.pi.write(self.en_not, 1)
        
    def set_direction(self, direction):
        """Set the forward/open (1) or backward/close (0) direction.
        """
        if self.direct:
            direction += 1
            direction %= 2
            
        self.pi.write(self.direction_pin, direction)
        
    def set_speed(self, mm_s):  
        self.speed = mm_s
      
        if mm_s == 0:
            self.pi.hardware_PWM(self.step, 0, 0)
            return
            
        if mm_s < 0:
            self.set_direction(1)
        else:
            self.set_direction(0)
            
        self.pi.hardware_PWM(self.step, mm_to_steps(abs(mm_s)), 500000)
    