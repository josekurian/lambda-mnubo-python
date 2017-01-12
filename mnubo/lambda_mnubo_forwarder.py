#!/usr/bin/env python

from __future__ import print_function
import os
import logging
import re
import time
import copy
from lru import LRU
from smartobjects import SmartObjectsClient
from smartobjects import Environments
import boto3


# Global variables
global_cache = None

# Mnubo config
config = dict(
    environment=None,
    client_id=os.environ.get('MNUBO_CLIENT_ID', None),
    client_secret=os.environ.get('MNUBO_CLIENT_SECRET', None),
    use_object_cache=bool(os.environ.get('USE_OBJECT_CACHE', 1)),
    cache_max_entries=int(os.environ.get('CACHE_MAX_ENTRIES', 1000000)),
    cache_validity_period=int(os.environ.get('CACHE_VALIDITY_PERIOD', 3600))
)

# Mnubo SmartObjects Client
mnubo_client = None
# AWS IoT Client
iot_client = None

SHADOW_UPDATE_EVENT_TYPE = os.environ.get('SHADOW_UPDATE_DEFAULT_EVENT_TYPE', 'shadow_update')
IOT_MQTT_EVENT_TYPE = os.environ.get('IOT_MQTT_DEFAULT_EVENT_TYPE', 'aws_iot_event')

# TODO: Find a way to take the event attribute mapping data from a configuration file
event_attributes_mapping = dict()
# TODO: Find a way to take the event attribute blacklist data from a configuration file
event_attributes_blacklist = list()
# TODO: Find a way to take the smart object attribute mapping data from a configuration file
smart_object_attributes_mapping = dict()
# TODO: Find a way to take the smart object attribute blacklist data from a configuration file
smart_object_attributes_blacklist = list()

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# TODO: Remove MnuboObject class once pull request is accepted in smartobjects sdk.
class SmartObject(object):
    """Helper class to build a mnubo SmartObject that will be assembled as a JSON
       structure to be sent to the mnubo platform.
    """
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


# TODO: Remove MnuboEvent class once pull request is accepted in smartobjects sdk.
class Event(object):
    """Helper class to build a mnubo event that will be assembled as a JSON
       structure to be sent to the mnubo platform.
    """
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
            mnubo_object = SmartObject()
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


def mnubo_object_exists(device_id):
    """ Method to lookup the object on the mnubo platform
    :param device_id:
    :return: True if it exists, false if it doesn't
    """
    c = get_mnubo_client()
    if c.objects.object_exists(device_id):
        return True
    else:
        return False


def cached_mnubo_object_exists(device_id):
    """ Method to wrap the object existence checking in a cached object
    :param device_id: The device id of the object
    :return: True of the object exists or False if it doesn't
    """
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


def mnubo_create_object(mnubo_object):
    """ Method to handle the mnubo object creation
    :param mnubo_object: Takes the MnuboObject object and creates the object.
    """
    assert isinstance(mnubo_object, SmartObject)
    c = get_mnubo_client()
    if mnubo_object.owner_username is not None:
        if not c.owners.owner_exists(mnubo_object.owner_username):
            mnubo_object.owner_username = None
    try:
        c.objects.create(mnubo_object.build())
    except ValueError as e:
        p = re.compile(r'already exists')
        if p.search(e.message):
            pass
        else:
            raise


def send_mnubo_event(mnubo_event):
    """ Method to send events to the mnubo platform.
    :param mnubo_event: Takes a MnuboEvent and sends it to the mnubo platform
    :return: True if the event was sent, False if not.
    """
    rc = False
    c = get_mnubo_client()
    if mnubo_event.device_id is None or mnubo_event.event_type is None:
        raise ValueError('We cannot send an event because of missing [ {0} ] or [ {1} ] fields.'
                         .format('device_id', 'event_type'))
    results = c.events.send(events=[mnubo_event.build()])
    if results is not None:
        rc = True
    return rc


def get_mnubo_client():
    """ A method to return the mnubo client and initialize it if not initialized
    :return: A SmartObjectsClient
    """
    global mnubo_client
    global config
    if not isinstance(mnubo_client, SmartObjectsClient):
        mnubo_client = SmartObjectsClient(client_id=config['client_id'],
                                          client_secret=config['client_secret'],
                                          environment=config['environment'])
    return mnubo_client


def get_aws_iot_client():
    """ A method to initialize and return the AWS SDK IoT client.
    :return: A boto3 IoT client.
    """
    global iot_client
    if iot_client is None:
        iot_client = boto3.client('iot')
    return iot_client


