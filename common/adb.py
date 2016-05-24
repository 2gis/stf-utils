import os
import subprocess
import logging
import time
from threading import Timer

log = logging.getLogger(__name__)
WAIT_FOR_CONNECT = 5
ADB_TIMEOUT = 10


def connect(connect_url):
    log.debug("ADB start connecting %s" % connect_url)
    command = ["connect", connect_url]
    stdout, stderr = _exec_adb(command)
    start_time = time.time()
    while True:
        time.sleep(1)
        if device_is_ready(connect_url):
            log.debug("ADB device %s connected. \nStdout %s. \nStderr %s." % (connect_url, stdout, stderr))
            break
        elif time.time() - start_time > WAIT_FOR_CONNECT:
            raise OSError("ADB connect for device %s has been failed" % connect_url)


def device_is_ready(device_adb_name):
    ready = True
    state, stderr = get_state(device_adb_name)
    if state != b'device\n':
        ready = False
    return ready


def get_state(device_adb_name):
    command = "-s %s get-state" % device_adb_name
    stdout, stderr = _exec_adb(command.split())
    log.debug("ADB getting state of device %s. \nStdout %s. \nStderr %s." % (device_adb_name, stdout, stderr))
    return stdout, stderr


def shutdown_emulator(connect_url):
    emulator_shell = '-s %s shell' % connect_url
    shutdown_command = "am start -a android.intent.action.ACTION_REQUEST_SHUTDOWN; stop adbd"
    stdout, stderr = _exec_adb(emulator_shell.split() + [shutdown_command])
    log.debug("ADB shutdown emulator %s. \nStdout %s. \nStderr %s" % (connect_url, stdout, stderr))


def _exec_adb(params):
    command = ['adb'] + params
    log.debug("Executing adb command: %s" % command)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    timer = Timer(ADB_TIMEOUT, _kill_process, [process])
    try:
        timer.start()
        return process.communicate()
    finally:
        timer.cancel()


def _kill_process(process):
    log.error("Execution timeout expired. Kill %s process." % process.pid)
    process.kill()
