#! /usr/bin/env python3

# Copyright 2022 Jeffrey LeBlanc

# Python
import secrets
import os
from pathlib import Path
import asyncio
import signal
import logging
import json
# Tornado
import tornado.web
import tornado.websocket
import tornado.autoreload
# Local
from system.basehandlers import BaseHandler, BaseWebsocketHandler
from system.auth_server import AuthServerMixin
from system.auth_handlers import get_account_handlers, authenticated


#-- Application Handlers ------------------------------------------------------#

class MainHandler(BaseHandler):
    @authenticated(action='login')
    def get(self):
        self.render("index.html",user=self.current_user,rh=secrets.token_urlsafe(6))


class ExampleGetHandler(BaseHandler):
    @authenticated()
    def get(self):
        url = self.get_query_argument('url','')
        title = self.get_query_argument('title','')
        selection = self.get_query_argument('selection','')
        self.write_json({
            "success": True,
            "url": url,
            "title": title,
            "selection": selection
        })

class ExamplePostHandler(BaseHandler):
    @authenticated()
    def post(self):
        authorization = self.request.headers.get("Authorization",None)
        print(f"auth:",authorization)
        data = tornado.escape.json_decode(self.request.body)
        print('data:',data)
        self.write_json({'success':True})


class ExampleUploadFile(BaseHandler):
    @authenticated()
    def post(self):
        # see https://www.tornadoweb.org/en/stable/httputil.html#tornado.httputil.HTTPFile
        fileinfo = self.request.files['myFile'][0]
        filename = fileinfo['filename']
        filedata = fileinfo['body']

        with open(filename,'w+b') as f:
            f.write(filedata)

        self.write_json({'success':True})


class EchoWebSocket(BaseWebsocketHandler):

    '''
    The sequence of calls on a new connection is:
    1. prepare
    2. get
    3. select_subprotocol
    4. open
    '''

    @authenticated()
    def prepare(self):
        logging.info("ws:prepare =>")
        self.idx = None
        print('current user:',self.current_user)
        ws_protocol = self.request.headers.get("Sec-Websocket-Protocol",None)
        print('ws_protocol:',ws_protocol)
        logging.info("<= ws:prepare")

    def get(self, *args, **kwargs):
        logging.info("ws:get =>")
        logging.info("<= ws:get")
        return super().get(*args,**kwargs)

    def select_subprotocol(self, proto_list):
        logging.info("ws:select_subprotocol =>")
        if len(proto_list) == 1:
            return proto_list[0]
        return None

    def open(self):
        logging.info("ws:open =>")
        self.idx = self.application.register_ws_client(self)
        print(f'WebSocket {self.idx} on_open')
        self.write_message("HELLO FROM THE SERVER!")
        logging.info("<= ws:open")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        self.application.unregister_ws_client(self.idx)
        print(f'WebSocket {self.idx} closed {self}')


#-- Application ---------------------------------------------------------------#

class MyApp(tornado.web.Application, AuthServerMixin):

    def __init__(self, autoreload=False):
        self._handlers = []
        self._settings = {}
        self.initialize(autoreload=autoreload)

        super().__init__(self._handlers,**self._settings)

    def initialize(self, autoreload=False):

        # Websocket tracking
        self.ws_client_idx = -1
        self.ws_clients = {}

        # Handlers
        self._handlers += [
            (r"^/$", MainHandler),
            (r"^/api/example/get/?$",ExampleGetHandler),
            (r"^/api/example/post/?$",ExamplePostHandler),
            (r"^/api/example/upload-file/?$",ExampleUploadFile),
            (r"^/api/example/ws/echo/?$",EchoWebSocket)
        ]
        self._handlers += get_account_handlers()

        # Get our paths
        _here = Path(__file__).parent
        static_dir = _here/'webresources/static'
        template_dir = _here/'webresources/templates'

        # Settings
        self._settings = dict(
            cookie_secret= secrets.token_urlsafe(24),
            login_url= "/login",
            static_path= static_dir,
            template_path= template_dir,
            autoreload= autoreload,
            gzip= True,
            xsrf_cookies= True
        )

        if autoreload:
            logging.info('Running autoreload on python source and template directory')
            for directory, _, files in os.walk(template_dir):
                [tornado.autoreload.watch(f'{directory}/{f}') for f in files if not f.startswith('.')]

        # Example value and heartbeat
        self.heartbeat_count = 0
        self.heartbeat = asyncio.create_task(self._call_heartbeat())

        # Setup Auth
        self.setup_auth()


    async def _call_heartbeat(self):
        while True:
            logging.info(f"heartbeat: {self.heartbeat_count}")
            self.heartbeat_count += 1
            await asyncio.sleep(10)

    async def on_shutdown(self):
        logging.info('app::on_shutdown >')
        self.heartbeat.cancel()
        for handler in self.ws_clients.values():
            handler.close()
        logging.info('< app::on_shutdown')

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


#-- Main -------------------------------------------------------------------------#

async def main():
    # Command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--autoreload', action='store_true', help='Autoreload server code')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)
    # Suppress 200 and 30* HTTP logging
    access_log = logging.getLogger("tornado.access")
    access_log.setLevel(logging.WARNING)

    # Setup the server
    tornado_app = MyApp(autoreload=args.autoreload)
    tornado_app.listen(8888)
    logging.info('running at localhost:8888')

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
                await tornado_app.on_shutdown()
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


if __name__ == '__main__':
    asyncio.run(main())