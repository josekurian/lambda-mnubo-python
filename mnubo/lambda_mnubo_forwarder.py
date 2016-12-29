#!/usr/bin/env python

from __future__ import print_function
import os
import logging
import re
import time
import copy
import json
from lru import LRU
from smartobjects import SmartObjectsClient
from smartobjects import Environments
import boto3


# Global variables
global_cache = None

# Mnubo config
config = dict()
# Please use production or sandbox for the following in the environment variable.
config['environment'] = None
config['client_id'] = os.environ.get('MNUBO_CLIENT_ID', None)
config['client_secret'] = os.environ.get('MNUBO_CLIENT_SECRET', None)
config['use_object_cache'] = bool(os.environ.get('USE_OBJECT_CACHE', 1))
config['cache_max_entries'] = int(os.environ.get('CACHE_MAX_ENTRIES', 1000000))
config['cache_validity_period'] = int(os.environ.get('CACHE_VALIDITY_PERIOD', 3600))

# Mnubo SmartObjects Client
mnubo_client = None
# AWS IoT Client
iot_client = None

# Default field name mappings
field_names = dict()
field_names['device_id'] = os.environ.get('DEVICE_ID_FIELD', 'device_id')
field_names['event_id'] = os.environ.get('EVENT_ID_FIELD', 'event_id')
field_names['event_type'] = os.environ.get('EVENT_TYPE_FIELD', 'event_type')
field_names['owner_username'] = os.environ.get('OWNER_USERNAME_FIELD', 'owner_username')
field_names['object_attributes'] = os.environ.get('OBJECT_ATTR_ROOT_FIELD', 'object_attributes')
field_names['object_type'] = os.environ.get('OBJECT_TYPE_FIELD', 'object_type')
field_names['timestamp'] = os.environ.get('TIMESTAMP_FIELD', 'timestamp')
field_names['latitude'] = os.environ.get('LATITUDE_FIELD', 'latitude')
field_names['longitude'] = os.environ.get('LONGITUDE_FIELD', 'longitude')
field_names['last_update'] = os.environ.get('LAST_UPDATE_FIELD', 'last_update')
field_names['registration_date'] = os.environ.get('REGISTRATION_DATE_FIELD', 'registration_date')

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
    def device_id(self, value):
        if value is not None:
            self._device_id = value

    @property
    def event_data(self):
        return self._event_data

    @event_data.setter
    def event_data(self, value):
        if value is None:
            self._event_data = dict()
        if value is not None:
            assert isinstance(value, dict)
        self._event_data = value

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


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=ignore_dicts) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=ignore_dicts): _byteify(value, ignore_dicts=ignore_dicts)
            for key, value in data.items()
        }
    # if it's anything else, return it in its original form
    return data


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

    # Cleanup
    if field_names['object_attributes'] in event:
        event.pop(field_names['object_attributes'])
    if field_names['registration_date'] in event:
        event.pop(field_names['longitude'])
    if field_names['object_type'] in event:
        event.pop(field_names['object_type'])
    if field_names['owner_username'] in event:
        event.pop(field_names['owner_username'])
    if field_names['last_update'] in event:
        event.pop(field_names['last_update'])

    ############################################################
    # Insert any other custom transformation on event dict here
    ############################################################

    # Assign the free-form data to mnubo
    mnubo_data.event_data = event
    # Returned the mnubo-compatible object
    return mnubo_data


def map_to_mnubo_object(device_id):
    global field_names

    # Create a new mnubo-formatted event
    mnubo_object = MnuboObject()
    assert isinstance(mnubo_object, MnuboObject)
    logger.info('About to get thing data on: {0}'.format(device_id))
    thing = get_thing_attributes(device_id=device_id)
    mnubo_object.device_id = thing['thingName']
    mnubo_object.object_type = thing['thingTypeName']

    thing_attrs = copy.deepcopy(thing['attributes'])

    if field_names['device_id'] in thing_attrs:
        mnubo_object.owner_username = thing_attrs.get(field_names['device_id'], None)
        thing_attrs.pop(field_names['device_id'])
    # if field_names['owner_username'] in thing_attrs:
    #     mnubo_object.owner_username = thing_attrs.get(field_names['owner_username'], None)
    #     thing_attrs.pop(field_names['owner_username'])
    if field_names['latitude'] in thing_attrs:
        mnubo_object.latitude = thing_attrs.get(field_names['latitude'], None)
        thing_attrs.pop(field_names['latitude'])
    if field_names['last_update'] in thing_attrs:
        mnubo_object.last_update_timestamp = thing_attrs.get(field_names['last_update'], None)
        thing_attrs.pop(field_names['last_update'])
    if field_names['longitude'] in thing_attrs:
        mnubo_object.longitude = thing_attrs.get(field_names['longitude'], None)
        thing_attrs.pop(field_names['longitude'])
    if field_names['registration_date'] in thing_attrs:
        mnubo_object.registration_date = thing_attrs.get(field_names['registration_date'], None)
        thing_attrs.pop(field_names['longitude'])
    if field_names['timestamp'] in thing_attrs:
        mnubo_object.timestamp = thing_attrs.get(field_names['timestamp'], None)
        thing_attrs.pop(field_names['timestamp'])

    ############################################################
    # Insert any other custom transformation on event dict here
    ############################################################
    if 'temperature' in thing_attrs:
        thing_attrs.pop('temperature')
    if 'owner_username' in thing_attrs:
        thing_attrs.pop('owner_username')

    mnubo_object.custom_attributes = thing_attrs

    # Returned the mnubo-compatible object
    return mnubo_object


