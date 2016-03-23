import os
import subprocess


def connect(connect_url):
    command = ["connect", connect_url]
    _exec_adb(command)


def shutdown_emulator(connect_url):
    command = ("-s %s shell am start -a android.intent.action.ACTION_REQUEST_SHUTDOWN" % connect_url).split()
    _exec_adb(command).wait()


def _exec_adb(params):
    command = ['adb'] + params
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
