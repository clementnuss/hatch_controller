
from global_variables import stop_event
from hatch_controller import hc
from ecran.mqtt import mqtt_client, coverQueue
import logging
import time

TRAPPE_TOPIC = "homeassistant/cover/trappe-ecran/trappe"
MQTT_OPEN = b"OPEN"
MQTT_CLOSE = b"CLOSE"
MQTT_STOP = b"STOP"


class State():
    def __init__(self):
        self.enter_time = time.time()
        logging.info(f'COVER: Current state: {str(self)}')
        self.on_enter()

    def on_enter(self) -> None:
        pass

    def update(self, mqtt_command=""):
        return self

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class Open(State):
    def on_enter(self):
        mqtt_client.publish(f"{TRAPPE_TOPIC}/state", "open")

    def update(self, mqtt_command=""):

        if mqtt_command == MQTT_CLOSE:
            return Closing()

        return self


class Closed(State):

    def on_enter(self):
        mqtt_client.publish(f"{TRAPPE_TOPIC}/state", "closed")

    def update(self, mqtt_command=""):

        if mqtt_command == MQTT_OPEN:
            return Opening()

        return self


class Stopped(State):
    def on_enter(self):
        hc.stop()
        mqtt_client.publish(f"{TRAPPE_TOPIC}/state", "stopped")

    def update(self, mqtt_command=""):

        if mqtt_command == MQTT_CLOSE:
            return Closing()
        elif mqtt_command == MQTT_OPEN:
            return Opening()

        return self


class Opening(State):
    def on_enter(self):
        mqtt_client.publish(f"{TRAPPE_TOPIC}/state", "opening")
        hc.set_target_position(hc.opened_position)

    def update(self, mqtt_command=""):
        if mqtt_command == MQTT_CLOSE:
            return Closing()
        elif mqtt_command == MQTT_STOP:
            return Stopped()

        return self


class Closing(State):

    def on_enter(self) -> None:
        mqtt_client.publish(f"{TRAPPE_TOPIC}/state", "closing")
        hc.enable_control()
        hc.set_target_position(hc.closed_position)
        return

    def update(self, mqtt_command=""):
        if mqtt_command == MQTT_OPEN:
            return Opening()
        elif mqtt_command == MQTT_STOP:
            # stop hc
            mqtt_client.publish(f"{TRAPPE_TOPIC}/state", "stopped")
            return Stopped()

        return self


class CoverStateMachine():
    def __init__(self) -> None:
        self.state = Closed()
        self.queue = coverQueue

    def control_loop(self):
        while not stop_event.is_set():

            if hc.target_position_reached():
                if hc.get_position() <= hc.closed_position + 1:
                    self.state = Closed()
                elif hc.get_position() >= hc.opened_position - 10:
                    self.state = Open()

            mqtt_command = ""
            if self.queue.not_empty:
                mqtt_command = self.queue.get()
                # logging.info(f"command: {mqtt_command}")

            self.state = self.state.update(mqtt_command)
            time.sleep(50 * 1e-3)  # 50 ms loop


coverFSM = CoverStateMachine()
