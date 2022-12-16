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
        self.write_message("welcome")

    def on_message(self, message):
        print("MeshLeafConnectionHandler:on_message",message)
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
                self.conn = await websocket_connect(url=request)
                print(self.name,"connected to",self.url)
                while True:
                    msg = await self.conn.read_message()
                    print("GOT A MESSAGE!!!!!",msg)
                    if msg is None:
                        break
                    print("DO SOMETHING WITH IT:::")
                    print(self.on_incoming_message)
                    self.master.on_ws_client_msg(self.name,msg)
                    # Needs to inject into a queue
                    print('?????')
                    ### self.on_incoming_message(msg)
                    print("WTF")
            except HTTPClientError as err:
                self.conn = None
            except ConnectionRefusedError as err:
                self.conn = None
            finally:
                self.conn = None

            print("EXITED")

            await asyncio.sleep(1)
        print("not connected anymore")

    def on_incoming_message(self, msg):
        print("MeshNodeConnectionClient:on_message".msg)
        self.master.on_ws_client_msg(self.name,msg)

    def write_message(self, msg):
        if self.conn is None: return
        self.conn.write_message(msg)


class MeshNodeConnectionHandler(tornado.websocket.WebSocketHandler):

    def prepare(self):
        print("Prepare!!!")
        self.addr = self.get_argument("from_addr",None)
        print("From:",self.addr)

    def open(self):
        self.application.register_node_client(self.addr,self)

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
        self.listen(self.port)

    async def on_shutdown(self):
        for handler in self.ws_clients.values():
            handler.close()

    def debug(self, *args):
        print(f"{self.port} =>",*args)

    #-- Status ------------------------------------------------#

    def dump_status(self):
        status = dict(self=str(self.port), leaf=[], node={})
        for leaf in self.leaf_clients_by_uuid.values():
            status["leaf"].append("client")
        for addr,conn in self.node_connections_by_addr.items():
            status["node"][str(addr)] = str(type(conn))
        return status

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
            print("SEND OUT TO:",cn)
            if isinstance(cn,dict): # MeshNodeConnectionHandler):
                print("SEND A")
                cn["conn"].write_message(message)
            if isinstance(cn,MeshNodeConnectionHandler):
                print("SEND B")
                cn.write_message(message)

    def unregister_leaf_client(self, wc_uuid):
        logging.info('unregister %s wsclient', wc_uuid)
        self.leaf_clients_by_uuid.pop(wc_uuid,None)

    #-- Node Connector API ------------------------------------------------#

    def connect_to(self, port):
        self.debug("connecting to node:",port)
        name = f"node:{port}"
        if name in self.node_connections_by_addr:
            print(f"{self.port} already has {name}")
        else:
            url = f"ws://localhost:{port}/api/ws/node/?from_addr={self.port}"
            connector = MeshNodeConnectionClient(self,name,url)
            connector_task = asyncio.create_task(connector.start(),name="client")
            self.node_connections_by_addr[str(port)] = {
                "conn": connector,
                "task": connector_task
            }

    #-- Node Client (Handler) Tracking ------------------------------------------------#

    def register_node_client(self, addr, handler):
        self.node_connections_by_addr[addr] = handler
        self.debug("connected to node:",addr)

    def on_node_client_msg(self, sender, message):
        print("on_node_client_msg",sender,message)
        for wc in self.leaf_clients_by_uuid.values():
            wc.write_message(message)

    def on_ws_client_msg(self, sender, message):
        print("on_ws_client_msg",sender,message)
        for wc in self.leaf_clients_by_uuid.values():
            wc.write_message(message)
        print("====> exit!")

    def unregister_node_client(self, addr):
        logging.info('unregister %s wsclient', addr)
        self.node_connections_by_addr.pop(addr,None)

