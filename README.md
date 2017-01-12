lambda-mnubo-python
===================

Mnubo sample lambda function in Python to be called from the AWS IoT rules engine.

Requirements
-------------
- Docker _(packaging-only)_
- Python: _see the_ [`requirements.txt`](requirements.txt) _file_
- mnubo credentials for a sandbox and/or a production account
- A AWS IAM profile associated with the lambda function to grant read-only access to Things.

Packaging
----------
Please run:

```
./build.sh
```

This will generate a `lambda_package.zip` file for use with the AWS Lambda cli or Web console.

Configuration
-------------

When deploying the lambda function, basic behaviour can be modified using environment variables. These are the following:

* `MNUBO_CLIENT_ID`: The mnubo client ID credential
* `MNUBO_CLIENT_SECRET`: The mnubo client secret credential
* `USE_OBJECT_CACHE`: Defaults to 1 to use the local LRU object cache. Set to 0 to disable it.
* `CACHE_MAX_ENTRIES`: Defaults to 1000000, sets the maximum number of entries in the LRU cache. Beware of memory use.
* `CACHE_VALIDITY_PERIOD`: Defaults to 3600, number of seconds before an entrie is re-verified.
* `SHADOW_UPDATE_EVENT_TYPE`: Defaults to `shadow_update`. Sets the event type for shadow update generated events in the mnubo platform. 
* `IOT_MQTT_DEFAULT_EVENT_TYPE`: Defaults to `aws_iot_event`. Sets the custom MQTT topic generated event types in the mnubo platform if not provided in the events. 

To modify the behaviour of the mapping functions, we provide variables for Things (SmartObjects) and for events
Object attribute blacklist:

For Things to SmartObjects mappings:
* The `smart_object_attributes_mapping` variable must be initialized as a dict with source field names as keys and target field names as values.
* The `smart_object_attributes_blacklist` variable must be initialized as a list of Thing attribute names that we do NOT want to send to the mnubo platform. These will be filtered out.

For IoT custom events or Thing shadow documents to mnubo Events mappings:

* The `event_attributes_mapping` variable must be initialized as a dict with source field names as keys and target field names as values.
* The `event_attributes_blacklist` variable must be initialized as a list of event or shadow document reported values that we do NOT want to send to the mnubo platform. These will be filtered out. 

When deploying the lambda function, you will need to have the following IAM policy associated with it.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iot:DescribeThing",
                "iot:GetThingShadow",
                "iot:ListThings"
            ],
            "Resource": [
                "your_aws_iot_arn:thing/*"
            ]
        }
    ]
}
```

Available handlers
------------------
* `lambda_mnubo_forwarder.iot_custom_event_handler`: To be used when IoT thing events are sent into a seperate custom MQTT topic. The messages sent to the function must contain a `device_id` field matching the AWS IoT Thing name at a minimum. This will create a corresponding SmartObject in the mnubo platform and send the events through. Here's a sample rule select statement:
```
SELECT * FROM 'temperature_thing_events'
```
* `lambda_mnubo_forwarder.iot_shadow_update_event_handler`: To be used when the IoT shadow documents are to be used to send time series to mnubo. A rule must be placed on the shadow accepted topic must be placed. The Thing name must be added as the device_id Here's a sample rule select statement:
```
SELECT *, topic(3) as device_id FROM '$aws/things/+/shadow/update/accepted'
```
Tests
------------------

Sample tests are included in the tests folder. These are mainly meant to test the transformation functions. You can use these to test your code prior to deploying to AWS Lambda.
