## Description:

Connect to "screen streaming service", provided by STF, save screenshots of your Android device, and create a video.

## Save screenshots
- run:
```
stf-record --serial="emulator-5555" --dir='test_dir'
```
or
```
stf-record --ws="127.0.0.1:9000" --dir='test_dir'
```
- options:
```
--serial - Device serial for automatic getting websocket url for saving screenshots
--ws - WebSocket URL <host:port> with ws:// or not (required!)
--dir - custom directory for saving screenshots from device (default: ./images )
--log-level - change log level for utility (default: INFO)
--resolution - change resolution of images from device (default: as is)
```

## Create video
convert images to .webm video format by ffmpeg (tested on ffmpeg version 7:3.0.0+git1~trusty from [trusty-media repo](https://launchpad.net/~mc3man/+archive/ubuntu/trusty-media))
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

