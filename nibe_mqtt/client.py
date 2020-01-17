# -*- coding: utf-8 -*-
# pylint: disable=E1101, C0103
'''Scrape heat pump metrics from Nibe Uplink to MQTT'''

import yaml
import json
import logging
import time
import paho.mqtt.client as mqtt
from nibe_mqtt.version import __version__, get_build_info
from nibe_mqtt.argparser import get_pars
from nibe_mqtt.service import NibeDownlink

# create logger
logger = logging.getLogger(__name__)

# get parameters from command line arguments
pars = get_pars()

# set logger
logging.basicConfig(format='%(levelname)s %(module)s: %(message)s',
                    level=pars.log_level)

# read config file and parse yaml to dict
with open(pars.conf_fname, 'r') as stream:
    try:
        c = yaml.load(stream)
    except yaml.YAMLError as exc:
        logger.error(exc)

nd = NibeDownlink(**c)
topic = '{}/{}/R'.format(pars.topic, c['hpid'])


def on_connect(client, userdata, flags, rc):
    '''
    fired upon a successful connection

    rc values:
    0: Connection successful
    1: Connection refused – incorrect protocol version
    2: Connection refused – invalid client identifier
    3: Connection refused – server unavailable
    4: Connection refused – bad username or password
    5: Connection refused – not authorised
    6-255: Currently unused.
    '''
    if rc == 0:
        client.connected_flag = True
        logger.info("MQTT connected OK")
    else:
        logger.error("MQTT connect: code={}".format(rc))


def on_disconnect(client, userdata, rc):
    '''fired upon a disconnection'''

    client.connected_flag = False
    logger.error("MQTT disconnect")
    logger.debug("userdata=%s, rc=%s", userdata, rc)


def on_publish(client, userdata, mid):
    '''fired upon a message published'''

    logger.info("MQTT published: topic={} mid={}".format(topic, mid))


mqtt.Client.connected_flag = False
mqtt_client = mqtt.Client(__file__ +
                          '_{0:010x}'.format(int(time.time() * 256))[:10])
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish = on_publish


def main():
    logger.info("conecting to mqtt broker ({}:{})".format(
        pars.mqtt_addr, pars.mqtt_port))
    try:
        mqtt_client.connect(pars.mqtt_addr, pars.mqtt_port,
                            pars.mqtt_keepalive)
    except:
        pass

    mqtt_client.loop_start()

    while True:
        while not mqtt_client.connected_flag:
            logger.debug("wait")
            time.sleep(10)

        online, values = nd.getValues()
        payload = {'ONLINE': online}

        if (str(online)) == "True":
            for key, value in values.items():

                m = {
                    "True": True,
                    "true": True,
                    "ON": True,
                    "On": True,
                    "on": True,
                    "OK": True,
                    "Yes": True,
                    "yes": True,
                    "ano": True,
                    "False": False,
                    "false": False,
                    "OFF": False,
                    "Off": False,
                    "off": False,
                    "LOW": False,
                    "No": False,
                    "no": False,
                    "ne": False
                }

                if value in m:
                    value = m[value]

                payload[str(key)] = value

        else:
            print("Device is offline")

        j = json.dumps(payload)
        ret = mqtt_client.publish(topic, j)
        if ret[0] != 0:
            logger.error("MQTT publish: ret={}".format(ret))

        time.sleep(59)


if __name__ == "__main__":
    main()
