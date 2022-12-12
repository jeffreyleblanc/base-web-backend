# Copyright 2022 Jeffrey LeBlanc

# Python
import json
# Tornado
import tornado.web


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

