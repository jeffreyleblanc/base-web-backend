Node(A)
    server:
        websocket-/api/local/
            websocket-client <=>
        websocket-/api/node/
            websocket-node-client [A.wc1] <=> [B.nc1]
    node-clients:
        node-client [A.nc1] <=> [C.wc1]
Node(B)
    server:
        websocket-/api/local/
            websocket-client <=>
        websocket-/api/node/
            websocket-node-client [B.wc1] <=> [C.nc1]
    node-clients:
        node-client [B.nc1 <=> [A.wc1]
Node(C)
    server:
        websocket-/api/local/
            websocket-client <=>
        websocket-/api/node/
            websocket-node-client [C.wc1] <=> [A.nc1]
    node-clients:
        node-client [C.nc1] <=> [B.wc1]