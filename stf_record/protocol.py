import time
import logging
from autobahn.asyncio.websocket import WebSocketClientProtocol

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

    def _construct_img_filename(self):
        img_filename = "{0}.jpg".format(
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
        self._write_image_file("{0}/{1}".format(self.img_directory, img_filename), binary_data)
        self._write_metadata(img_filename)

    def onOpen(self):
        log.info('Starting receive binary data')
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
        log.info('Disconnecting {0} ...'.format(self.address))
        self.sendMessage('off'.encode('ascii'))
