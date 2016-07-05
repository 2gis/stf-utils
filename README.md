[![Build Status](https://travis-ci.org/2gis/stf-utils.svg?branch=master)](https://travis-ci.org/2gis/stf-utils)
[![codecov](https://codecov.io/gh/2gis/stf-utils/branch/master/graph/badge.svg)](https://codecov.io/gh/2gis/stf-utils)



# stf-utils
Utils for Open Smartphone Test Farm (OpenSTF)


## STF-connect
> dumb script

Connects and binds all available devices on target
[OpenSTF 2.0.0](https://github.com/openstf/stf/tree/2.0.0)
instance via adb connect.

When killed, releases all binded devices and closes all adb connections.

#### requirements:
* 2.7 <= python <= 3.5
* adb

#### usage:
```
python connector.py &
adb devices
kill $!
```

### how it works:
- stf-connect makes requests for STFAPI and get list of connected devices

>for example of STFAPI request http://<stf_url>/api/v1/devices

```
[
    {
        success: true,
        device: {
            abi: "x86",
            airplaneMode: false,
            battery: {
                health: "good",
                level: 50,
                scale: 100,
                source: "ac",
                status: "charging",
                temp: 0,
                voltage: 0
            },
            browser: {
                apps: [
                    {
                        id: "com.android.browser/.BrowserActivity",
                        name: "Browser",
                        selected: true,
                        system: true,
                        type: "android-browser",
                        developer: "Google Inc."
                    }
                ],
                selected: true
            },
            channel: "i1n+UzNiirx9+t0iq3aY/Qqxbms=",
            createdAt: "2016-04-04T07:23:19.888Z",
            display: {
                density: 2,
                fps: 60.000003814697266,
                height: 1280,
                id: 0,
                rotation: 0,
                secure: true,
                size: 4.589389801025391,
                url: "ws://10.0.0.7:7408",
                width: 720,
                xdpi: 320,
                ydpi: 320
            },
            manufacturer: "UNKNOWN",
            model: " SDK built for x86",
            network: {
                connected: true,
                failover: false,
                roaming: false,
                subtype: "UMTS",
                type: "MOBILE"
            },
            operator: "Android",
            owner: null,
            phone: {
                iccid: "89014103211118510720",
                imei: "000000000000000",
                network: "UMTS",
                phoneNumber: "15555215680"
            },
            platform: "Android",
            presenceChangedAt: "2016-04-05T11:07:34.206Z",
            present: true,
            product: "sdk_phone_x86",
            provider: {
                channel: "/ZLD2jzkR8myIxIveGR/6A==",
                name: "test01"
            },
            ready: true,
            remoteConnect: false,
            remoteConnectUrl: null,
            reverseForwards: [ ],
            sdk: "23",
            serial: "emulator-5680",
            status: 3,
            statusChangedAt: "2016-04-05T11:07:36.997Z",
            version: "6.0",
            using: false
        }
    }
]
```

- then, stf-connect compares list of devices with spec.json and get list of devices which available for connect.

>for example, we want get 3 groups with devices for connect. 
>first group required 10 devices in a range from sdk version equals 16 till sdk version equals 23 and api equals x86 and platform as Android.
>if value for parameter has not been conceived then this parameter maybe removed or set as "ANY".

```
[
    {
        "group_name": "alfa",
        "amount": "10",
        "min_sdk": "16",
        "max_sdk": "23",
        "specs": {
            "abi": "x86",
            "model": "ANY",
            "platform": "Android",
            "serial": "ANY",
            "manufacturer": "ANY",
            "provider_name": "ANY"
        }
    },
    {
        "group_name": "beta",
        "amount": "2",
        "specs": {
            "abi": "ANY",
            "model": "ANY",
            "platform": "Android",
            "serial": "ANY",
            "manufacturer": "ANY",
            "provider_name": "ANY",
            "version": "4.1.2"
        }
    },
    {
        "group_name": "b",
        "amount": "2",
        "specs": {
            "abi": "ANY",
            "model": " SDK built for x86",
            "platform": "Android",
            "serial": "ANY",
            "manufacturer": "ANY",
            "provider_name": "ANY"
        }
    }
]
```
- if require parameter is such as:
```
# from response on request from STFAPI, device specification
provider: {
    channel: "/ZLD2jzkR8myIxIveGR/6A==",
    name: "test_provider_node.local"
}
```
then you should set in the following way:
```
{
    "group_name": "beta",
    "amount": "1",
    "specs": {
        "provider_name": "test_provider_node.local"
    }
}
```
- also you maybe set a range from min SDK till max SDK:
```
{
    "group_name": "alfa",
    "amount": "10",
    "min_sdk": "16",
    "max_sdk": "23"
}
```
> if doesn't set a range SDK versions then automatically will set range from 1 till 100


#### todo:
* "amount" feature
* exception handling
* logging



## STF-record:
- description:
> Utility for getting screenshots from android devices which connect with OpenSTF. Images saves to directory. Utility makes file with list of images and duration.

- install dependencies:
```
pip3 install -r requirements.txt
```
- run:
```
python3 recorder.py -serial="emulator-5555" -dir='test_dir'
python3 recorder.py -ws="127.0.0.1:9000" -dir='test_dir'
```
- options:
```
-serial - Device serial for automatic getting websocket url for saving screenshots
-ws - WebSocket URL <host:port> with ws:// or not (required!)  
-dir - custom directory for saving screenshots from device (default: ./images )
-log-level - change log level for utility (default: INFO)
-resolution - change resolution of images from device (default: as is)
```

### convert images to .webm video format by ffmpeg (tested on ffmpeg version 7:3.0.0+git1~trusty from [trusty-media repo](https://launchpad.net/~mc3man/+archive/ubuntu/trusty-media))
- install ffmpeg
```
sudo add-apt-repository --yes ppa:mc3man/trusty-media
sudo apt-get update
sudo apt-get install -y ffmpeg
```
- convert
```
cd <images_directory>
ffmpeg -f concat -i input.txt output.webm
```

