
Todo

-->
* clean up the authenticated dectorator
* common js file with getCookie and a fetch wrapper
* cleanup the file upload handler
    * e.g. where it writes too
    * show taking a sha256 of it


* improve the password update page
* improve the signup page
* revisit the fake page, including xsrf examples
* show getting the request ip
* make a standard page base for logged in users
* single file handler
* notes on run_in_executor

---

https://www.tornadoweb.org/en/stable/httpserver.html#http-server
note different ways to start listen with different processes

Note that the user secure_cookie can be read by the browser

https://tailwindcss.com/docs/installation#using-tailwind-via-cdn

To add:

* autoreload
    * for server code
    * for static and templates too
* basic websockets
    * include basic js setup and error handling
* post example
    * include basic js (fetch api)
* url regex example
* xsrf tokens
* examples of rejection (of say a websocket connection)
* ways of prefixing links
* filter out ip

* redirect failed password to try again

* pulling ip off of requests

* ws auth with cookies or a token?
    * also show it getting REJECTED

* breakup the system so it is cleaner!

#--> make a post json handler
#--> make a post normal handler
#--> make a upload file handler (single, and multiple?)

'''
This file is a self contained example of a tornado server with:
* virtualenv and pip configuration
* template and static file directories
* dev options
    * static file serving
    * file serving
    * autoreload
        * python code
        * other file paths
    * flags on the static sources (hashes)
* basic user account paths
    * use of bcrypt to hash passwords
* basic examples of common endpoints:
    * get
    * get with query parameters
    * post forms
    * AJAX style post
    * single file upload
    * multiple file upload
    * websockets
        * authenticated
        * unauthenticated
* setup with pure asyncio
    * graceful shutdown
* example nginx integration
    * includes as the root /
    * or as /some/path/ to the server
'''

https://www.tornadoweb.org/en/stable/
https://github.com/tornadoweb/tornado

https://www.tornadoweb.org/en/stable/guide/intro.html


https://www.tornadoweb.org/en/stable/guide/running.html

https://www.tornadoweb.org/en/stable/guide/templates.html

https://www.tornadoweb.org/en/stable/guide/security.html

https://www.tornadoweb.org/en/stable/util.html#tornado.util.ObjectDict


https://github.com/tornadoweb/tornado/issues/1791
https://github.com/tornadoweb/tornado/issues/1791#issuecomment-409258371

https://www.tornadoweb.org/en/stable/web.html#application-configuration

https://www.tornadoweb.org/en/stable/httpserver.html#tornado.httpserver.HTTPServer

https://www.tornadoweb.org/en/stable/autoreload.html?highlight=autoreload#module-tornado.autoreload