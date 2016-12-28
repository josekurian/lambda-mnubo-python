#!/usr/bin/env python

from __future__ import print_function
import os
import logging
import re
import time
import copy
from smartobjects import SmartObjectsClient
from smartobjects import Environments


# Constants
CACHE_VALIDITY_PERIOD = 300
# Global variables
global_cache = dict()
# Mnubo config
config = dict()
# Please use production or sandbox for the following in the environment variable.
config['environment'] = None
config['client_id'] = os.environ.get('MNUBO_CLIENT_ID', None)
config['client_secret'] = os.environ.get('MNUBO_CLIENT_SECRET', None)

# Mnubo SmartObjects Client
client = None

# Default field name mappings
field_names = dict()
field_names['device_id'] = os.environ.get('DEVICE_ID_FIELD', 'device_id')
field_names['event_id'] = os.environ.get('EVENT_ID_FIELD', 'event_id')
field_names['event_type'] = os.environ.get('EVENT_TYPE_FIELD', 'event_type')
field_names['owner_username'] = os.environ.get('OWNER_USERNAME_FIELD', 'owner_username')
field_names['object_type'] = os.environ.get('OBJECT_TYPE_FIELD', 'object_type')
field_names['timestamp'] = os.environ.get('TIMESTAMP_FIELD', 'timestamp')
field_names['latitude'] = os.environ.get('LATITUDE_FIELD', 'latitude')
field_names['longitude'] = os.environ.get('LONGITUDE_FIELD', 'longitude')
field_names['last_update'] = os.environ.get('LAST_UPDATE_FIELD', 'last_update')
field_names['registration_date'] = os.environ.get('REGISTRATION_DATE_FIELD', 'registration_date')

# Get the logger.
logger = logging.getLogger()


class MnuboObject(object):
    def __init__(self):
        self._object_data = dict()
        self._device_id = None
        self._object_type = None
        self._owner_username = None
        self._timestamp = None
        self._registration_date = None
        self._registration_latitude = None
        self._registration_longitude = None
        self._last_update_timestamp = None
        self._custom_attributes = dict()

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, value):
        self._device_id = value

    @property
    def object_type(self):
        return self._object_type

    @object_type.setter
    def object_type(self, value):
        self._object_type = value

    @property
    def owner_username(self):
        return self._owner_username

    @owner_username.setter
    def owner_username(self, value):
        self._owner_username = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = value

    @property
    def registration_date(self):
        return self._registration_date

    @registration_date.setter
    def registration_date(self, value):
        self._registration_date = value

    @property
    def registration_latitude(self):
        return self._registration_latitude

    @registration_latitude.setter
    def registration_latitude(self, value):
        self._registration_latitude = value

    @property
    def registration_longitude(self):
        return self._registration_longitude

    @registration_longitude.setter
    def registration_longitude(self, value):
        self._registration_longitude = value

    @property
    def last_update_timestamp(self):
        return self._last_update_timestamp

    @last_update_timestamp.setter
    def last_update_timestamp(self, value):
        self._last_update_timestamp = value

    @property
    def custom_attributes(self):
        return self._custom_attributes

    @custom_attributes.setter
    def custom_attributes(self, value):
        assert isinstance(value, dict)
        self._custom_attributes = value

    def build(self):
        mnubo_object = dict()
        if self.device_id is not None:
            mnubo_object['x_device_id'] = self.device_id
        if self.object_type is not None:
            mnubo_object['x_object_type'] = self.object_type
        if self.owner_username is not None:
            mnubo_object['x_owner'] = dict()
            mnubo_object['x_owner']['username'] = self.owner_username
        if self.timestamp is not None:
            mnubo_object['x_timestamp'] = self.timestamp
        if self.registration_date is not None:
            mnubo_object['x_registration_date'] = self.registration_date
        if self.registration_latitude is not None:
            mnubo_object['x_registration_latitude'] = self.registration_latitude
        if self.registration_longitude is not None:
            mnubo_object['x_registration_longitude'] = self.registration_longitude
        if self.last_update_timestamp is not None:
            mnubo_object['x_last_update_timestamp'] = self.last_update_timestamp

        p = re.compile(r'x_\w+')
        for k in self.custom_attributes.keys():
            if not p.match(k):
                mnubo_object[k] = self.custom_attributes.get(k)

        return mnubo_object


