from argparse import ArgumentParser, ArgumentTypeError
import paho.mqtt.client as mqtt
import yaml
import json
import logging
import time
from service import NibeDownlink

# create logger
logger = logging.getLogger(__name__)

##
## cmd line argument parser
##

parser = ArgumentParser(
    description="Read heat pump metrics from Nibe Uplink to MQTT")
parser.add_argument(
    '-q',
    '--mqtt-broker-host',
    action='store',
    dest='mqtt_addr',
    help='mqtt broker host address',
    type=str,
    default="127.0.0.1")
parser.add_argument(
    '-p',
    '--mqtt-broker-port',
    action='store',
    dest='mqtt_port',
    help='mqtt broker port',
    type=int,
    default=1883)
parser.add_argument(
    '-k',
    '--mqtt-keepalive',
    action='store',
    dest='mqtt_keepalive',
    help='mqtt keepalive',
    type=int,
    default=60)
parser.add_argument(
    '-c',
    '--nibe-config',
    action='store',
    dest='conf_fname',
    help='nibe credentials and variables config yaml file',
    type=str,
    default='conf/nibe-uplink.yml')
parser.add_argument(
    '-t',
    '--mqtt-topic-prefix',
    action='store',
    dest='topic',
    help='mqtt topic prefix',
    type=str,
    default='nibe-uplink')

LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


def log_level_string_to_int(log_level_string):
    if not log_level_string in LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, LOG_LEVEL_STRINGS)
        raise ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the logging log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


parser.add_argument(
    '-l',
    '--log-level',
    action='store',
    dest='log_level',
    help='set the logging output level. {0}'.format(LOG_LEVEL_STRINGS),
    type=log_level_string_to_int,
    default='INFO')

pars = parser.parse_args()

##
## set logger
##

logging.basicConfig(
    format='%(levelname)s %(module)s: %(message)s', level=pars.log_level)

##
## Nibe uplink
##

#read config file and parse yaml to dict
with open(pars.conf_fname, 'r') as stream:
    try:
        c = yaml.load(stream)
    except yaml.YAMLError as exc:
        logger.error(exc)

nd = NibeDownlink(**c)
topic = '{}/{}/R'.format(pars.topic, c['hpid'])

##
## MQTT
##


def on_connect(client, userdata, flags, rc):
    '''
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
    client.connected_flag = False
    logger.error("MQTT disconnect: code={}".format(rc))


def on_publish(client, userdata, mid):
    logger.info("MQTT published: topic={} mid={}".format(topic, mid))


mqtt.Client.connected_flag = False
mqtt_client = mqtt.Client(
    __file__ + '_{0:010x}'.format(int(time.time() * 256))[:10])
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
