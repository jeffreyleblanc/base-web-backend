#! /usr/bin/env python3

# Python
import secrets
import os
from pathlib import Path
import asyncio
import signal
import logging
import json
import functools
import urllib.parse
from urllib.parse import urlencode
# Tools
import bcrypt
# Tornado
import tornado.web
import tornado.websocket
import tornado.autoreload


#-- Base Handlers --------------------------------------------------#

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def write_json(self, obj, indent=None):
        self.set_header("Content-Type", "application/json")
        s = json.dumps(obj,indent=indent)
        self.write(s)

class BaseWebsocketHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

#-- Account Handlers --------------------------------------------------#

def authenticated(action=403):
    '''
    This is very similar to the tornado base decorator:
    ( see https://www.tornadoweb.org/en/stable/_modules/tornado/web.html#authenticated )
    But this allows for finer grain control over what occurs with an outer wrapper.
    By default this raises 403, instead of redirection to login
    '''
    def _authenticated(method):

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                if action in (400,401,403,404):
                    raise tornado.web.HTTPError(action)
                if action == 'login' and self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urllib.parse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            assert self.request.uri is not None
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return None
                logging.warning('Improper action: %s',action)
                raise tornado.web.HTTPError(403)
            return method(self, *args, **kwargs)

        return wrapper
    return _authenticated

class SignupHandler(BaseHandler):

    def get(self):
        if self.current_user is not None:
            self.render('accounts/loggedin.html',user=self.current_user)
        else:
            error = self.get_query_argument('error', '')
            self.render('accounts/signup.html',error=error)

    async def post(self):
        invite = self.get_argument("invite",None)
        username = self.get_argument("username",None)
        password1 = self.get_argument("password1",None)
        password2 = self.get_argument("password2",None)

        resp = { 'success': False }
        if not self.application.has_invite(invite):
            self.set_status(40)
            resp['error'] = 'Invalid invite'
        elif username == '':
            self.set_status(400)
            resp['error'] = 'Empty username'
        elif self.application.has_username(username):
            self.set_status(403)
            resp['error'] = 'Already that user'
        elif password1 == '':
            self.set_status(400)
            resp['error'] = 'Empty password!'
        elif password1 != password2:
            self.set_status(400)
            resp['error'] = 'Passwords do not match'
        else:
            await self.application.create_user(username,password1)
            self.set_secure_cookie("user",username)
            self.application.remove_invite(invite)
            resp['success'] = True
            resp['next'] = '/welcome'

        self.write_json(resp)

class WelcomeHandler(BaseHandler):
    @authenticated(action='login')
    def get(self):
        self.render('accounts/welcome.html',user=self.current_user)


class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user is not None:
            self.render('accounts/loggedin.html',user=self.current_user)
        else:
            next_url = self.get_query_argument('next', '/')
            error = self.get_query_argument('error', '')
            self.render('accounts/login.html',next_url=next_url,error=error)

    async def post(self):
        username = self.get_argument("username",None)
        password = self.get_argument("password",None)
        success = await self.application._validate_user_creds(username,password)
        if not success:
            self.set_status(403)
            self.redirect(f"/login?next={self.get_argument('next', '/')}&error=Error")
        else:
            self.set_secure_cookie("user",username)
            self.redirect(self.get_argument('next', '/'))

class AccountHandler(BaseHandler):
    @authenticated(action='login')
    def get(self):
        self.render('accounts/account.html',user=self.current_user, error='')

class ChangePasswordHandler(BaseHandler):
    @authenticated()
    async def post(self):
        user = self.current_user
        password = self.get_argument("password",None)
        npassword1 = self.get_argument("npassword1",None)
        npassword2 = self.get_argument("npassword2",None)

        # Note that the checking order here could be different
        resp = { 'success': False }
        success = await self.application._validate_user_creds(user,password)
        if not success:
            self.set_status(403)
            resp['error'] = 'wrong_current_password'
            resp['message'] ='Incorrect current password'
        else:
            if npassword1 != npassword2:
                self.set_status(400)
                resp['error'] = 'new_passwords_no_match'
                resp['message'] ='New passwords do not match'
            else:
                await self.application._update_user_creds(user,npassword1)
                resp['success'] = True
                resp['redirect'] = '/welcome'

        self.write_json(resp)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.render('accounts/logout.html')

def get_account_handlers():
    return [
        (r"/login/?",LoginHandler),
        (r"/logout/?",LogoutHandler),
        (r"/account/?",AccountHandler),
        (r"/welcome/?",WelcomeHandler),
        (r"/api/account/changepw?",ChangePasswordHandler),
        (r"/signup/?",SignupHandler)
    ]

#-- Application Handlers ------------------------------------------------------#

class MainHandler(BaseHandler):
    @authenticated(action='login')
    def get(self):
        self.render("index.html",user=self.current_user)

