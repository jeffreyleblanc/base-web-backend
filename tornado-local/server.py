#! /usr/bin/env python3

# Python
import secrets
import os
import asyncio
import signal
import logging
import json
import functools
import urllib.parse
from urllib.parse import urlencode
from pathlib import Path
# Tornado
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.autoreload
from tornado.ioloop import PeriodicCallback


class BaseHandler(tornado.web.RequestHandler):
    '''
    Add in method that can limit to local only
    '''
    def write_json(self, obj, indent=None):
        self.set_header("Content-Type", "application/json")
        s = json.dumps(obj,indent=indent)
        self.write(s)

class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")

class APIHandler(BaseHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print('DATA!',data)
        self.write_json({'status':'OK'})


class ExplorerWebserver(tornado.web.Application):

    def __init__(self, ioloop, autoreload=False):
        self.ioloop = ioloop
        self._handlers = []
        self._settings = {}
        self.initialize(autoreload=autoreload)

        super().__init__(self._handlers,**self._settings)

    def initialize(self, autoreload=False):

        if autoreload:
            logging.info('Running autoreload on python source and template directory')

        # Handlers
        self._handlers += [
            (r"/", MainHandler),
            (r"/api/v1/http/main/?", APIHandler)
        ]

        # Get our paths
        '''
        Use pathlib instead!!!
        '''
        _here = Path(os.path.dirname(__file__))
        static_dir = _here / 'webresources/static'
        template_dir = _here /'webresources/templates'

        # Settings
        self._settings = dict(
            static_path= static_dir,
            template_path= template_dir,
            autoreload= autoreload
        )

        if autoreload:
            for directory, _, files in os.walk(template_dir):
                [tornado.autoreload.watch(f'{directory}/{f}') for f in files if not f.startswith('.')]

    async def on_shutdown(self):
        pass

#-- Main -------------------------------------------------------------------------#

def main():
    # Command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8888, help='Port for the server')
    parser.add_argument('--autoreload', action='store_true', help='Autoreload server code')
    args = parser.parse_args()

    # Setup logging
    '''
    Set this level from a flag
    '''
    logging.basicConfig(level=logging.INFO)
    # Suppress 200 and 30* HTTP logging
    access_log = logging.getLogger("tornado.access")
    access_log.setLevel(logging.WARNING)

    # Get our ioloop
    ioloop = tornado.ioloop.IOLoop.current()

    # Setup the server
    tornado_app = ExplorerWebserver(ioloop,autoreload=args.autoreload)
    http_server = tornado_app.listen(args.port)
    logging.info(f'running at localhost:{args.port}')

    # Setup shutdown methods
    shutdown_triggered = False
    async def shutdown():
        nonlocal shutdown_triggered
        if shutdown_triggered:
            logging.info('duplicate shutdown call')
            return
        shutdown_triggered = True
        logging.info('shutdown begun')
        await tornado_app.on_shutdown()
        http_server.stop()
        await http_server.close_all_connections()
        await asyncio.sleep(0.25)
        tornado.ioloop.IOLoop.current().stop()
        logging.info('shutdown complete')

    def exit_handler(sig, frame):
        tornado.ioloop.IOLoop.instance().add_callback_from_signal(shutdown)

    signal.signal(signal.SIGTERM,exit_handler)
    signal.signal(signal.SIGINT,exit_handler)

    # Start the system
    ioloop.start()


if __name__ == '__main__':
    main()
