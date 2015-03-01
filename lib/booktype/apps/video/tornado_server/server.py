# -*- coding: utf-8 -*-
import os
import logging

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.web import RequestHandler as _RequestHandler
from tornado.websocket import WebSocketHandler

import settings

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


# logger
logger = logging.getLogger('webrtc_server')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('webrtc_server.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s || %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

resolve = lambda *dirname: os.path.abspath(os.path.join(settings.ROOT_PATH, *dirname))

# TODO this is only for prototyping in future better to use dbm/nosql or smth similar
GLOBAL_NODES = {}


class RequestHandler(_RequestHandler):
    """
    Main request handler.
    """
    # TODO research and override some methods for pretty errors handle
    pass


# not using for now, django app render "call node"
# tornado using only for socket connection
class NodeHandler(RequestHandler):
    def get(self, inviter, invited):

        self.render('node.html',
                    inviter=inviter,
                    invited=invited)


class WebSocket(WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super(WebSocket, self).__init__(*args, **kwargs)
        self.current_node = None

    def open(self, inviter, invited):
        logger.info('WebSocket opening "{0}<-{1}" from %s'.format(inviter, invited), self.request.remote_ip)

        if inviter not in GLOBAL_NODES:
            GLOBAL_NODES[inviter] = Node(inviter, [self])
        else:
            GLOBAL_NODES[inviter].clients.append(self)

        self.current_node = GLOBAL_NODES[inviter]

        if len(self.current_node.clients) == 1:
            self.write_message('inviter')
        elif len(self.current_node.clients) > 2:
            self.write_message('magic_overload')
        else:
            self.write_message('invited')

        logger.info('WebSocket opened "{0}" from %s'.format(inviter), self.request.remote_ip)

    def on_message(self, message):
        logger.info('Received message from %s: %s', self.request.remote_ip, message)

        for client in self.current_node.clients:
            if client is self:
                continue
            client.write_message(message)

    def on_close(self):
        logger.info('WebSocket connection closed.')
        self.current_node.clients.remove(self)

    def check_origin(self, origin):
        parsed_origin = urlparse(origin)
        origin = parsed_origin.netloc
        origin = origin.lower()

        return origin in settings.ALLOWED_IP_ADDRESS_REQUEST


class Node(object):
    """
    Node model
    """
    def __init__(self, name, clients=[]):
        self.name = name
        self.clients = clients

    def __repr__(self):
        return "Node '{0}'".format(self.name)


class WebRTCApplication(Application):
    """
    Main tornado application.
    """
    pass


def main():
    app_settings = {'template_path': resolve('templates'),
                    'static_path': resolve('static'),
                    'debug': settings.DEBUG}

    application = WebRTCApplication([(r"/node/([^/]*)/([^/]*)", NodeHandler),
                                     (r"/wbsckt/([^/]*)/([^/]*)/", WebSocket)],
                                    **app_settings)

    application.listen(address=settings.HOST, port=settings.PORT)
    logger.info("Server started. Listen {host}:{port}.".format(host=settings.HOST,
                                                               port=settings.PORT))
    # run reactor
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
