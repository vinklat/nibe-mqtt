# -*- coding: utf-8 -*-
'''nibe_mqtt app version and resources info'''

from platform import python_version
import pkg_resources

__version__ = '0.1.0rc0'


def get_build_info():
    '''get app version and resources info'''
    ret = {
        'nibe-mqtt': __version__,
        'python': python_version(),
        'paho-mqtt': pkg_resources.get_distribution("paho-mqtt").version
    }
    return ret
