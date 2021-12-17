import pigpio
import time
import logging
from threading import Lock

from ecran.pin_mapping import *
import global_variables


class HatchController:
    closed_switch_supply = SWITCH_CLOSED_Supply
    closed_switch_input = SWITCH_CLOSED_Input
    opened_switch_supply = SWITCH_OPENED_Supply
    opened_switch_input = SWITCH_OPENED_Input
    pi: pigpio.pi

    lock = Lock()

    def __init__(self, motors, constants):

        self.pi = global_variables.pi
        self.motors = motors # array containing the motors to control

        # constants
        self.max_speed = constants['max_speed']
        self.closed_position = constants['closed_position']
        self.opened_position = constants['opened_position']
        self.timeout = 1.0  # 5 seconds before disabling drivers

        # configure stepping on the motor: MS12 = 10 := 1/2 steps
        self.pi.write(MS1, 1)
        self.pi.write(MS2, 0)

        self.position = self.opened_position - 20
        self.target_position = self.position

        self.last_mvmt_time = time.time()
        self.last_closed_callback_time = time.time()
        self.last_opened_callback_time = time.time()
        self.last_update_time = time.time()
        self.controller_speed = 0.0
        self.is_closed = False
        self.is_opened = False

        self.control_enabled = False

    def enable_control(self, disable=False):
        self.control_enabled = not disable
        return self.control_enabled

    def enable_motors(self):
        for mot in self.motors:
            mot.enable()

    def disable_motors(self):
        for mot in self.motors:
            mot.disable()

    def stop(self):
        self.stop_motors()
        with self.lock:
            self.target_position = self.position

    def stop_motors(self):
        if self.controller_speed != 0:
            self.set_speed(0)
            # logging.info(f"motor speed: {self.controller_speed}")
            self.update_speed()
            self.last_mvmt_time = time.time()

    def update_speed(self):
        for mot in self.motors:
            mot.set_speed(self.controller_speed)

    def set_speed(self, speed):
        self.controller_speed = speed

    def get_position(self):
        with self.lock:
            return self.position

    def target_position_reached(self):
        with self.lock:
            return abs(self.position - self.target_position) < 0.5

    def set_target_position(self, new_target):
        with self.lock:
            self.target_position = new_target

    def configure_closed_switch(self):
        self.pi.set_mode(self.closed_switch_supply, pigpio.OUTPUT)
        self.pi.write(self.closed_switch_supply, 1)
        self.pi.set_mode(self.closed_switch_input, pigpio.INPUT)
        self.pi.set_pull_up_down(self.closed_switch_input, pigpio.PUD_DOWN)
        time.sleep(10e-3)
        self.cb = self.pi.callback(
            self.closed_switch_input, pigpio.FALLING_EDGE, self.closed_callback)
        self.enable_closed_callback()

    def configure_opened_switch(self):
        self.pi.set_mode(self.opened_switch_supply, pigpio.OUTPUT)
        self.pi.write(self.opened_switch_supply, 1)
        self.pi.set_mode(self.opened_switch_input, pigpio.INPUT)
        self.pi.set_pull_up_down(self.opened_switch_input, pigpio.PUD_DOWN)
        time.sleep(10e-3)
        self.cb = self.pi.callback(
            self.opened_switch_input, pigpio.FALLING_EDGE, self.opened_callback)
        self.enable_opened_callback()
        logging.info(f"current status: opened input: {self.pi.read(self.opened_switch_input)}")

    def closed_callback(self, gpio, level, tick):
        if self.is_closed:
            return

        self.last_closed_callback_time = time.time()
        self.stop_motors()
        with self.lock:
            self.position = self.target_position = self.closed_position

        self.is_closed = True
        logging.info('now closed')

    def opened_callback(self, gpio, level, tick):
        if self.is_opened:
            return

        self.last_opened_callback_time = time.time()
        self.stop_motors()
        with self.lock:
            self.position = self.target_position = self.opened_position + 40

        self.is_opened = True
        logging.info('now opened')

    def enable_closed_callback(self):
        if self.pi.read(self.closed_switch_input) == 0:  # already closed
            self.is_closed = True
        else:
            if time.time() - self.last_closed_callback_time > 1.0:  # after 1 second with endstop not reached, we reenable it
                self.is_closed = False

    def enable_opened_callback(self):
        if self.pi.read(self.opened_switch_input) == 0:  # already opened
            self.is_opened = True
        else:
            if time.time() - self.last_opened_callback_time > 1.0:  # after 1 second with endstop not reached, we reenable it
                self.is_opened = False


    def time_since_last_change(self):
        return time.time() - self.last_update_time

    def update_position(self):
        with self.lock:
            self.position += self.time_since_last_change() * self.controller_speed

        self.last_update_time = time.time()
        return self.position

    def control_loop(self):
        logging.info('control loop started')
        self.configure_closed_switch()
        self.configure_opened_switch()

        while not global_variables.stop_event.is_set():
            self.update_position()
            if not self.control_enabled:
                continue

            if self.controller_speed == 0.0:
                if time.time() - self.last_mvmt_time > self.timeout:
                    self.disable_motors()

            if self.is_closed:
                self.enable_closed_callback()

            if self.is_opened:
                self.enable_opened_callback()

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

import os, sys
if os.getenv("CONTROLLER_TYPE") == "ECRAN":
    from ecran import vars

    hc = HatchController(vars.motors, vars.constants)
elif os.getenv("CONTROLLER_TYPE") == "BEAMER":
    pass

else:
    logging.error("FATAL#: CONTROLLER_TYPE env variable must be either ECRAN or BEAMER")
    sys.exit(14)

