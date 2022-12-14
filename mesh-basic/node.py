# Copyright 2022 Jeffrey LeBlanc

import asyncio
import signal
import logging
import datetime
import secrets
import random
import uuid
from tornado.websocket import websocket_connect
from tornado.httpclient import HTTPRequest, HTTPClientError
import asyncio
import datetime
import signal
import logging
import tornado.web
import tornado.websocket
import random


'''
Node(A)
    server:
        websocket-/api/local/
            websocket-client <=>
        websocket-/api/node/
            websocket-node-client [A.wc1] <=> [B.nc1]
    node-clients:
        node-client [A.nc1] <=> [C.wc1]
Node(B)
    server:
        websocket-/api/local/
            websocket-client <=>
        websocket-/api/node/
            websocket-node-client [B.wc1] <=> [C.nc1]
    node-clients:
        node-client [B.nc1 <=> [A.wc1]
Node(C)
    server:
        websocket-/api/local/
            websocket-client <=>
        websocket-/api/node/
            websocket-node-client [C.wc1] <=> [A.nc1]
    node-clients:
        node-client [C.nc1] <=> [B.wc1]
'''


class NodeClient:

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.conn = None

    #-- Await System -----------------------------------------------------------------------------#

    async def start(self):
        while True:
            try:
                request = HTTPRequest(url=self.url,request_timeout=5)
                print("connected")
                while True:
                    msg = await self.conn.read_message()
                    if msg is None: break
                    self.on_message(msg)
            except HTTPClientError as err:
                self.conn = None
            except ConnectionRefusedError as err:
                self.conn = None
            finally:
                self.conn = None

            await asyncio.sleep(1)

    def on_message(self, msg):
        self.master.on_message(self.name,msg)

    def send_msg(self, msg):
        if self.conn is None: return
        self.conn.write_message(msg)

#-- Server ------------------------------------------------------------------#

class NodeWebSocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        self.kind = self.request.path
        self.wc_uuid = self.application.register_ws_client(self)

    def on_message(self, message):
        self.application.on_ws_client_msg(self,message)

    def on_close(self):
        self.application.unregister_ws_client(self.wc_uuid)
        print(f'WebSocket {self.wc_uuid} closed {self}')


class DemoActionHandler(tornado.web.RequestHandler):

    def post(self):
        pass

class NodeServer(tornado.web.Application):

    def __init__(self):
        # Websocket tracking
        self.ws_clients = {}

        _handlers = [
            (r"^/api/ws/client/?$",ClientWebSocketHandler),
            (r"^/api/ws/node/?$",NodeWebSocketHandler),
            (r"^/api/http/demo/action/?$",DemoActionHandler)
        ]

        self.node_connections = {
            # "fqdn1": NodeClient,
            # "fqdn2": NodeWebSocketHandler
        }

        super().__init__(_handlers)

    async def on_shutdown(self):
        for handler in self.ws_clients.values():
            handler.close()

    def announce(self, sender, message):
        sender.write_message(f"ECHO: {message}")
        for wc in self.ws_clients.values():
            if wc == sender:
                continue
            wc.write_message(message)

    async def eject_cycle(self):
        while True:
            if len(self.ws_clients) > 0 and random.random()>0.75:
                pass

    #-- Websocket Tracking ------------------------------------------------#

    def register_ws_client(self, handler):
        wc_uuid = uuid.uuid4()
        self.ws_clients[wc_uuid] = handler
        logging.info('register %s wsclient', wc_uuid)
        return wc_uuid

    def on_ws_client_msg(self, handler, message):
        pass

    def unregister_ws_client(self, wc_uuid):
        logging.info('unregister %s wsclient', wc_uuid)
        self.ws_clients.pop(wc_uuid)

    def launch_client_connection(self, name):
        client = NodeClient(name,url)
        client_task = asyncio.create_task(client.connect(),name="client")
        self._client_registry[name] = tuple(client,client_task)


