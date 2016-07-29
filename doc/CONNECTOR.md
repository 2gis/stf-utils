
## Requirements:
* Your [STF](https://github.com/openstf/stf) instance is ready and you are using v2.0 or above.
* 2.7 <= python <= 3.5
* adb

## Quick start:
1. Generate OAuth token in web-interface as described [here](https://github.com/openstf/stf/blob/master/doc/API.md#authentication).
2. Edit [config.ini](../config.ini) - fill `OAUTH_TOKEN` and `host` values
2. Specify devices you want to connect by editing `spec.json` (examples below)
2. Run `python connector.py`

`connector.py` will connect and bind devices from your STF instance specified in `spec.json` file.

If some device for some reason will disconnect, `connector.py` will try to reconnect it again.

To release devices binded by `connector.py`, type CTRL+C or kill `connector.py` process.

## Examples of `spec.json` file:
##### Connect all available devices
```json
[
    {
        "group_name": "all_devices",
        "amount": "999"
    }
]
```
##### Connect one specific device by its serialno (spec.json example)
```json
[
    {
        "group_name": "device_by_serial_no",
        "amount": "1",
        "specs": {
            "serial": "<your device serial>"
        }
    }
]
```
##### Connect five armeabi-v7a devices 
```json
[
    {
        "group_name": "device_by_serial_no",
        "amount": "5",
        "specs": {
            "serial": "ANY",
            "abi": "armeabi-v7a"
        }
    }
]
```


### Advanced usage: Use one spec.json for different cases
You can specify several groups in your `spec.json` file and control which groups to connect with `-groups` argument for `connector.py`.

For example, you `spec.json` looks like:
```json
[
    {
        "group_name": "x86_Android_6",
        "amount": "8",
        "min_sdk": "23",
        "specs": {
            "serial": "ANY",
            "abi": "x86"
        }
    },
    {
        "group_name": "unit_test_devices",
        "amount": "100",
        "specs": {
            "platform": "Android",
            "serial": "ANY",
            "manufacturer": "ANY",
            "provider_name": "ANY"
        }
    },
    {
        "group_name": "the_magnificent_armeabi-v7a_seven",
        "amount": "7",
        "specs": {
            "abi": "armeabi-v7a"
        }
    }
]
```
then, if you want only last two groups, you should run:
```shell
python connector.py -groups the_magnificent_armeabi-v7a_seven,unit_test_devices
```
