import argparse
import asyncio
import logging
from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('stf-record')


class SlowSquareClientProtocol(WebSocketClientProtocol):

    def onOpen(self):
        log.info('onOpen')

    def onMessage(self, payload, isBinary):
        log.info('onMessage')

    def onClose(self, wasClean, code, reason):
        log.info('onClose')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='')
    parser.add_argument(
        '-ws', required=True, help=''
    )
    parser.add_argument(
        '-dir', required=True, help=''
    )

    args = vars(parser.parse_args())

    host = args['ws'].split(':')[0]
    port = args['ws'].split(':')[1]
    directory = args['dir']

    log.debug('HOST:' + host)
    log.debug('PORT:' + port)
    factory = WebSocketClientFactory("ws://" + host + ":" + port)
    factory.protocol = SlowSquareClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, host, port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
