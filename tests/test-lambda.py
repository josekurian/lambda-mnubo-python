import unittest
from mnubo import map_shadow_update_to_mnubo_event
from mnubo import map_iot_event_to_mnubo_event
from mnubo import map_thing_to_smart_object
from mnubo import select_mnubo_env
from smartobjects import Environments


class TestLambda(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_map_iot_event_to_mnubo_event_with_device_id(self):
        device_id = '1234'
        event_type = 'temperature_change'
        temperature = 32
        humidity = 0.45

        event = dict(
            device_id=device_id,
            event_type=event_type,
            temperature=temperature,
            humidity=humidity
        )

        result = map_iot_event_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_object', result)
        self.assertIsInstance(result['x_object'], dict)
        self.assertIn('x_device_id', result['x_object'])
        self.assertEqual(result['x_object']['x_device_id'], device_id)
        self.assertIn('x_event_type', result)
        self.assertEqual(result['x_event_type'], event_type)
        self.assertIn('temperature', result)
        self.assertEqual(result['temperature'], temperature)
        self.assertIn('humidity', result)
        self.assertEqual(result['humidity'], humidity)
        pass

    def test_map_iot_event_to_mnubo_event_wo_device_id(self):
        temperature = 32
        humidity = 0.45

        event = dict(
            temperature=temperature,
            humidity=humidity
        )

        result = map_iot_event_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertNotIn('x_object', result)
        self.assertEqual(result['temperature'], temperature)
        self.assertEqual(result['humidity'], humidity)
        pass

    def test_map_iot_event_to_mnubo_event_with_default_event_type(self):
        device_id = '1234'
        temperature = 32
        humidity = 0.45

        event = dict(
            device_id=device_id,
            temperature=temperature,
            humidity=humidity
        )

        result = map_iot_event_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_event_type', result)
        self.assertEqual(result['x_event_type'], 'aws_iot_event')
        self.assertEqual(result['temperature'], temperature)
        self.assertEqual(result['humidity'], humidity)
        pass

    def test_map_shadow_update_to_mnubo_event_with_device_id(self):
        device_id = '1234'
        event_type = 'shadow_update'  # This is a static value in the code.
        temperature = 32
        humidity = 0.45
        event = dict(
            device_id=device_id,
            state=dict(
                reported=dict(
                    temperature=temperature,
                    humidity=humidity
                )
            )
        )
        result = map_shadow_update_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_object', result)
        self.assertIsInstance(result['x_object'], dict)
        self.assertIn('x_device_id', result['x_object'])
        self.assertEqual(result['x_object']['x_device_id'], device_id)
        self.assertIn('x_event_type', result)
        self.assertEqual(result['x_event_type'], event_type)
        self.assertIn('temperature', result)
        self.assertEqual(result['temperature'], temperature)
        self.assertIn('humidity', result)
        self.assertEqual(result['humidity'], humidity)
        pass

    def test_map_to_mnubo_object_with_everything(self):
        device_id = '1234'
        object_type = 'temperatureThing'
        owner = 'yo@yomama.com'
        firmware_version = '0.1'
        thing_model = 'temperature-thingy'
        thing_data = dict(
            thingName=device_id,
            thingTypeName=object_type,
            attributes=dict(
                owner_username=owner,
                firmware_version=firmware_version,
                model=thing_model
            )
        )
        result = map_thing_to_smart_object(thing=thing_data).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_device_id', result)
        self.assertEqual(result['x_device_id'], device_id)
        self.assertIn('x_object_type', result)
        self.assertEqual(result['x_object_type'], object_type)
        self.assertIn('x_owner', result)
        self.assertIsInstance(result['x_owner'], dict)
        self.assertIn('username', result['x_owner'])
        self.assertEqual(result['x_owner']['username'], owner)
        self.assertIn('firmware_version', result)
        self.assertEqual(result['firmware_version'], firmware_version)
        self.assertIn('model', result)
        self.assertEqual(result['model'], thing_model)
        pass

    def test_map_to_mnubo_object_wo_device_id(self):
        object_type = 'temperatureThing'
        owner = 'yo@yomama.com'
        firmware_version = '0.1'
        thing_model = 'temperature-thingy'
        thing_data = dict(
            thingTypeName=object_type,
            attributes=dict(
                owner_username=owner,
                firmware_version=firmware_version,
                model=thing_model
            )
        )
        result = map_thing_to_smart_object(thing=thing_data).build()
        self.assertIsInstance(result, dict)
        self.assertNotIn('x_device_id', result)
        self.assertIn('x_object_type', result)
        self.assertEqual(result['x_object_type'], object_type)
        self.assertIn('x_owner', result)
        self.assertIsInstance(result['x_owner'], dict)
        self.assertIn('username', result['x_owner'])
        self.assertEqual(result['x_owner']['username'], owner)
        self.assertIn('firmware_version', result)
        self.assertEqual(result['firmware_version'], firmware_version)
        self.assertIn('model', result)
        self.assertEqual(result['model'], thing_model)
        pass

    def test_map_to_mnubo_object_wo_object_type(self):
        device_id = '1234'
        owner = 'yo@yomama.com'
        firmware_version = '0.1'
        thing_model = 'temperature-thingy'
        thing_data = dict(
            thingName=device_id,
            attributes=dict(
                owner_username=owner,
                firmware_version=firmware_version,
                model=thing_model
            )
        )
        result = map_thing_to_smart_object(thing=thing_data).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_device_id', result)
        self.assertEqual(result['x_device_id'], device_id)
        self.assertNotIn('x_object_type', result)
        self.assertIn('x_owner', result)
        self.assertIsInstance(result['x_owner'], dict)
        self.assertIn('username', result['x_owner'])
        self.assertEqual(result['x_owner']['username'], owner)
        self.assertIn('firmware_version', result)
        self.assertEqual(result['firmware_version'], firmware_version)
        self.assertIn('model', result)
        self.assertEqual(result['model'], thing_model)
        pass

    def test_map_to_mnubo_object_wo_owner(self):
        device_id = '1234'
        object_type = 'temperatureThing'
        firmware_version = '0.1'
        thing_model = 'temperature-thingy'
        thing_data = dict(
            thingName=device_id,
            thingTypeName=object_type,
            attributes=dict(
                firmware_version=firmware_version,
                model=thing_model
            )
        )
        result = map_thing_to_smart_object(thing=thing_data).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_device_id', result)
        self.assertEqual(result['x_device_id'], device_id)
        self.assertIn('x_object_type', result)
        self.assertEqual(result['x_object_type'], object_type)
        self.assertNotIn('x_owner', result)
        self.assertIn('firmware_version', result)
        self.assertEqual(result['firmware_version'], firmware_version)
        self.assertIn('model', result)
        self.assertEqual(result['model'], thing_model)
        pass

    def test_select_environment_production(self):
        environment = 'production'
        result = select_mnubo_env(environment)
        self.assertEqual(result, Environments.Production)
        pass

    def test_select_environment_sandbox(self):
        environment = 'sandbox'
        result = select_mnubo_env(environment)
        self.assertEqual(result, Environments.Sandbox)
        pass

    def test_select_environment_other(self):
        environment = 'foo'
        with self.assertRaises(EnvironmentError):
            select_mnubo_env(environment)
        pass
