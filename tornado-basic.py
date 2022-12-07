# Copyright Jeffrey LeBlanc, 2022. MIT License.

import asyncio
import datetime
import signal
import logging
import tornado.web

'''
Basic server setup for Python 3.10+ and Tornado 6.2+.
Includes graceful shutdown and periodic methods.

See <https://www.tornadoweb.org/en/stable/guide/structure.html>
'''

async def heartbeat1():
    while True:
        print(f"A {datetime.datetime.now()}")
        await asyncio.sleep(4)

async def heartbeat2():
    while True:
        print(f"B {datetime.datetime.now()}")
        await asyncio.sleep(10)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        now = datetime.datetime.now()
        self.write(f"Hello world at {now}\n")

class MyApp(tornado.web.Application):

    def __init__(self):
        self._handlers = []
        self._settings = {}
        self.initialize()
        super().__init__(self._handlers,**self._settings)

    def initialize(self):
        # Handlers
        self._handlers += [
            (r"/", MainHandler)
        ]

        # Settings
        self._settings = dict(
            debug= True
        )

        # Example value and heartbeat
        self.heartbeat_count = 0
        self.heartbeat = asyncio.create_task(self._call_heartbeat())

    async def _call_heartbeat(self):
        while True:
            logging.info(f"heartbeat: {self.heartbeat_count}")
            self.heartbeat_count += 1
            await asyncio.sleep(1)

    async def on_shutdown(self):
        logging.info('app::on_shutdown >')
        await asyncio.sleep(0.5)
        self.heartbeat.cancel()
        logging.info('< app::on_shutdown')


async def main():

    # Setup logging
    logging.basicConfig(level=logging.INFO,format='%(message)s',)

    # Setup the server
    http_server = MyApp()
    http_server.listen(8888)

    # Start other repeating tasks
    heartbeat_tasks = set()
    hb = asyncio.create_task(heartbeat1())
    heartbeat_tasks.add(hb)
    hb = asyncio.create_task(heartbeat2())
    heartbeat_tasks.add(hb)

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
                await http_server.on_shutdown()
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

