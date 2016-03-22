import os
import subprocess


def connect(connect_url):
    command = ["adb", "connect", connect_url]
    subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
