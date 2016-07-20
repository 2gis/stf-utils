import os
import subprocess
import logging
import time
from threading import Timer
from common.exceptions import ADBException

log = logging.getLogger(__name__)
WAIT_FOR_CONNECT = 5
ADB_TIMEOUT = 10


def connect(connect_url):
    log.debug("Trying to establish ADB connection with %s" % connect_url)
    command = ["connect", connect_url]
    stdout, stderr = _exec_adb(command)
    start_time = time.time()
    while True:
        time.sleep(1)
        if device_is_ready(connect_url):
            log.debug("ADB connection with %s successfully established. "
                      "Stdout %s. Stderr %s." % (connect_url, stdout, stderr))
            break
        elif time.time() - start_time > WAIT_FOR_CONNECT:
            raise ADBException("Failed to establish ADB connection with %s. "
                               "Stdout %s. Stderr %s." % (connect_url, stdout, stderr))


def disconnect(connect_url):
    log.debug("Closing ADB connection with %s" % connect_url)
    command = ["disconnect", connect_url]
    stdout, stderr = _exec_adb(command)
    log.debug("ADB disconnect for %s executed. "
              "Stdout %s. Stderr %s." % (connect_url, stdout, stderr))


def device_is_ready(device_adb_name):
    state, stderr = get_state(device_adb_name)
    if state != b'device\n':
        log.debug("Device %s isn't ready and his status is %s" % (device_adb_name, state))
        return False
    else:
        log.debug("Device %s is ready" % device_adb_name)
        return True


def get_state(device_adb_name):
    command = "-s %s get-state" % device_adb_name
    stdout, stderr = _exec_adb(command.split())
    log.debug("ADB getting state of device %s. Stdout %s. Stderr %s." % (device_adb_name, stdout, stderr))
    return stdout, stderr


def echo_ping(device_adb_name):
    command = "-s %s shell" % device_adb_name
    shell_command = "echo 'ping'"
    stdout, stderr = _exec_adb(command.split() + [shell_command])
    log.debug("Echo 'ping' by ADB for device %s. Stdout %s. Stderr %s." % (device_adb_name,
                                                                           str(stdout).replace("\n", ""),
                                                                           str(stderr).replace("\n", "")))
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
