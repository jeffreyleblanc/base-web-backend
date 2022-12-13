#! /usr/bin/env python3

# Copyright 2022 Jeffrey LeBlanc

import asyncio
import signal
import logging
import datetime
import secrets
import random
import tornado.websocket

'''
https://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketClientConnection
'''

async def main():
    # Set a custom name
    name = secrets.token_urlsafe(6)

    def on_message(message):
        print("  =>",message)

    url = 'ws://localhost:8898/api/ws/channel/'
    conn = await tornado.websocket.websocket_connect(url,on_message_callback=on_message)

    async def send_something():
        while True:
            msg = f"{name} {datetime.datetime.now()}"
            print("<=",msg)
            conn.write_message(msg)
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
                conn.close()
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
