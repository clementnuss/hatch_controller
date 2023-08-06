from motor import Motor
from beamer.pin_mapping import *

mot = Motor(MOT_DIR, MOT_STEP, MOT_ENn, direct=0, steps_per_mm=STEPS_PER_MM)
motors = [mot]

max_speed = 4.0
closed_position = -0.3
opened_position = 155


