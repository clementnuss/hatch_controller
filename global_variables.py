
import threading, logging
import pigpio

logging.basicConfig(level=logging.INFO)

stop_event = threading.Event()

# Connecting to the PiGPIO Daemon
pi = pigpio.pi(host='rpi-ecran', port=28888)
if not pi.connected:
    logging.fatal("Unable to connect to the pigpiod daemon. exiting")
    exit(-1)
logging.info("Correctly connected to the pigpio daemon.")