def get_thing_attributes(device_id):
    """ Method to wrap getting the AWS IoT device registry thing attributes. We must clean the returned data structure
    to use it later on.
    :param device_id: The AWS IoT thing name, the mnubo device ID.
    :return: The cleaned thing dict data structure.
    """
    c = get_aws_iot_client()
    r = c.describe_thing(thingName=device_id)
    # Cleanup
    r.pop('ResponseMetadata', None)
    r.pop('version', None)
    r.pop('defaultClientId', None)
    return r


def select_mnubo_env(env_name):
    """ Method to return the SmartObjectsClient environment object matched to the environment variable.
    :param env_name: 'production' or 'sandbox'
    :return: A mnubo object for the environment
    """
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


def map_thing_to_smart_object(thing):
    """ Mapping method for AWS IoT device registry Thing to a mnubo SmartObject This method operates with well-known
    field names, builds a SmartObject ready to be sent to the mnubo platform.

    :param thing: The thing definition JSON document.
    :return: A SmartObject object.
    """
    # Create a new mnubo-formatted event
    mnubo_object = SmartObject()
    assert isinstance(mnubo_object, SmartObject)
    # Assign the thing name as the mnubo device_id
    mnubo_object.device_id = thing.get('thingName', None)
    # Assign the thing type name as the mnubo SmartObject type
    mnubo_object.object_type = thing.get('thingTypeName', None)
    # Get a copy of the attributes so we can manipulate them later.
    thing_attrs = copy.deepcopy(thing.get('attributes', dict()))

    # If the owner username is present, take it.
    mnubo_object.owner_username = thing_attrs.pop('owner_username', None)
    # If a latitude was defined, take it.
    mnubo_object.latitude = thing_attrs.pop('latitude', None)
    # If a last update timestamp is available, take it.
    mnubo_object.last_update_timestamp = thing_attrs.pop('last_update', None)
    # If a longitude was defined, take it.
    mnubo_object.longitude = thing_attrs.pop('longitude', None)
    # If a registration date is available, take it.
    mnubo_object.registration_date = thing_attrs.pop('registration_date', None)
    # If a timestamp for the object is available, take it.
    mnubo_object.timestamp = thing_attrs.pop('timestamp', None)

    # Cleanup unwanted keys defined in the blacklist variable.
    for v in smart_object_attributes_blacklist:
        thing_attrs.pop(v, None)

    # Add custom attributes to be added to the mnubo SmartObject
    for k, v in thing_attrs.items():
        # If the attribute key is to be mapped to another key
        if k in smart_object_attributes_mapping:
            # Perform key mapping and assign value
            mnubo_object.custom_attributes.update({smart_object_attributes_mapping[k]: v})
        else:
            # Assign key and value directly
            mnubo_object.custom_attributes.update({k: v})

    # Returned the mnubo-compatible object
    return mnubo_object


def manage_object(device_id):
    """ Method to manipulate mnubo SmartObjects. To be used in the different handlers.
    :param device_id: The thing name or mnubo SmartObject device id
    """
    # If we are to use local caching of objects
    if config['use_object_cache']:
        # Check using the cache
        target_object_exists = cached_mnubo_object_exists(device_id)
    else:
        # Check directly
        target_object_exists = mnubo_object_exists(device_id)
    if not target_object_exists:
        # Get the Device Registry Thing definition
        logger.info('About to get thing data on: {0}'.format(device_id))
        thing = get_thing_attributes(device_id=device_id)
        # If the object does not exist, perform the mapping and create it.
        mnubo_object = map_thing_to_smart_object(thing=thing)
        mnubo_create_object(mnubo_object)


def map_shadow_update_to_mnubo_event(event):
    """ Mapping method for AWS IoT shadow device documents to a mnubo event This method operates with well-known
    field names, builds a mnubo event ready to be sent to the mnubo platform.
    :param event: The event received by the handler
    :return: A mnubo Event
    """
    # Sanity check, we must have a dict shadow document.
    assert isinstance(event, dict)
    # Create a new mnubo-formatted event
    mnubo_data = Event()
    # If a field called device_id is present, use it. This should be injected using the Rule engine rule. See readme.
    mnubo_data.device_id = event.get('device_id', None)
    # We are only interested by the Thing reported state.
    shadow_reported = event.get('state', dict()).get('reported', dict())
    # Sanity check #2, It must be a dict
    assert isinstance(shadow_reported, dict)

    # Assign a default or environment variable event type to this event
    mnubo_data.event_type = SHADOW_UPDATE_EVENT_TYPE
    # Get the timestamp of this shadow update accepted document
    mnubo_data.timestamp = event.get('metadata', dict()).get('timestamp', None)
    # If an event id is present, use it. Else, the mnubo platform will generate one.
    mnubo_data.event_id = shadow_reported.pop('event_id', None)
    # If a latitude is present, take it.
    mnubo_data.latitude = shadow_reported.pop('latitude', None)
    # If a longitude is present, take it.
    mnubo_data.longitude = shadow_reported.pop('longitude', None)

    # Cleanup unwanted keys before using the event_attributes_blacklist list.
    for v in event_attributes_blacklist:
        shadow_reported.pop(v, None)

    # Add custom time series
    for k, v in shadow_reported.items():
        # If the key is in the event_attributes_mapping dict
        if k in event_attributes_mapping:
            # Perform key mapping and assign the mapped key with the value
            mnubo_data.event_data.update({event_attributes_mapping[k]: v})
        else:
            # Assign key and value directly
            mnubo_data.event_data.update({k: v})

    # Returned the mnubo-compatible object
    return mnubo_data


