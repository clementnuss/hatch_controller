import pigpio
from dataclasses import dataclass
from global_variables import pi


@dataclass
class Motor:
    direction_pin: int
    step: int
    en_not: int
    direct: int
    steps_per_mm: int
            
    def is_enabled(self):
        return not pi.read(self.en_not)
        
    def enable(self):
        pi.write(self.en_not, 0)
        
    def disable(self):
        pi.write(self.en_not, 1)

    def mm_to_steps(self, mm_s: float):
        return int(self.steps_per_mm * mm_s)
        
    def set_direction(self, direction):
        """Set the forward/open (1) or backward/close (0) direction.
        """
        if self.direct:
            direction += 1
            direction %= 2
            
        pi.write(self.direction_pin, direction)
        
    def set_speed(self, mm_s):  
        self.speed = mm_s
      
        if mm_s == 0:
            pi.hardware_PWM(self.step, 0, 0)
            return
            
        if mm_s < 0:
            self.set_direction(1)
        else:
            self.set_direction(0)
            
        pi.hardware_PWM(self.step, self.mm_to_steps(abs(mm_s)), 500000)
    
