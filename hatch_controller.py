import pigpio
import time
import logging
from threading import Lock

from motor import Motor
from pin_mapping import *
import global_variables


class HatchController:
    sw_supply = SWITCH_G_Supply
    sw_input = SWITCH_G_Input
    mot_g: Motor
    mot_d: Motor
    pi: pigpio.pi

    lock = Lock()

    def __init__(self):

        self.pi = global_variables.pi

        # configure stepping on the motor: MS12 = 10 := 1/2 steps
        self.pi.write(MS1, 1)
        self.pi.write(MS2, 0)
        self.mot_g = Motor(MOT_G_DIR, MOT_G_STEP, MOT_G_ENn, self.pi, direct=1)
        self.mot_d = Motor(MOT_D_DIR, MOT_D_STEP, MOT_D_ENn, self.pi, direct=0)

    # constants
    max_speed = 7.0
    closed_position = -1
    opened_position = 362
    timeout = 5.0  # 5 seconds before disabling drivers

    position = opened_position
    target_position = position

    last_mvmt_time = time.time()
    last_callback_time = time.time()
    last_update_time = time.time()
    controller_speed = 0.0
    is_closed = False

    control_enabled = False

    def enable_control(self, disable=False):
        self.control_enabled = not disable
        return self.control_enabled

    def enable_motors(self):
        for mot in [self.mot_g, self.mot_d]:
            mot.enable()

    def disable_motors(self):
        for mot in [self.mot_g, self.mot_d]:
            mot.disable()

    def stop(self):
        self.stop_motors()
        with self.lock:
            self.target_position = self.position

    def stop_motors(self):
        if self.controller_speed != 0:
            self.set_speed(0)
            self.update_speed()
            self.last_mvmt_time = time.time()

    def update_speed(self):
        for mot in [self.mot_g, self.mot_d]:
            mot.set_speed(self.controller_speed)

    def set_speed(self, speed):
        self.controller_speed = speed

    def set_target_position(self, new_target):
        with self.lock:
            self.target_position = new_target

    def configure_switch(self):
        self.pi.write(self.sw_supply, 1)
        self.pi.set_mode(self.sw_input, pigpio.INPUT)
        self.pi.set_pull_up_down(self.sw_input, pigpio.PUD_DOWN)
        time.sleep(10e-3)
        self.cb = self.pi.callback(
            self.sw_input, pigpio.FALLING_EDGE, self.callback)
        self.enable_callback()

    def callback(self, gpio, level, tick):
        if self.is_closed:
            return

        self.last_callback_time = time.time()
        self.stop_motors()
        with self.lock:
            self.position = self.target_position = 0

        self.is_closed = True
        logging.info('now closed')

    def enable_callback(self):
        if self.pi.read(self.sw_input) == 0:  # already closed
            self.is_closed = True
        else:
            if time.time() - self.last_callback_time > 1.0:  # after 1 second with endstop not reached, we reenable it
                self.is_closed = False

    def time_since_last_change(self):
        return time.time() - self.last_update_time

    def update_position(self):
        with self.lock:
            self.position += self.time_since_last_change() * self.controller_speed

        self.last_update_time = time.time()
        return self.position

    def control_loop(self):
        logging.info('control loop started')
        self.configure_switch()
        while not global_variables.stop_event.is_set():
            self.update_position()
            if not self.control_enabled:
                continue

            if self.controller_speed == 0.0:
                if time.time() - self.last_mvmt_time > self.timeout:
                    self.disable_motors()

            if self.is_closed:
                self.enable_callback()

            with self.lock:
                d = self.target_position - self.position
            
            if abs(d) <= 0.5:  # close to target: stop
                self.stop_motors()
            else:
                with self.lock:
                    if self.position > 1.0:
                        self.enable_motors()

                new_speed = min(self.max_speed, 1 +
                                self.max_speed * (abs(d) + 0.5) / 40)
                new_speed *= abs(d)/d
                new_speed = self.controller_speed + 0.05 * \
                    (new_speed - self.controller_speed)

                self.set_speed(new_speed)
                self.update_speed()

            time.sleep(10e-3)  # ~10ms control loop

        logging.info('control loop stopped')
        self.stop_motors()


hc = HatchController()
