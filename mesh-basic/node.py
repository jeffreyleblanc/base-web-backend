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


class MeshLeafClient:
    pass

class NodeConnectorClient:

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.conn = None

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

    def prepare(self):
        self.addr = self.request.get_query_argument("port",None)

    def open(self):
        self.kind = self.request.path
        self.wc_uuid = self.application.register_ws_client(self)

    def on_message(self, message):
        self.application.on_ws_client_msg(self,message)

    def on_close(self):
        self.application.unregister_ws_client(
            self.kind,
            self.wc_uuid,
            self.addr
        )
        print(f'WebSocket {self.wc_uuid} closed {self}')


class DemoActionHandler(tornado.web.RequestHandler):

    def post(self):
        pass

class NodeServer(tornado.web.Application):

    def __init__(self):

        _handlers = [
            (r"^/api/ws/client/?$",ClientWebSocketHandler),
            (r"^/api/ws/node/?$",NodeWebSocketHandler),
            (r"^/api/http/demo/action/?$",DemoActionHandler)
        ]

        self.local_clients = {}
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

    #-- Node Connector API ------------------------------------------------#

    def launch_client_connection(self, port):
        url = f"ws://localhost:{port}/api/ws/node/"
        connector = NodeConnectorClient(name,url)
        connector_task = asyncio.create_task(connector.connect(),name="client")
        self.node_connections[name] = {
            "conn": connector,
            "task": connector_task
        }

    #-- Websocket Tracking ------------------------------------------------#

    def register_ws_client(self, handler):
        wc_uuid = uuid.uuid4()
        if "client" in handler.path:
            self.local_clients[wc_uuid] = handler
        if "node" in handler.path:
            addr = handler.addr
            self.node_connections[addr] = handler
        return wc_uuid

    def on_ws_client_msg(self, handler, message):
        pass

    def unregister_ws_client(self, kind, wc_uuid, addr):
        logging.info('unregister %s wsclient', wc_uuid)
        if "client" in kind:
            self.local_clients.pop(wc_uuid,None)
        if "node" in kind:
            self.node_connections.pop(addr,None)

