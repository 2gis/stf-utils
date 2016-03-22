# stf-utils
Utils for Open Smartphone Test Farm (OpenSTF)

### STF-record:
- description:
> Utility for getting screenshots from android devices which connect with OpenSTF. Images saves to directory. Utility makes file with list of images and duration.

- install dependencies:
```
pip3 install -r requirements.txt
```
- run:
```
python3 stf-record.py -ws="127.0.0.1:9000" -dir='test_dir'
```
- options:
```
-ws - WebSocket URL (required!)
-dir - custom directory for saving screenshots from device (default: ./images )
-log-level - change log level for utility (default: INFO)
-resolution - change resolution of images from device (default: as is)
```