class MnuboEvent(object):

    def __init__(self):
        self._device_id = None
        self._event_data = dict()
        self._event_id = None
        self._event_type = None
        self._latitude = None
        self._longitude = None
        self._timestamp = None

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

    @property
    def event_id(self):
        return self._event_id

    @event_id.setter
    def event_id(self, value):
        self._event_id = value

    @property
    def event_type(self):
        return self._event_type

    @event_type.setter
    def event_type(self, value):
        self._event_type = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = value

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        self._latitude = value

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        self._longitude = value

    def build(self):
        mnubo_event = dict()
        if self.device_id is not None:
            mnubo_object = MnuboObject()
            mnubo_object.device_id = self.device_id
            mnubo_event['x_object'] = mnubo_object.build()

        if self.event_type is not None:
            mnubo_event['x_event_type'] = self.event_type

        if self.event_id is not None:
            mnubo_event['event_id'] = self.event_id

        if self.timestamp is not None:
            mnubo_event['x_timestamp'] = self.timestamp

        if self.latitude is not None:
            mnubo_event['x_latitude'] = self.latitude

        if self.longitude is not None:
            mnubo_event['x_longitude'] = self.longitude

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
    global field_names
    # Sanity check
    assert isinstance(event, dict)

    # Create a new mnubo-formatted event
    mnubo_data = MnuboEvent()

    if field_names['device_id'] in event:
        mnubo_data.device_id = event.get(field_names['device_id'], None)
        event.pop(field_names['device_id'])
    if field_names['event_id'] in event:
        mnubo_data.event_id = event.get(field_names['event_id'], None)
        event.pop(field_names['event_id'])
    if field_names['event_type'] in event:
        mnubo_data.event_type = event.get(field_names['event_type'], None)
        event.pop(field_names['event_type'])
    if field_names['latitude'] in event:
        mnubo_data.latitude = event.get(field_names['latitude'], None)
        event.pop(field_names['latitude'])
    if field_names['longitude'] in event:
        mnubo_data.longitude = event.get(field_names['longitude'], None)
        event.pop(field_names['longitude'])
    if field_names['timestamp'] in event:
        mnubo_data.timestamp = event.get(field_names['timestamp'], None)
        event.pop(field_names['timestamp'])

    ############################################################
    # Insert any other custom transformation on event dict here
    ############################################################

    # Assign the free-form data to mnubo
    mnubo_data.event_data = event
    # Returned the mnubo-compatible object
    return mnubo_data


def map_to_mnubo_object(event):
    global field_names
    # Sanity check
    assert isinstance(event, dict)

    # Create a new mnubo-formatted event
    mnubo_object = MnuboObject()
    assert isinstance(mnubo_object, MnuboObject)

    if field_names['device_id'] in event:
        mnubo_object.device_id = event.get(field_names['device_id'], None)
        event.pop(field_names['device_id'])
    if field_names['object_type'] in event:
        mnubo_object.object_type = event.get(field_names['object_type'], None)
        event.pop(field_names['object_type'])
    if field_names['owner_username'] in event:
        mnubo_object.owner_username = event.get(field_names['owner_username'], None)
        event.pop(field_names['owner_username'])
    if field_names['latitude'] in event:
        mnubo_object.latitude = event.get(field_names['latitude'], None)
        event.pop(field_names['latitude'])
    if field_names['last_update'] in event:
        mnubo_object.last_update_timestamp = event.get(field_names['last_update'], None)
        event.pop(field_names['last_update'])
    if field_names['longitude'] in event:
        mnubo_object.longitude = event.get(field_names['longitude'], None)
        event.pop(field_names['longitude'])
    if field_names['registration_date'] in event:
        mnubo_object.registration_date = event.get(field_names['registration_date'], None)
        event.pop(field_names['longitude'])
    if field_names['timestamp'] in event:
        mnubo_object.timestamp = event.get(field_names['timestamp'], None)
        event.pop(field_names['timestamp'])

    ############################################################
    # Insert any other custom transformation on event dict here
    ############################################################

    # Returned the mnubo-compatible object
    return mnubo_object


# Now we begin.
logger.info('Loading function')
select_mnubo_env(env_name=os.environ.get('MNUBO_ENV', 'sandbox'))


def cached_mnubo_object_exists(device_id):
    global global_cache
    global client
    assert isinstance(client, SmartObjectsClient)
    if device_id in global_cache:
        return device_id
    else:
        if client.objects.object_exists(device_id):
            global_cache[device_id] = time.time()
            return True
        else:
            return False


def mnubo_create_object(mnubo_object):
    global client
    assert isinstance(client, SmartObjectsClient)
    assert isinstance(mnubo_object, MnuboObject)
    if mnubo_object.owner_username is not None:
        if not client.owners.owner_exists(mnubo_object.owner_username):
            mnubo_object.owner_username = None
    client.objects.create(mnubo_object.build())


# AWS Lambda handler function
def lambda_handler(event, context):
    global client
    global config

    if client is None:
        client = SmartObjectsClient(client_id=config.get('client_id'),
                                    client_secret=config.get('client_secret'),
                                    environment=config.get('environment'))

    mnubo_event = map_to_mnubo_event(event=copy.deepcopy(event))

    if not cached_mnubo_object_exists(mnubo_event.device_id):
        mnubo_object = map_to_mnubo_object(event=copy.deepcopy(event))
        if mnubo_object.device_id is None or mnubo_object.object_type is None:
            raise ValueError('We cannot create object [ {0} ] because of missing '
                             '[ {1} ] or [ {2} ] fields. Event data: {3}'
                             .format(mnubo_object.device_id,
                                     field_names['device_id'],
                                     field_names['object_type'],
                                     event))
        mnubo_create_object(mnubo_object)

    if mnubo_event.device_id is None or mnubo_event.event_type is None:
        raise ValueError('We cannot send an event because of missing [ {0} ] or [ {1} ] fields. Event data: {2}'
                         .format(field_names['device_id'], field_names['event_type'], event))
    results = client.events.send(events=[mnubo_event.build()])
    logger.info('Remaining time in ms: {0}'.format(context.get_remaining_time_in_millis()))

    return results
