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
#### todo:
* "amount" feature
* "min/max sdk" feature
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

### convert images to .webm video format by ffmpeg (tested on ffmpeg version 	7:3.0.0+git1~trusty from [trusty-media repo](https://launchpad.net/~mc3man/+archive/ubuntu/trusty-media))
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

