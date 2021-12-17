from motor import Motor
from ecran.pin_mapping import *

mot_g = Motor(MOT_G_DIR, MOT_G_STEP, MOT_G_ENn, direct=1)
mot_d = Motor(MOT_D_DIR, MOT_D_STEP, MOT_D_ENn, direct=0)
motors = [mot_g, mot_d]

constants = {}
constants["max_speed"] = 7.0
constants["closed_position"] = -0.3 
constants["opened_position"] = 362 

