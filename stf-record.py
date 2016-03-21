import os
import argparse
import asyncio
import logging
from datetime import datetime
from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('stf-record')


class STFRecordProtocol(WebSocketClientProtocol):
    directory = None
    host = None
    port = None

    def onOpen(self):
        log.info('onOpen')
        self.sendMessage(b'1920x1080/0', isBinary=True)
        self.sendMessage(b'on', isBinary=True)

    def onMessage(self, payload, isBinary):
        if isBinary:
            current_time = datetime.now()
            if not self.directory:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                os.mkdir('images')
                self.directory = current_dir + '/images/'
                log.debug('Directory not set. Default directory is %s' % self.directory)

            image_name = 'image_%s.png' % current_time.timestamp()
            image = open(self.directory + '/' + image_name, 'bw+')
            image.write(payload)
            log.debug('Saving image ' + image_name + ' to ' + self.directory)
            image.close()

    def onClose(self, wasClean, code, reason):
        log.info('Disconnecting %s:%s ...' % (host, port))
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
        log.info('Changed log level to %s' % args['log_level'].upper())
        log.setLevel(args['log_level'].upper())

    host = args['ws'].split(':')[0]
    port = args['ws'].split(':')[1]
    directory = args['dir']

    log.info('Connecting to %s:%s ...' % (host, port))

    factory = WebSocketClientFactory("ws://" + host + ":" + port)
    factory.protocol = STFRecordProtocol
    factory.protocol.directory = directory
    factory.protocol.host = host
    factory.protocol.port = port

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, host, port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
