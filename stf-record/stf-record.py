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
    address = None
    resolution = None

    def __init__(self):
        super().__init__()
        self.first_msg_timestamp = None
        self.previous_msg_timestamp = None
        self.current_msg_timestamp = None
        self._create_img_directory_if_not_exists()

    def _create_img_directory_if_not_exists(self):
        if not self.img_directory:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.img_directory = '{0}/images'.format(current_dir)
            log.debug(
                'Directory not set. '
                'Default directory is {0}'.format(self.img_directory)
            )
        if not os.path.exists(self.img_directory):
                os.mkdir(self.img_directory)

    def _construct_img_filename(self):
        img_filename = "{0}/{1}.jpg".format(
            self.img_directory,
            self.current_msg_timestamp - self.first_msg_timestamp
        )
        return img_filename

    @staticmethod
    def _write_image_file(img_filename, binary_data):
        with open(img_filename, 'bw+') as file:
            log.debug('Writing image data to file {0}'.format(file.name))
            file.write(binary_data)

    def _write_metadata(self, img_filename):
        metadata_filename = "{0}/input.txt".format(self.img_directory)
        m_file = open(metadata_filename, 'a')
        log.debug('Appending image metadata to file {0}'.format(m_file.name))
        if self.previous_msg_timestamp is not None:
            duration = self.current_msg_timestamp - self.previous_msg_timestamp
            m_file.write("duration {0}\n".format(duration))
        m_file.write("file '{0}'\n".format(img_filename))
        m_file.close()

    def save_data_and_metadata(self, binary_data):
        img_filename = self._construct_img_filename()
        self._write_image_file(img_filename, binary_data)
        self._write_metadata(img_filename)

    def onOpen(self):
        log.info('Starting recieve binary data')
        if self.resolution:
            self.sendMessage(self.resolution.encode('ascii'))
        self.sendMessage('on'.encode('ascii'))

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.current_msg_timestamp = time.time()
            if self.previous_msg_timestamp is None:
                self.first_msg_timestamp = self.current_msg_timestamp
            self.save_data_and_metadata(payload)
            self.previous_msg_timestamp = self.current_msg_timestamp

    def onClose(self, wasClean, code, reason):
        log.info('Disconnecting {0} ...'.format(address))
        self.sendMessage('off'.encode('ascii'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Utility for saving screenshots '
                    'from devices with openstf minicap'
    )
    parser.add_argument(
        '-ws', required=True, help='WebSocket URL'
    )
    parser.add_argument(
        '-dir', help='Directory for images'
    )
    parser.add_argument(
        '-resolution', help='Resolution of images'
    )
    parser.add_argument(
        '-log-level', help='Log level'
    )

    args = vars(parser.parse_args())

    if args['log_level']:
        log.info('Changed log level to {0}'.format(args['log_level'].upper()))
        log.setLevel(args['log_level'].upper())

    address = args['ws']
    if args['ws'].find('ws://') >= 0:
        address = address.split('ws://')[1]

    directory = args['dir']
    resolution = args['resolution']

    log.info('Connecting to {0} ...'.format(address))

    factory = WebSocketClientFactory("ws://{0}".format(address))
    factory.protocol = STFRecordProtocol
    factory.protocol.img_directory = directory
    factory.protocol.address = address
    factory.protocol.resolution = resolution

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(
        factory, address.split(':')[0], address.split(':')[1]
    )
    loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.info('Disconnecting {0} ...'.format(address))
    loop.close()
