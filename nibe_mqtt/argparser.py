# -*- coding: utf-8 -*-
'''cmd line argument parser for nibe_mqtt'''

import logging
from argparse import ArgumentParser, ArgumentTypeError
from nibe_mqtt.version import __version__, get_build_info

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


def log_level_string_to_int(arg_string):
    '''get log level int from string'''

    log_level_string = arg_string.upper()
    if log_level_string not in _LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, _LOG_LEVEL_STRINGS)
        raise ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


def get_pars():
    '''get parameters from from command line arguments'''

    parser = ArgumentParser(
        description="Scrape heat pump metrics from Nibe Uplink to MQTT")
    parser.add_argument('-q',
                        '--mqtt-broker-host',
                        action='store',
                        dest='mqtt_addr',
                        help='mqtt broker host address',
                        type=str,
                        default="127.0.0.1")
    parser.add_argument('-p',
                        '--mqtt-broker-port',
                        action='store',
                        dest='mqtt_port',
                        help='mqtt broker port',
                        type=int,
                        default=1883)
    parser.add_argument('-k',
                        '--mqtt-keepalive',
                        action='store',
                        dest='mqtt_keepalive',
                        help='mqtt keepalive',
                        type=int,
                        default=60)
    parser.add_argument('-c',
                        '--nibe-config',
                        action='store',
                        dest='conf_fname',
                        help='nibe credentials and variables config yaml file',
                        type=str,
                        default='conf/nibe-uplink.yml')
    parser.add_argument('-t',
                        '--mqtt-topic-prefix',
                        action='store',
                        dest='topic',
                        help='mqtt topic prefix',
                        type=str,
                        default='nibe-uplink')

    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version=str(get_build_info()))

    parser.add_argument(
        '-l',
        '--log-level',
        action='store',
        dest='log_level',
        help='set the logging output level. {0}'.format(_LOG_LEVEL_STRINGS),
        type=log_level_string_to_int,
        default='INFO')

    return parser.parse_args()
