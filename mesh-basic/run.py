#! /usr/bin/env python3

import asyncio
import signal
from mesh.node import MeshNodeServer

async def main():

    # Make a series of servers
    server1 = MeshNodeServer(port=8701)
    server2 = MeshNodeServer(port=8702)
    server3 = MeshNodeServer(port=8703)

    # start them up
    server1.start()
    server2.start()
    server3.start()

    # Pause
    await asyncio.sleep(1)

    # connect some of them
    server1.connect_to(8702)
    await asyncio.sleep(1)
    server2.connect_to(8703)
    await asyncio.sleep(1)
    server3.connect_to(8701)

    # Setup the shutdown systems
    shutdown_trigger = asyncio.Event()
    is_shutdown_triggered = False
    async def exit_handler(signame):
        nonlocal is_shutdown_triggered
        if not is_shutdown_triggered:
            is_shutdown_triggered = True
            try:
                # await http_server.on_shutdown()
                pass
            except Exception as e:
                logging.error(f"Error on shutdown: {e}")
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
