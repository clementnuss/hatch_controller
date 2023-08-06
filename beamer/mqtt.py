
import paho.mqtt.client as mqtt
from .pin_mapping import *

import json
import logging

from global_variables import stop_event, pi

import queue

fsmQueue = queue.Queue(10)

HDMI_TOPIC = "hass-plan63-1/switch/trappe-beamer/hdmi"
BEAMER_TOPIC = "hass-plan63-1/switch/trappe-beamer/beamer"
TRAPPE_TOPIC = "hass-plan63-1/cover/trappe-beamer/trappe"

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(f"{BEAMER_TOPIC}/set")
    client.subscribe(f"{TRAPPE_TOPIC}/set")
    client.subscribe(f"{HDMI_TOPIC}/set")


def on_message(cb_client, userdata, msg):
    logging.info(f"received {msg.topic}")
    logging.info(f"received {msg.payload}")

    if msg.topic == f"{BEAMER_TOPIC}/set":
        if msg.payload == b"ON":
            pi.write(RELAIS_BEAMER, 0)
            pi.write(RELAIS_HDMI, 0)
            # logging.info("turning on")
            mqtt_client.publish(f"{BEAMER_TOPIC}/state", "ON", retain=True)
        elif msg.payload == b"OFF":
            pi.write(RELAIS_BEAMER, 1)
            pi.write(RELAIS_HDMI, 1)
            mqtt_client.publish(f"{BEAMER_TOPIC}/state", "OFF", retain=True)
    elif msg.topic == f"{TRAPPE_TOPIC}/set" or f"{HDMI_TOPIC}/set":
        fsmQueue.put(msg)
    else:
        logging.info(f"received msg for unknown topic {msg.payload}")

def pi_status_to_homeassistant_status(pi_status):
    if pi_status == 0: # inverted logic with Sertronics Blue relays
        return "ON"
    else:
        return "OFF"

def mqtt_loop():
    init_mqtt_client()

    mqtt_client.loop_start()
    stop_event.wait(1)

    while not stop_event.is_set():
        beamer_config = {}
        beamer_config['name'] = "Beamer (230V)"
        beamer_config['command_topic'] = f"{BEAMER_TOPIC}/set"
        beamer_config['state_topic'] = f"{BEAMER_TOPIC}/state"
        beamer_config['icon'] = "mdi:projector"
        mqtt_client.publish(f"{BEAMER_TOPIC}/config", json.dumps(beamer_config))

        mqtt_client.publish(f"{BEAMER_TOPIC}/state",
            pi_status_to_homeassistant_status(pi.read(RELAIS_BEAMER)),
            retain=True)

        hdmi_config = {}
        hdmi_config['name'] = "Relais HDMI"
        hdmi_config['command_topic'] = f"{HDMI_TOPIC}/set"
        hdmi_config['state_topic'] = f"{HDMI_TOPIC}/state"
        hdmi_config['icon'] = "mdi:video-input-hdmi"
        mqtt_client.publish(f"{HDMI_TOPIC}/config", json.dumps(hdmi_config))

        trappe_config = {}
        trappe_config['name'] = "Trappe beamer"
        trappe_config['command_topic'] = f"{TRAPPE_TOPIC}/set"
        trappe_config['state_topic'] = f"{TRAPPE_TOPIC}/state"
        trappe_config['icon'] = "mdi:wall-sconce-flat"
        mqtt_client.publish(f"{TRAPPE_TOPIC}/config",
            json.dumps(trappe_config))

        stop_event.wait(60)

    mqtt_client.loop_stop(force=True)


def init_mqtt_client():
    logging.info("Connecting to the MQTT broker")

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    from global_variables import EMQX_HOST, EMQX_PORT, EMQX_USER, EMQX_PASS

    mqtt_client.tls_set()
    # mqtt_client.tls_insecure_set(True)

    mqtt_client.username_pw_set(username=EMQX_USER, password=EMQX_PASS)
    mqtt_client.connect_async(host=EMQX_HOST, port=int(EMQX_PORT), keepalive=60)

