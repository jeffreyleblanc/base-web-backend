#! /usr/bin/env python3

import asyncio
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

if __name__ == "__main__":
    asyncio.run(main())