def map_iot_event_to_mnubo_event(event):
    """ Mapping method to map a Thing generated event in a MQTT topic to a mnubo event
    This method operates with well-known field names, builds a mnubo event ready to be sent to the mnubo platform.
    :param event: The event received by the handler
    :return: A mnubo Event
    """
    # Sanity check, make sure the event is a dict.
    assert isinstance(event, dict)

    # Create a new mnubo-formatted event
    mnubo_data = Event()
    # If there's an event_type in the event, use it, else use the content of the constant variable that can be
    # modified using an environment variable.
    mnubo_data.event_type = event.pop('event_type', IOT_MQTT_EVENT_TYPE)
    # If there's a timestamp in the event, use it.
    mnubo_data.timestamp = event.pop('timestamp', None)
    # If there's a device_id in the event, take it.
    mnubo_data.device_id = event.pop('device_id', None)
    # If there's a custom event id, take it.
    mnubo_data.event_id = event.pop('event_id', None)
    # If there's a latitude defined, take it.
    mnubo_data.latitude = event.pop('latitude', None)
    # If there's a longitude defined, take it.
    mnubo_data.longitude = event.pop('longitude', None)

    # Cleanup unwanted keys before using the event_attributes_blacklist list.
    for v in event_attributes_blacklist:
        event.pop(v, None)

    # Add custom time series
    for k, v in event.items():
        # If the key is in the event_attributes_mapping dict
        if k in event_attributes_mapping:
            # Perform key mapping and assign the mapped key with the value
            mnubo_data.event_data.update({event_attributes_mapping[k]: v})
        else:
            # Assign key and value directly
            mnubo_data.event_data.update({k: v})

    # Returned the mnubo-compatible object
    return mnubo_data


# Now we begin.
logger.info('Loading mnubo forwarder function...')
# Setup the config value to the right environment object.
config['environment'] = select_mnubo_env(env_name=os.environ.get('MNUBO_ENV', 'sandbox'))
# Make sure we leave traces behind that we're using caching or not.
if config['use_object_cache']:
    logger.info('Use of mnubo object cache enabled.')
else:
    logger.info('Use of mnubo object cache disabled.')


def iot_custom_event_handler(event, context):
    """ AWS Lambda handler to be triggered by the AWS IoT rules engine. To be used with events in a custom MQTT topic.
    :param event: A JSON document built by the rule
    :param context: A AWS Lambda Context object.
    :return: True if it works, false if not.
    """
    try:
        # Map the event document to a mnubo event.
        mnubo_event = map_iot_event_to_mnubo_event(event=copy.deepcopy(event))
        # Create the object if needed.
        manage_object(mnubo_event.device_id)
        # Send the event to the mnubo platform
        rc = send_mnubo_event(mnubo_event)
        logger.info('Remaining time in ms: {0}'.format(context.get_remaining_time_in_millis()))
    except Exception:
        logger.error('An unexpected error occurred: event data is: {0}'.format(str(event)))
        raise
    return rc


def iot_shadow_update_event_handler(event, context):
    """ AWS Lambda handler to be triggered by the AWS IoT rules engine. To be used with shadow update documents.
    :param event: A shadow update JSON document.
    :param context: A AWS Lambda Context object.
    :return: True if it works, false if not.
    """
    try:
        # Map the shadow update document to the mnubo event
        mnubo_event = map_shadow_update_to_mnubo_event(event=copy.deepcopy(event))
        # Create the object if needed.
        manage_object(mnubo_event.device_id)
        # Send the event to the mnubo platform
        rc = send_mnubo_event(mnubo_event)
        logger.info('Remaining time in ms: {0}'.format(context.get_remaining_time_in_millis()))
    except Exception:
        logger.error('An unexpected error occurred: event data is: {0}'.format(str(event)))
        raise
    return rc
