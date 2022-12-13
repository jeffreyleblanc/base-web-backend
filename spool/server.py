#! /usr/bin/env python3

# Copyright Jeffrey LeBlanc, 2022. MIT License.

import asyncio
import datetime
import signal
import logging
import tornado.web
import tornado.websocket

class ChannelWebSocket(tornado.websocket.WebSocketHandler):

    def open(self):
        self.idx = self.application.register_ws_client(self)
        print(f'WebSocket {self.idx} on_open')
        self.write_message("HELLO FROM THE SERVER!")

    def on_message(self, message):
        self.application.announce(self,message)

    def on_close(self):
        self.application.unregister_ws_client(self.idx)
        print(f'WebSocket {self.idx} closed {self}')


class MyApp(tornado.web.Application):

    def __init__(self):
        # Websocket tracking
        self.ws_client_idx = -1
        self.ws_clients = {}

        _handlers = [
            (r"^/api/ws/channel/?$",ChannelWebSocket)
        ]
        _settings = {}

        super().__init__(_handlers,**_settings)

    async def on_shutdown(self):
        logging.info('app::on_shutdown >')
        for handler in self.ws_clients.values():
            handler.close()
        logging.info('< app::on_shutdown')

    def announce(self, sender, message):
        sender.write_message(f"ECHO: {message}")
        for wc in self.ws_clients.values():
            if wc == sender:
                continue
            wc.write_message(message)

    #-- Websocket Tracking ------------------------------------------------#

    def new_ws_client_key(self):
        ''' Could update to be anything '''
        self.ws_client_idx += 1
        return self.ws_client_idx

    def register_ws_client(self, handler):
        idx = self.new_ws_client_key()
        self.ws_clients[idx] = handler
        logging.info('register %s wsclient', idx)
        return idx

    def unregister_ws_client(self, idx):
        logging.info('unregister %s wsclient', idx)
        self.ws_clients.pop(idx)



async def main():

    # Setup logging
    logging.basicConfig(level=logging.INFO,format='%(message)s',)

    # Setup the server
    http_server = MyApp()
    http_server.listen(8898)

    # Setup the shutdown systems
    shutdown_trigger = asyncio.Event()
    is_shutdown_triggered = False
    async def exit_handler(signame):
        nonlocal is_shutdown_triggered
        if not is_shutdown_triggered:
            is_shutdown_triggered = True
            try:
                await http_server.on_shutdown()
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

