import unittest
from mnubo import map_to_mnubo_event
from mnubo import map_to_mnubo_object
from mnubo import select_mnubo_env
from smartobjects import Environments


class TestEvents(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_map_to_mnubo_event_with_device_id(self):
        device_id = '1234'
        event_type = 'dummy_event'
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz, "device_id": device_id, "event_type": event_type}
        result = map_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_object', result)
        self.assertIsInstance(result['x_object'], dict)
        self.assertIn('x_device_id', result['x_object'])
        self.assertEqual(result['x_object']['x_device_id'], device_id)
        self.assertIn('x_event_type', result)
        self.assertEqual(result['x_event_type'], event_type)
        self.assertIn('foo', result)
        self.assertEqual(result['foo'], foo)
        self.assertIn('baz', result)
        self.assertEqual(result['baz'], baz)
        pass

    def test_map_to_mnubo_event_wo_device_id(self):
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz}
        result = map_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertNotIn('x_object', result)
        self.assertEqual(event['foo'], foo)
        self.assertEqual(event['baz'], baz)
        pass

    def test_map_to_mnubo_event_wo_event_type(self):
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz}
        result = map_to_mnubo_event(event).build()
        self.assertIsInstance(result, dict)
        self.assertNotIn('x_event_type', result)
        self.assertEqual(event['foo'], foo)
        self.assertEqual(event['baz'], baz)
        pass

    def test_map_to_mnubo_object_with_everything(self):
        device_id = '1234'
        object_type = 'dummy_object'
        owner = 'yo@yomama.com'
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz, 'device_id': device_id, 'object_type': object_type, 'owner_username': owner}
        result = map_to_mnubo_object(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_device_id', result)
        self.assertEqual(result['x_device_id'], device_id)
        self.assertIn('x_object_type', result)
        self.assertEqual(result['x_object_type'], object_type)
        self.assertIn('x_owner', result)
        self.assertIsInstance(result['x_owner'], dict)
        self.assertIn('username', result['x_owner'])
        self.assertEqual(result['x_owner']['username'], owner)
        self.assertNotIn('foo', result)
        self.assertNotIn('baz', result)
        pass

    def test_map_to_mnubo_object_wo_device_id(self):
        object_type = 'dummy_object'
        owner = 'yo@yomama.com'
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz, 'object_type': object_type, 'owner_username': owner}
        result = map_to_mnubo_object(event).build()
        self.assertIsInstance(result, dict)
        self.assertNotIn('x_device_id', result)
        self.assertIn('x_object_type', result)
        self.assertEqual(result['x_object_type'], object_type)
        self.assertIn('x_owner', result)
        self.assertIsInstance(result['x_owner'], dict)
        self.assertIn('username', result['x_owner'])
        self.assertEqual(result['x_owner']['username'], owner)
        self.assertNotIn('foo', result)
        self.assertNotIn('baz', result)
        pass

    def test_map_to_mnubo_object_wo_object_type(self):
        device_id = '1234'
        owner = 'yo@yomama.com'
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz, 'device_id': device_id, 'owner_username': owner}
        result = map_to_mnubo_object(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_device_id', result)
        self.assertEqual(result['x_device_id'], device_id)
        self.assertNotIn('x_object_type', result)
        self.assertIn('x_owner', result)
        self.assertIsInstance(result['x_owner'], dict)
        self.assertIn('username', result['x_owner'])
        self.assertEqual(result['x_owner']['username'], owner)
        self.assertNotIn('foo', result)
        self.assertNotIn('baz', result)
        pass

    def test_map_to_mnubo_object_wo_owner(self):
        device_id = '1234'
        object_type = 'dummy_object'
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz, 'device_id': device_id, 'object_type': object_type}
        result = map_to_mnubo_object(event).build()
        self.assertIsInstance(result, dict)
        self.assertIn('x_device_id', result)
        self.assertEqual(result['x_device_id'], device_id)
        self.assertIn('x_object_type', result)
        self.assertEqual(result['x_object_type'], object_type)
        self.assertNotIn('x_owner', result)
        self.assertNotIn('foo', result)
        self.assertNotIn('baz', result)
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
