lambda-mnubo-python
===================

Mnubo sample lambda function in Python to be called from the AWS IoT rules engine.

The lambda function expects a `JSON` payload. It requires the `MNUBO_CLIENT_ID`, `MNUBO_CLIENT_SECRET` and `MNUBO_ENV` variables for configuration. 

If using defaults, it will assign the value of the `device_id` key to being the device id in the mnubo event. This can be changed using the `DEVICE_ID_FIELD` environment variable.

Some customization in the `map_to_mnubo_event` function can be done to rename fields. Please see the commented area in the function for more details.

Requirements:
-------------
- Docker _(packaging-only)_

Packaging:
-------------
Please run:

```
./build.sh
```