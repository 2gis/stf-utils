import os
import subprocess


def connect(connect_url):
    command = ["connect", connect_url]
    _exec_adb(command)


def shutdown_emulator(connect_url):
    emulator_shell = '-s %s shell' % connect_url
    shutdown_command = "am start -a android.intent.action.ACTION_REQUEST_SHUTDOWN; stop adbd"
    _exec_adb(emulator_shell.split() + [shutdown_command]).wait()


def _exec_adb(params):
    command = ['adb'] + params
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