class FakeMainHandler(BaseHandler):
    def get(self):
        user = None
        self.render("index.html",user=user)

class UploadHandler(BaseHandler):
    @authenticated()
    def get(self):
        url = self.get_query_argument('url','')
        title = self.get_query_argument('title','')
        selection = self.get_query_argument('selection','')
        self.write(f'uploaded: {url} {title} {selection}')

class POSTUploadHandler(BaseHandler):
    @authenticated()
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print('DATA!',data)
        self.write_json({'status':'OK'})

class EchoWebSocket(BaseWebsocketHandler):
    @authenticated()
    def prepare(self):
        print('ws prepare!!!!')
        self.idx = None
        print('user???',self.current_user)

    def get(self, *args, **kwargs):
        print('ws get!')
        print('user2???',self.current_user)
        return super().get(*args,**kwargs)

    def open(self):
        self.idx = self.application.register_ws_client(self)
        print(f'WebSocket {self.idx} on_open')

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        self.application.unregister_ws_client(self.idx)
        print(f'WebSocket {self.idx} closed {self}')

class UploadImage(BaseHandler):
    @authenticated()
    def post(self):
        # see https://www.tornadoweb.org/en/stable/httputil.html#tornado.httputil.HTTPFile
        fileinfo = self.request.files['myFile'][0]
        filename = fileinfo['filename']
        filedata = fileinfo['body']

        with open(filename,'w+b') as f:
            f.write(filedata)

        self.write_json({'success':True})

#-- Application ---------------------------------------------------------------#

def as_bytes(val):
    if isinstance(val,bytes): return val
    if isinstance(val,str): return val.encode('utf-8')
    raise TypeError()

def as_string(val):
    if isinstance(val,str): return val
    if isinstance(val,bytes): return val.decode('utf-8')
    raise TypeError()


class MyApp(tornado.web.Application):

    def __init__(self, autoreload=False):
        self._handlers = []
        self._settings = {}
        self.initialize(autoreload=autoreload)

        super().__init__(self._handlers,**self._settings)

    def initialize(self, autoreload=False):

        # Example simple user map, don't do in real life!
        self.user_map = {
            'tester': b'tester',
            'admin': b'admin'
        }
        for k in self.user_map.keys():
            self.user_map[k] = bcrypt.hashpw(self.user_map[k],bcrypt.gensalt())

        # invites
        self.invites = [ 'apple', 'pancake']

        # Websocket tracking
        self.ws_client_idx = -1
        self.ws_clients = {}

        # Handlers
        #--> make a 'insert_auth_handlers' as an example
        self._handlers += [
            (r"/", MainHandler),
            (r"/fake/?", FakeMainHandler),
            (r"/upload/?",UploadHandler),
            (r"/upload-file/?",UploadImage),
            (r"/ws/echo/?",EchoWebSocket),
            (r"/upload-post/?",POSTUploadHandler)
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


    async def _call_heartbeat(self):
        while True:
            logging.info(f"heartbeat: {self.heartbeat_count}")
            self.heartbeat_count += 1
            await asyncio.sleep(1)

    async def on_shutdown(self):
        logging.info('app::on_shutdown >')
        self.heartbeat.cancel()
        for handler in self.ws_clients.values():
            handler.close()
        logging.info('< app::on_shutdown')

    #-- New Users ------------------------------------------------#

    def has_invite(self, invite):
        return invite in self.invites

    def remove_invite(self, invite):
        self.invites.remove(invite)

    def has_username(self, username):
        return username in self.user_map

    async def create_user(self, username, password):
        username = as_string(username)
        password = as_bytes(password)
        hpw = bcrypt.hashpw(password,bcrypt.gensalt()) # could run in executor
        self.user_map[username] = hpw
        logging.info('created user: %s', username)

    #-- Current Users ------------------------------------------------#

    def get_user_password_hash(self, username):
        # raise Exception('Implement')
        return self.user_map[username]

    def set_user_password_hash(self, username, password_hash):
        # raise Exception('Implement')
        self.user_map[username] = password_hash

    async def _validate_user_creds(self, username, password):
        ''' Obviously update this to something better '''
        username = as_string(username)
        password = as_bytes(password)
        try:
            pwh = self.get_user_password_hash(username)
            success = bcrypt.checkpw(password,pwh)
            if not success:
                logging.warning(f'Failed validation attempt for user: %s', username)
            return success
        except KeyError:
            logging.warning(f'No user: %s', username)
            return False

    async def _update_user_creds(self, username, password):
        if isinstance(username,bytes):
            username = username.decode('utf-8')
        if isinstance(password,str):
            password = password.encode('utf-8')
        hpw = bcrypt.hashpw(password,bcrypt.gensalt())
        print(username,password,hpw)
        self.set_user_password_hash(username,hpw)

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