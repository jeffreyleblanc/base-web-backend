#! /usr/bin/env python3

# Copyright 2022 Jeffrey LeBlanc

import asyncio
import signal
import logging
import datetime
import secrets
import random
from tornado.websocket import websocket_connect

'''
https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketClientConnection
'''

class SpoolClient:

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.conn = None

    async def connect(self):
        if self.conn is not None:
            raise Exception("Already connected")
        self.conn = await websocket_connect(self.url,on_message_callback=self.on_message)

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def on_message(self, message):
        print("  ==>",message)

    def write_something(self):
        msg = f"{self.name} {datetime.datetime.now()}"
        print("<==",msg)
        self.conn.write_message(msg)


async def main():
    # Set a custom name
    name = secrets.token_urlsafe(6)
    url = 'ws://localhost:8898/api/ws/channel/'

    # Make our client and await it connecting
    client = SpoolClient(name,url)
    await client.connect()

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
