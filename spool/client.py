# Copyright 2022 Jeffrey LeBlanc

import asyncio
import signal
import logging
import datetime
import secrets
import tornado.websocket


def clbk(message):
    print('received', message)

async def main():

    name = secrets.token_urlsafe(6)

    url = 'ws://localhost:8898/api/ws/channel/'
    conn = await tornado.websocket.websocket_connect(url,on_message_callback=clbk)

    async def heartbeat2():
        while True:
            conn.write_message(f"{name} {datetime.datetime.now()}")
            await asyncio.sleep(1)

    asyncio.create_task(heartbeat2())

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
