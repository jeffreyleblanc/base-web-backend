
import asyncio
from node import NodeClient, NodeServer


async def main():

    # Make a series of servers
    server1 = NodeServer(port=8701)
    server2 = NodeServer(port=8702)
    server3 = NodeServer(port=8703)

    # start them up
    asyncio.create_task(server1.start(),"8701")
    asyncio.create_task(server2.start(),"8702")
    asyncio.create_task(server3.start(),"8703")

    # connect some of them
    server1.connect_to(8702)
    server2.connect_to(8703)
    server3.connect_to(8701)

if __name__ == "__main__":
    asyncio.run(main())
