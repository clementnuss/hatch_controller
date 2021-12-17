
import paho.mqtt.client as mqtt
from ecran.pin_mapping import *

import json
import logging

from global_variables import stop_event, pi

import queue

coverQueue = queue.Queue(10)


ECRAN_TOPIC = "homeassistant/switch/trappe-ecran/ecran"
TRAPPE_TOPIC = "homeassistant/cover/trappe-ecran/trappe"

mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(f"{ECRAN_TOPIC}/set")
    client.subscribe(f"{TRAPPE_TOPIC}/set")


def on_message(cb_client, userdata, msg):

    if msg.topic == f"{ECRAN_TOPIC}/set":
        if msg.payload == b"ON":
            pi.write(RELAIS_12V, 1)
            pi.write(RELAIS_230V, 1)
            mqtt_client.publish(f"{ECRAN_TOPIC}/state", "ON", retain=True)
        elif msg.payload == b"OFF":
            pi.write(RELAIS_12V, 0)
            mqtt_client.publish(f"{ECRAN_TOPIC}/state", "OFF", retain=True)
    elif msg.topic == f"{TRAPPE_TOPIC}/set":
        coverQueue.put(msg.payload)


def mqtt_loop():
    init_mqtt_client()

    mqtt_client.loop_start()
    stop_event.wait(1)

    while not stop_event.is_set():
        ecran_config = {}
        ecran_config['name'] = "Écran"
        ecran_config['command_topic'] = f"{ECRAN_TOPIC}/set"
        ecran_config['state_topic'] = f"{ECRAN_TOPIC}/state"
        ecran_config['icon'] = "mdi:projector-screen"
        mqtt_client.publish(f"{ECRAN_TOPIC}/config", json.dumps(ecran_config))

        trappe_config = {}
        trappe_config['name'] = "Trappe écran"
        trappe_config['command_topic'] = f"{TRAPPE_TOPIC}/set"
        trappe_config['state_topic'] = f"{TRAPPE_TOPIC}/state"
        # trappe_config['icon'] = "mdi:projector-screen"
        mqtt_client.publish(f"{TRAPPE_TOPIC}/config",
                            json.dumps(trappe_config))

        # result = client.publish(ecran_topic, json.dumps(ecran_config))
        # status = result[0]
        # if status == 0:
        #     print(f"Send `{msg}` to topic `{topic}`")
        # else:
        #     print(f"Failed to send message to topic {topic}")

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

