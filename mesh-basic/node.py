# Copyright 2022 Jeffrey LeBlanc

# Python
import asyncio
import signal
import logging
import datetime
import secrets
import uuid
# Tornado
import tornado.web
from tornado.websocket import websocket_connect
from tornado.httpclient import HTTPRequest, HTTPClientError


#-- Leaf Connection Handlers ----------------------------------------#

class MeshLeafConnectionHandler(tornado.websocket.WebSocketHandler):

    def prepare(self):
        pass

    def open(self):
        self.wc_uuid = self.application.register_leaf_client(self)

    def on_message(self, message):
        self.application.on_leaf_client_msg(self,message)

    def on_close(self):
        self.application.unregister_leaf_client(self.wc_uuid)
        print(f'WebSocket Leaf {self.wc_uuid} closed {self}')


#-- Node Connection Handlers ----------------------------------------#

class MeshNodeConnectionClient:

    def __init__(self, master, name, url):
        self.master = master
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
        self.master.on_ws_client_msg(self.name,msg)

    def write_message(self, msg):
        if self.conn is None: return
        self.conn.write_message(msg)


class MeshNodeConnectionHandler(tornado.websocket.WebSocketHandler):

    def prepare(self):
        self.addr = self.request.get_query_argument("port",None)

    def open(self):
        self.application.register_node_client(self,self.addr)

    def on_message(self, message):
        self.application.on_node_client_msg(self,message)

    def on_close(self):
        self.application.unregister_node_client(self.addr)
        print(f'Node Client {self.addr} closed {self}')

#-- Control Plane Handlers ----------------------------------------#

class ControlActionHandler(tornado.web.RequestHandler):

    def post(self):
        pass


#-- Mesh Node Server ----------------------------------------#

class MeshNodeServer(tornado.web.Application):

    def __init__(self, port):
        # Attributes
        self.port = port

        # Connection tracking
        self.leaf_clients_by_uuid = {}
        self.node_connections_by_addr = {
            # "fqdn1": NodeClient,
            # "fqdn2": NodeWebSocketHandler
        }

        # Handlers
        _handlers = [
            (r"^/api/ws/leaf/?$",MeshLeafConnectionHandler),
            (r"^/api/ws/node/?$",MeshNodeConnectionHandler),
            (r"^/api/http/control/action/?$",ControlActionHandler)
        ]

        super().__init__(_handlers)

    def start(self):
        self.listen(8888)

    async def on_shutdown(self):
        for handler in self.ws_clients.values():
            handler.close()

    #-- Leaf Tracking ------------------------------------------------#

    def register_leaf_client(self, handler):
        wc_uuid = uuid.uuid4()
        self.leaf_clients_by_uuid[wc_uuid] = handler
        return wc_uuid

    def on_leaf_client_msg(self, sender, message):
        sender.write_message(f"ECHO: {message}")
        for wc in self.leaf_clients_by_uuid.values():
            if wc == sender: continue
            wc.write_message(message)
        for cn in self.node_connections_by_addr.values():
            if isinstance(cn,NodeConnectorClient):
                cn.write_message(message)
            if isinstance(cn,NodeWebSocketHandler):
                cn.write_message(message)

    def unregister_leaf_client(self, wc_uuid):
        logging.info('unregister %s wsclient', wc_uuid)
        self.leaf_clients_by_uuid.pop(wc_uuid,None)

    #-- Node Connector API ------------------------------------------------#

    def launch_node_client_connection(self, port):
        url = f"ws://localhost:{port}/api/ws/node/"
        connector = MeshNodeConnectionClient(name,url)
        connector_task = asyncio.create_task(connector.connect(),name="client")
        self.node_connections_by_addr[name] = {
            "conn": connector,
            "task": connector_task
        }
    #-- Node Client (Handler) Tracking ------------------------------------------------#

    def register_node_client(self, addr, handler):
        self.node_connections_by_addr[addr] = handler

    def on_node_client_msg(self, sender, message):
        for wc in self.leaf_clients_by_uuid.values():
            wc.write_message(message)

    def unregister_node_client(self, addr):
        logging.info('unregister %s wsclient', addr)
        self.node_connections_by_addr.pop(addr,None)

