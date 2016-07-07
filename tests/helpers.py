import os
import json
import time


def get_response_from_file(filename):
    with open('%s/data/%s' % (os.path.dirname(os.path.abspath(__file__)), filename)) as f:
        all_devices = f.read()
        return json.loads(all_devices)


def wait_for(condition, timeout=5):
    start = time.time()
    while not condition() and time.time() - start < timeout:
        time.sleep(0.1)

    return condition()