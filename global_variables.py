
import threading, logging
import pigpio

logging.basicConfig(level=logging.INFO)

stop_event = threading.Event()

import os, dotenv
dotenv.load_dotenv()


EMQX_HOST = os.getenv("EMQX_HOST")
EMQX_PORT = os.getenv("EMQX_PORT")
EMQX_USER = os.getenv("EMQX_USER")
EMQX_PASS = os.getenv("EMQX_PASS")


# Connecting to e PiGPIO Daemon
pi = pigpio.pi(host=os.getenv("PIGPIOD_HOST", default="localhost"), port=8888)
if not pi.connected:
    logging.fatal("Unable to connect to the pigpiod daemon. exiting")
    exit(-1)
logging.info("Correctly connected to the pigpio daemon.")
