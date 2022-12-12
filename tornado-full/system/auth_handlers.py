# Copyright 2022 Jeffrey LeBlanc

# Python
import functools
import urllib.parse
from urllib.parse import urlencode
# Tornado
import tornado.web
# Local
from .basehandlers import BaseHandler, BaseWebsocketHandler


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
