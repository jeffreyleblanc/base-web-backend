# Copyright 2022 Jeffrey LeBlanc

# Python
import logging
# Tools
import bcrypt
# Local
from .utils import as_string, as_bytes


class AuthServerMixin:

    def setup_auth(self):

        # Example simple user map, don't do in real life!
        self.user_map = {
            'tester': b'tester',
            'admin': b'admin'
        }
        for k in self.user_map.keys():
            self.user_map[k] = bcrypt.hashpw(self.user_map[k],bcrypt.gensalt())

        # invites
        self.invites = [ 'apple', 'pancake']

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
