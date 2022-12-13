#! /usr/bin/env python3

# Copyright 2022 Jeffrey LeBlanc

import asyncio
import signal
import logging
import datetime
import secrets
import random
from tornado.websocket import websocket_connect
from tornado.httpclient import HTTPRequest, HTTPClientError

'''
Notes:

https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketClientConnection
https://www.tornadoweb.org/en/stable/httpclient.html#tornado.httpclient.HTTPRequest
* Note request vs connect timeouts

'''

class SpoolClient:

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.conn = None

        # Connection management
        self.locally_closed = False
        self.conn_retrigger = None


    #-- Callback Based System -----------------------------------------------------------------#

    async def connect(self):
        if self.conn is not None:
            raise Exception("Already connected")

        remaining_connection_attempts = 5
        while True:
            try:
                # Make our connection
                request = HTTPRequest(url=self.url,request_timeout=5)
                self.conn = await websocket_connect(
                    url=request, on_message_callback=self.on_message )

                # Await to keep open: triggered by `on_close`
                self.locally_closed = False
                self.conn_retrigger = asyncio.Event()
                await self.conn_retrigger.wait()

                # Reengage reconnection attemps
                remaining_connection_attempts = 5

            except HTTPClientError as err:
                print("err!",err)
                self.conn = None
            except ConnectionRefusedError as err:
                print('refused!!!!',err)
                self.conn = None
            finally:
                remaining_connection_attempts -= 1
                if remaining_connection_attempts > 0:
                    print("waiting to try connecting again")
                    await asyncio.sleep(1)
                else:
                    raise Exception("Could not connect")
        print('done connect')

    def close(self):
        if self.conn is not None:
            self.locally_closed = True
            self.conn.close()
            self.conn = None

    def on_closed(self):
        if not self.locally_closed:
            print("on_closed: Try to reconnect")
            self.conn.close() # Needed?
            self.conn = None
            self.conn_retrigger.set()

    def on_message(self, message):
        if message is None:
            self.on_closed()
        else:
            print("  ==>",message)

    #-- Await System -----------------------------------------------------------------------------#

    """
    Alternatively here we could do the:

        conn = await websocket_connect(url)
        while True:
            msg = await conn.read_message()
            if msg is None: break
            # Do something with msg

    pattern which might make the reconnect logic clearer
    """

    #-- Write ------------------------------------------------------------------------------------#

    def write_something(self):
        if self.conn is None:
            return
        msg = f"{self.name} {datetime.datetime.now()}"
        print("<==",msg)
        self.conn.write_message(msg)


async def main():
    # Set a custom name
    name = secrets.token_urlsafe(6)
    url = 'ws://localhost:8898/api/ws/channel/'

    # Make our client and await it connecting
    client = SpoolClient(name,url)
    # await client.connect() # OR?
    asyncio.create_task(client.connect(),name="First conn")

    # Define a periodic message
    async def send_something():
        while True:
            client.write_something()
            sleep_for = 2+4*random.random()
            await asyncio.sleep(sleep_for)
    asyncio.create_task(send_something())

    # Setup the shutdown systems
    shutdown_trigger = asyncio.Event()
    is_shutdown_triggered = False
    async def exit_handler(signame):
        nonlocal is_shutdown_triggered
        if is_shutdown_triggered:
            logging.info("already shutting down")
        else:
            is_shutdown_triggered = True
            logging.info("shutdown start...")
            try:
                client.close()
            except Exception as e:
                logging.error(f"Error on shutdown: {e}")
            logging.info("...shutdown complete")
            shutdown_trigger.set()

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda signame=signame: asyncio.create_task(exit_handler(signame))
        )

    # Block on the shutdown trigger
    await shutdown_trigger.wait()

if __name__ == "__main__":
    asyncio.run(main())
