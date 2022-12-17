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

    # Setup
    ports = [8701, 8702, 8703]
    servers = []
    clients = []

    ctx.H2("Make a series of servers")
    for port in ports:
        servers.append(MeshNodeServer("localhost",port=port))

    ctx.H2("start them up")
    for server in servers:
        server.start()

    ctx.H2("Pause")
    await ctx.async_sleep(1)
    dump_statuses(servers)

    ctx.H2("Make a client for each")
    for i,port in enumerate(ports):
        name = f"c{i}"
        url = f"ws://localhost:{port}/api/ws/leaf/"
        client = MeshLeafClient(name,url)
        asyncio.create_task(client.start(),name=name)
        clients.append(client)

    ctx.H2("Pause")
    await ctx.async_sleep(1)
    dump_statuses(servers)

    ctx.H2("connect some of them")
    servers[0].connect_to(8702)
    servers[1].connect_to(8703)
    servers[2].connect_to(8701)

    ctx.H2("Pause")
    await ctx.async_sleep(2)
    dump_statuses(servers)

    ctx.H2("Pause")
    await ctx.async_sleep(2)

    ctx.H2("client[0] Send a message")
    clients[0].send_msg("CLIENT[0] BROADCAST!")
    await ctx.async_sleep(2)

    ctx.H2("client[1] Send a second message")
    clients[1].send_msg("CLIENT[1] BROADCAST!")
    await ctx.async_sleep(5)

    ctx.H2("client2 Send a second message")
    clients[1].send_msg("CLIENT[1] BROADCAST AGAIN!")
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
