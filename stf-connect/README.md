## stf-connect
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
python stf-connect.py &
adb devices
kill $!
```
> hint: `stfapi.py` and `connector.py` are still under development
