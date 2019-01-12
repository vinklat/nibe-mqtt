from argparse import ArgumentParser, ArgumentTypeError
import paho.mqtt.client as mqtt
import yaml
import json
import logging
import time
from service import NibeDownlink

##
## cmd line argument parser
##

parser = ArgumentParser(description='nibe-mqtt')
parser.add_argument(
    '-q',
    '--mqtt-broker-host',
    action='store',
    dest='mqtt_addr',
    help='mqtt broker host address',
    type=str,
    default="172.28.16.1")
parser.add_argument(
    '-p',
    '--mqtt-broker-port',
    action='store',
    dest='mqtt_port',
    help='mqtt port port',
    type=int,
    default=1883)
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
## create logger
##

logger = logging.getLogger('switchboard-mqtt')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(pars.log_level)
formatter = logging.Formatter('%(levelname)s %(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

##
## connect MQTT
##

mqtt_client = mqtt.Client()
try:
    mqtt_client.connect(pars.mqtt_addr, pars.mqtt_port, 60)
except:
    logger.error("can't connect to mqtt broker ({}:{})".format(
        pars.mqtt_addr, pars.mqtt_port))
    exit(1)

##
## nibe uplink
##

#read config file and parse yaml to dict
with open(pars.conf_fname, 'r') as stream:
    try:
        c = yaml.load(stream)
    except yaml.YAMLError as exc:
        logger.error(exc)

nd = NibeDownlink(**c)
topic = '{}/{}/R'.format(pars.topic, c['hpid'])

while True:
    online, values = nd.getValues()
    payload = { 'ONLINE': online }

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
    logger.info("publish: {} {}".format(topic, j))
    mqtt_client.publish(topic, j)

    time.sleep(60)
