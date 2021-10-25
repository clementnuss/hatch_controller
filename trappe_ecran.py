#!/usr/bin/env python3
# coding: utf-8

import hatch_controller
import global_variables
import threading
import logging
import signal


def exit_gracefully(signum, frame):
    logging.warning("Exiting")
    global_variables.stop_event.set()


def main():

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    from mqtt import mqtt_loop
    mqtt_thread = threading.Thread(
        target=mqtt_loop, name="MQTT-Thread")
    mqtt_thread.start()

    from cover_state_machine import coverFSM
    logging.info("Starting cover state machine (Trappe écran)")
    cover_thread = threading.Thread(
        target=coverFSM.control_loop, name="coverFSM-thread", daemon=True)
    cover_thread.start()

    logging.info("Starting 'trappe écran' main Python")
    hc_thread = threading.Thread(
        target=hatch_controller.hc.control_loop, name="HC-ControlLoop", daemon=True)
    hc_thread.start()
    hc_thread.join()


if __name__ == "__main__":
    main()