# Now we begin.
logger.info('Loading mnubo forwarder function...')
config['environment'] = select_mnubo_env(env_name=os.environ.get('MNUBO_ENV', 'sandbox'))
if config['use_object_cache']:
    logger.info('Use of mnubo object cache enabled.')
else:
    logger.info('Use of mnubo object cache disabled.')


def cached_mnubo_object_exists(device_id):
    global global_cache
    global config
    now = int(time.time())

    if not isinstance(global_cache, LRU):
        if not isinstance(config['cache_max_entries'], int):
            raise ValueError('cache_max_entries must be an integer')
        global_cache = LRU(config['cache_max_entries'])

    if not isinstance(config['cache_validity_period'], int):
        raise ValueError('cache_validity_period must be an integer')

    found = global_cache.get(device_id, None)
    if found and found > now:
        rc = True
    else:
        rc = mnubo_object_exists(device_id)
        if rc:
            global_cache[device_id] = now + config['cache_validity_period']
    return rc


def mnubo_object_exists(device_id):
    c = get_mnubo_client()
    if c.objects.object_exists(device_id):
        return True
    else:
        return False


def mnubo_create_object(mnubo_object):
    assert isinstance(mnubo_object, MnuboObject)
    c = get_mnubo_client()
    if mnubo_object.owner_username is not None:
        if not c.owners.owner_exists(mnubo_object.owner_username):
            mnubo_object.owner_username = None
    try:
        c.objects.create(mnubo_object.build())
    except ValueError as e:
        p = re.compile(r"already exists")
        if p.search(e):
            pass
        else:
            raise


def send_mnubo_event(mnubo_event):
    rc = False
    c = get_mnubo_client()
    if mnubo_event.device_id is None or mnubo_event.event_type is None:
        raise ValueError('We cannot send an event because of missing [ {0} ] or [ {1} ] fields.'
                         .format(field_names['device_id'], field_names['event_type']))
    results = c.events.send(events=[mnubo_event.build()])
    if results is not None:
        rc = True
    return rc


def get_mnubo_client():
    global mnubo_client
    global config
    if not isinstance(mnubo_client, SmartObjectsClient):
        mnubo_client = SmartObjectsClient(client_id=config['client_id'],
                                          client_secret=config['client_secret'],
                                          environment=config['environment'])
    return mnubo_client


def get_aws_iot_client():
    global iot_client
    if iot_client is None:
        iot_client = boto3.client('iot')
    return iot_client


def get_thing_attributes(device_id):
    c = get_aws_iot_client()
    r = c.describe_thing(thingName=device_id)
    # Cleanup
    r.pop('ResponseMetadata')
    r.pop('version')
    r.pop('defaultClientId')
    return r


# AWS Lambda handler function
def lambda_handler(event, context):

    try:
        mnubo_event = map_to_mnubo_event(event=copy.deepcopy(event))

        if config['use_object_cache']:
            target_object_exists = cached_mnubo_object_exists(mnubo_event.device_id)
        else:
            target_object_exists = mnubo_object_exists(mnubo_event.device_id)
        if not target_object_exists:
            mnubo_object = map_to_mnubo_object(device_id=mnubo_event.device_id)
            mnubo_create_object(mnubo_object)
        rc = send_mnubo_event(mnubo_event)
    except Exception:
        logger.error('An unexpected error occurred: event data is: {0}'.format(str(event)))
        raise

    logger.info('Remaining time in ms: {0}'.format(context.get_remaining_time_in_millis()))
    return rc
