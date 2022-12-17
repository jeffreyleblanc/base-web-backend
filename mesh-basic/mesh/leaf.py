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


class MeshLeafClient:

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.conn = None

    async def start(self):
        while True:
            try:
                request = HTTPRequest(url=self.url,request_timeout=5)
                self.conn = await websocket_connect(url=request)
                print(f"leaf {self.name} connected")
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
        print(f"leaf[{self.name}] recv:",msg)

    def send_msg(self, msg):
        if self.conn is None: return
        print(f"leaf[{self.name}] send:",msg)
        self.conn.write_message(msg)

