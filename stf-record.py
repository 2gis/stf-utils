import os
import time
import argparse
import asyncio
import logging
from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('stf-record')


class STFRecordProtocol(WebSocketClientProtocol):
    img_directory = None
    host = None
    port = None

    def __init__(self):
        super().__init__()
        self.previous_msg_timestamp = None
        self.first_msg_timestamp = None
        if not self.img_directory:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.img_directory = '{0}/images'.format(current_dir)
            if not os.path.exists(self.img_directory):
                os.mkdir(self.img_directory)
            log.debug('Directory not set. Default directory is {0}'.format(self.img_directory))

    def save_data_and_metadata(self, binary_data):
        if self.previous_msg_timestamp is None:
            self.first_msg_timestamp = time.time()
        current_msg_timestamp = self.first_msg_timestamp
        img_file = "{0}/{1}.jpg".format(
            self.img_directory,
            current_msg_timestamp - self.first_msg_timestamp
        )
        with open(img_file, 'bw+') as file:
            log.debug('Writing image data to file {0}'.format(file.name))
            file.write(binary_data)
        metadata_file = "{0}/input.txt".format(self.img_directory)
        m_file = open(metadata_file, 'w')
        log.debug('Appending image metadata to file {0}'.format(m_file.name))
        if self.previous_msg_timestamp is not None:
            duration = current_msg_timestamp - self.previous_msg_timestamp
            m_file.write("duration {0}".format(duration))
        m_file.write("file '{0}'".format(img_file))
        m_file.close()

    def onOpen(self):
        log.info('onOpen')
        self.sendMessage(b'1920x1080/0', isBinary=True)
        self.sendMessage(b'on', isBinary=True)

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.save_data_and_metadata(payload)

    def onClose(self, wasClean, code, reason):
        log.info('Disconnecting {0}:{1} ...'.format(host, port))
        self.sendMessage(b'off', isBinary=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='')
    parser.add_argument(
        '-ws', required=True, help='WebSocket URL'
    )
    parser.add_argument(
        '-dir', help='Directory for images'
    )
    parser.add_argument(
        '-log-level', help='Log level'
    )

    args = vars(parser.parse_args())

    if args['log_level']:
        log.info('Changed log level to {0}'.format(args['log_level'].upper()))
        log.setLevel(args['log_level'].upper())

    host = args['ws'].split(':')[0]
    port = args['ws'].split(':')[1]
    directory = args['dir']

    log.info('Connecting to {0}:{1} ...'.format(host, port))

    factory = WebSocketClientFactory("ws://{0}:{1}".format(host, port))
    factory.protocol = STFRecordProtocol
    factory.protocol.img_directory = directory
    factory.protocol.host = host
    factory.protocol.port = port

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, host, port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
