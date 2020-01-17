import json
import logging
import re

import requests

# create logger
logging.getLogger(__name__).addHandler(logging.NullHandler())


class NibeDownlink(object):
    def __init__(self, username, password, hpid, variables):
        self.auth_data = {
            "email": username,
            "password": password,
        }
        self.hpid = hpid
        self.variables = variables
        self.authenticated = False
        self.session = requests.Session()

    def login(self):
        auth_result = self.session.post('https://www.nibeuplink.com/LogIn',
                                        self.auth_data)
        if auth_result.status_code == 200:
            self.authenticated = True
            logging.info("Succesfully authenticated")
            return True
        else:
            logging.error(
                "Failed to authenticate with status code: %d, content: %s",
                auth_result.status_code, auth_result.content)
            return False

    def normalize_value(self, value):
        try:
            return float(
                re.sub(
                    u'^([-\d.]+)(A|Hz|h|%|\u00B0C|DM|SM|bar|cent/kWh|kWh|l/m)?$',
                    r'\1',
                    value,
                    flags=re.UNICODE))
        except ValueError:
            pass

        return value

    def getValues(self):
        if not self.authenticated:
            if not self.login():
                raise Exception(
                    "Unable to get Nibe uplink values. Authentication failed")

        variable_query_result = self.session.post(
            'https://www.nibeuplink.com/PrivateAPI/Values', {
                "hpid": self.hpid,
                "variables": self.variables
            })

        decoded = {}

        try:
            data = json.loads(variable_query_result.content.decode('utf8'))
        except ValueError as e:
            logging.exception(
                "Failed to decode JSON object: %s. Request status code: %d",
                variable_query_result.content,
                variable_query_result.status_code)
            # try to reauth
            self.authenticated = False
            return None, None

        if 'IsOffline' in data and 'Values' in data:
            online = not data['IsOffline']

            values = data['Values']

            for value in values:
                if 'VariableId' in value and 'CurrentValue' in value:
                    v = value['CurrentValue']
                    v = self.normalize_value(v)
                    decoded[value['VariableId']] = v

            logging.info("Fetched: %s", str(decoded))
            return online, decoded

        return None, None
