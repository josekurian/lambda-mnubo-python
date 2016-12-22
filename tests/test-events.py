import unittest
from mnubo import map_to_mnubo_event
from mnubo import select_mnubo_env
from smartobjects import Environments


class TestEvents(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_map_to_mnubo_event_with_device_id(self):
        device_id = '1234'
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz, "device_id": device_id}
        result = map_to_mnubo_event(event)
        self.assertIsInstance(result, dict)
        self.assertIn('x_object', result)
        self.assertIsInstance(result['x_object'], dict)
        self.assertIn('x_device_id', result['x_object'])
        self.assertEqual(result['x_object']['x_device_id'], device_id)
        self.assertIn('foo', result)
        self.assertEqual(result['foo'], foo)
        self.assertIn('baz', result)
        self.assertEqual(result['baz'], baz)
        pass

    def test_map_to_mnubo_event_wo_device_id(self):
        foo = 'abc123'
        baz = 'def456'
        event = {'foo': foo, 'baz': baz}
        result = map_to_mnubo_event(event)
        self.assertIsInstance(result, dict)
        self.assertNotIn('x_object', result)
        self.assertEqual(event['foo'], foo)
        self.assertEqual(event['baz'], baz)
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
