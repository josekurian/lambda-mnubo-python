#!/usr/bin/env python

from __future__ import print_function
import os
import logging
import re
from smartobjects import SmartObjectsClient
from smartobjects import Environments


class MnuboEvent(object):

    def __init__(self):
        self._event_data = dict()
        self._device_id = None

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, device_id=None):
        if device_id is not None:
            assert isinstance(device_id, str)
        self._device_id = device_id

    @property
    def event_data(self):
        return self._event_data

    @event_data.setter
    def event_data(self, event_data=None):
        if event_data is None:
            self._event_data = dict()
        if event_data is not None:
            assert isinstance(event_data, dict)
        self._event_data = event_data

    def build(self):
        mnubo_event = dict()
        if self.device_id is not None:
            mnubo_event['x_object'] = dict()
            mnubo_event['x_object']['x_device_id'] = self.device_id

        p = re.compile(r'x_\w+')
        for k in self._event_data.keys():
            if not p.match(k):
                mnubo_event[k] = self.event_data.get(k)
        return mnubo_event


def select_mnubo_env(env_name):
    # Do some sanity checks on the environments and return the right value for the mnubo client
    if env_name == 'production':
        logger.info('Loading with environment: {0}'.format(env_name))
        return Environments.Production
    elif env_name == 'sandbox':
        logger.info('Loading with environment: {0}'.format(env_name))
        return Environments.Sandbox
    else:
        logger.error('Wrong environment value: {0}'.format(env_name))
        raise EnvironmentError('Do not know about env {0}'.format(env_name))


def map_to_mnubo_event(event):
    global device_id_field_name
    # Sanity check
    assert isinstance(event, dict)

    # Create a new mnubo-formatted event
    mnubo_data = MnuboEvent()

    # If we have a device id,
    if device_id_field_name in event:
        # Set it up in the mnubo way
        mnubo_data.device_id = event.get(device_id_field_name, None)
        # Remove it from the event data
        event.pop(device_id_field_name)

    ############################################################
    # Insert any other custom transformation on event dict here
    ############################################################

    # Assign the free-form data to mnubo
    mnubo_data.event_data = event
    # Returned mapped dictionary to send to mnubo
    return mnubo_data.build()

logger = logging.getLogger()
# Mnubo environment
mnubo_environment = select_mnubo_env(env_name=os.environ.get('MNUBO_ENV', 'sandbox'))
# Mnubo client ID
mnubo_client_id = os.environ.get('MNUBO_CLIENT_ID', None)
# Mnubo client secret
mnubo_client_secret = os.environ.get('MNUBO_CLIENT_SECRET', None)
# Name of the device id field.
device_id_field_name =  os.environ.get('DEVICE_ID_FIELD', 'device_id')
# Mnubo SmartOjbects Client
client = None

logger.info('Loading function')


# AWS Lambda handler function
def lambda_handler(event, context):
    global client
    global mnubo_environment
    global mnubo_client_id
    global mnubo_client_secret

    if client is None:
        client = SmartObjectsClient(client_id=mnubo_client_id,
                                    client_secret=mnubo_client_secret,
                                    environment=mnubo_environment)

    results = client.events.send(events=[map_to_mnubo_event(event=event)])
    logger.info('Remaining time in ms: {0}'.format(context.get_remaining_time_in_millis()))

    return results
