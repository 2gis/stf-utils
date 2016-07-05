import os
import subprocess
import logging
import time
from threading import Timer

log = logging.getLogger(__name__)
WAIT_FOR_CONNECT = 10
ADB_TIMEOUT = 10


def command_with_wait(command, connect_url):
    log.debug("ADB start command %s for %s" % (command, connect_url))
    stdout, stderr = _exec_adb(command)
    start_time = time.time()
    while True:
        time.sleep(1)
        if device_is_ready(connect_url):
            log.debug("ADB command %s for device %s was successful. "
                      "Stdout %s. Stderr %s." % (command, connect_url, stdout, stderr))
            break
        elif time.time() - start_time > WAIT_FOR_CONNECT:
            raise OSError("ADB command %s for device %s has been failed" % (command, connect_url))


def connect(connect_url):
    command = ["connect", connect_url]
    command_with_wait(command, connect_url)


def disconnect(connect_url):
    log.debug("ADB start disconnecting %s" % connect_url)
    command = ["disconnect", connect_url]
    stdout, stderr = _exec_adb(command)
    log.debug("ADB disconnect for device %s was done. "
              "Stdout %s. Stderr %s." % (connect_url, stdout, stderr))


def device_is_ready(device_adb_name):
    state, stderr = get_state(device_adb_name)
    if state != b'device\n':
        log.debug("Device %s isn't ready and has status is %s" % (device_adb_name, state))
        return False
    else:
        log.debug("Device %s is ready" % device_adb_name)
        return True


def get_state(device_adb_name):
    command = "-s %s get-state" % device_adb_name
    stdout, stderr = _exec_adb(command.split())
    log.debug("ADB getting state of device %s. Stdout %s. Stderr %s." % (device_adb_name, stdout, stderr))
    return stdout, stderr


def shutdown_emulator(connect_url):
    emulator_shell = '-s %s shell' % connect_url
    shutdown_command = "am start -a android.intent.action.ACTION_REQUEST_SHUTDOWN; stop adbd"
    stdout, stderr = _exec_adb(emulator_shell.split() + [shutdown_command])
    log.debug("ADB shutdown emulator %s. Stdout %s. Stderr %s" % (connect_url, stdout, stderr))


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
