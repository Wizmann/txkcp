#coding=utf-8

import ikcp
import logging
import time
from twisted.internet import protocol, reactor, defer

def to_millisec(sec):
    return sec / 1000.

def timestamp():
    return int(time.time() * 1000)

class SocketAdapter(object):
    def __init__(self, peer, addr):
        self.peer = peer
        self.addr = addr

    def send(self, data):
        self.peer.transport.write(data, self.addr)

class Protocol(protocol.DatagramProtocol):
    def __init__(self, addr, conv, factory=None, wndsize=1024, mode=ikcp.DEFAULT_MODE):
        if factory:
            self.socket = SocketAdapter(factory, addr)
        else:
            self.socket = SocketAdapter(self, addr)

        self.addr = addr
        self.conv = conv
        self.kcp_mode = mode
        self.factory = factory
        self.tick = 0
        self.pre_timestamp = timestamp()
        self.kcp = ikcp.IKcp(self.socket, conv, mode)
        self.kcp.wndsize(wndsize, wndsize)

        self.update()

    def update(self):
        try:
            self.tick += timestamp() - self.pre_timestamp
            self.pre_timestamp = timestamp()

            next = self.kcp.check(self.tick)

            if next <= self.tick or self.kcp.next_update_time == 0:
                self.kcp.update(self.tick)
                bufsize = max(1500, self.kcp.peeksize)
                data = self.kcp.recv(bufsize)
                if data:
                    self.dataReceived(data)

            delta = max(0, next - self.tick)
            reactor.callLater(to_millisec(delta), self.update)
        except Exception, e:
            logging.error("error on kcp tick: %s" % e)
            reactor.callLater(to_millisec(30), self.update)

    def send(self, data):
        self.kcp.send(data)

    def datagramReceived(self, data, addr):
        self.kcp.input(data)

    def dataReceived(self, data):
        pass

    def loseConnection(self):
        if self.factory:
            self.factory.connectionLost(self)

class ProtocolFactory(protocol.DatagramProtocol):
    protocol = None
    wndsize = 1024
    mode=ikcp.DEFAULT_MODE

    def __init__(self):
        self.d = {}

    def datagramReceived(self, data, addr):
        conv = ikcp.IKcp.get_conv(data)
        conn_id = (addr, conv)
        if conn_id not in self.d:
            self.d[conn_id] = self.protocol(addr, conv, self, self.wndsize, self.mode)
            d = defer.Deferred()
            d.addCallback(lambda _:
                self.d[conn_id].datagramReceived(data, addr)
            )
            self.d[conn_id].startProtocol(d)

        else:
            self.d[conn_id].datagramReceived(data, addr)

    def connectionLost(self, protocol):
        conn_id = (protocol.addr, protocol.conv)
        logging.debug("protocol connection lost: %s" % str(conn_id))
        del self.d[conn_id]
