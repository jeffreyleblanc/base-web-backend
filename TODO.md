# Todo

Sprint 4:

* [ ] Make sure that the clients can be stopped/shut down easily
    * [ ] They should know their state as well
* [ ] Implement a client with basic future like capability
* [ ] Upgrade the mesh clients with the above
* [ ] Make sure the task tracking is sane and easy to manage/cleanup

Sprint 5:

* [ ] More modern node fqdn mappings / names etc
* [ ] Make a better node connection protocol/handshake


---

Sprint 3:

* [x] Initial mesh sketch

Sprint 2:

* [x] Clean up tornado-full python a bit
    * [x] Better endpoint names
    * [x] comments where needed (for example on ws subprotocol)
    * [x] Clean up random print statements
* [x] Make basic tornado asyncio websocket client

Sprint 1: Tornado-full

* [x] Remove the previous server.py file
* [x] Fix the http server / shutdown errors
* [x] Use pathlib
* [x] Break out files a bit more:
    * [x] utils
    * [x] base handlers
    * [x] auth components
* [x] Clean up the javascript and css as stand now
