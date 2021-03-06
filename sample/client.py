#coding=utf-8

import os
import sys

sys.path.insert(0, os.path.abspath('src'))

import txkcp
import logging
from twisted.internet import protocol, reactor, defer

import config

class ClientOutgoing(txkcp.Protocol):
    def __init__(self, addr, peer):
        self.addr = addr
        self.peer = peer
        self.peer.outgoing = self

        txkcp.Protocol.__init__(self, self.addr, config.CONV_ID)

    def dataReceived(self, data):
        logging.info("kcp data received: %s" % data)

class LocalProxyProtocol(protocol.Protocol):
    def __init__(self):
        self.addr = (config.SERVER_ADDR, config.SERVER_PORT)
        reactor.listenUDP(config.CLIENT_OUTGOING_PORT, ClientOutgoing(self.addr, self))

    def dataReceived(self, data):
        self.outgoing.send(data)

class LocalProxyFactory(protocol.ServerFactory):
    protocol = LocalProxyProtocol

if __name__ == '__main__':
    reactor.listenTCP(config.CLIENT_PORT, LocalProxyFactory())
    reactor.run()
