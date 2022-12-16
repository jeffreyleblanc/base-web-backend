#! /usr/bin/env python3

import asyncio
import signal
import json
import logging
from mesh.node import MeshNodeServer
from mesh.leaf import MeshLeafClient
from testutils.context import TestContext


def dump_statuses(server_list):
    print("\n-- statuses----------------------------")
    for server in server_list:
        print(json.dumps(server.dump_status(),indent=4))
    print("------------------------------\n")

async def main():

    ctx = TestContext()

    # Setup logging
    logging.basicConfig(level=logging.INFO,format='%(message)s',)

    ctx.H2("Make a series of servers")
    server1 = MeshNodeServer(port=8701)
    server2 = MeshNodeServer(port=8702)
    server_list = [server1,server2]

    ctx.H2("start them up")
    server1.start()
    server2.start()

    ctx.H2("Pause")
    await ctx.async_sleep(1)
    dump_statuses(server_list)

    ctx.H2("Make a client for each")
    client1 = MeshLeafClient('c1',f"ws://localhost:{server1.port}/api/ws/leaf/")
    asyncio.create_task(client1.start(),name="c1")
    client2 = MeshLeafClient('c2',f"ws://localhost:{server2.port}/api/ws/leaf/")
    asyncio.create_task(client2.start(),name="c2")

    ctx.H2("Pause")
    await ctx.async_sleep(1)
    dump_statuses(server_list)

    ctx.H2("connect some of them")
    server1.connect_to(8702) # 1 : 2

    ctx.H2("Pause")
    await ctx.async_sleep(2)
    dump_statuses(server_list)

    ctx.H2("Pause")
    await ctx.async_sleep(2)
    print("client1 Send a message")
    client1.send_msg("CLIENT 1 BROADCAST!")
    await ctx.async_sleep(2)


    ctx.H2("client2 Send a second message")
    client2.send_msg("CLIENT 2 BROADCAST!")
    await ctx.async_sleep(5)

    ctx.H2("client2 Send a second message")
    client2.send_msg("CLIENT 2 BROADCAST AGAIN!")
    await ctx.async_sleep(5)

    ctx.H2("Finished Run")

    # Setup the shutdown systems
    shutdown_trigger = asyncio.Event()
    is_shutdown_triggered = False
    async def exit_handler(signame):
        nonlocal is_shutdown_triggered
        if not is_shutdown_triggered:
            is_shutdown_triggered = True
            try:
                for client in client_list:
                    pass
                for server in server_list:
                    await server.on_shutdown()
                pass
            except Exception as e:
                print(f"Error on shutdown: {e}")
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
