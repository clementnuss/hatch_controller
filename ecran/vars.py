from motor import Motor
from ecran.pin_mapping import *

mot_g = Motor(MOT_G_DIR, MOT_G_STEP, MOT_G_ENn, direct=1, steps_per_mm=STEPS_PER_MM)
mot_d = Motor(MOT_D_DIR, MOT_D_STEP, MOT_D_ENn, direct=0, steps_per_mm=STEPS_PER_MM)
motors = [mot_g, mot_d]

max_speed = 7.0
closed_position = -0.3 
opened_position = 362 

