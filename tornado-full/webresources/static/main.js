/* Copyright 2022 Jeffrey LeBlanc */

// returns the cookie with the given name,
// or undefined if not found
function getCookie(name) {
    const matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

class InterfaceClient {

    constructor(session_secret){
        this.session_secret = session_secret;
    }

    make_websocket(url){
        const proto_string = `Bearer--${this.session_secret}`
        return new WebSocket(url,proto_string);
    }

    async get_json(url){
        const resp = await window.fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.session_secret}`,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-XSRFToken': getCookie('_xsrf')
            }
        });
        return await resp.json();
    }

    async post_json(url, obj){
        const resp = await window.fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.session_secret}`,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-XSRFToken': getCookie('_xsrf')
            },
            body: JSON.stringify(obj)
        });
        return await resp.json();
    }

}

async function async_main(){
    console.log("Start of main");

    // Our session secret
    const session_secret = "_5QFrDCHm1c2WMzoDNgCWoRvuusomPZCVvd540XwtKM";
    const client = new InterfaceClient(session_secret);

    // Setup the Image Upload
    const handleImageUpload = event => {
        const files = event.target.files;
        const formData = new FormData();
        formData.append('myFile', files[0]);

        fetch('/upload-file', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'X-XSRFToken': getCookie('_xsrf')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(data)
        })
        .catch(error => {
            console.error(error)
        });
    }
    document.querySelector('#fileUpload').addEventListener('change', event => {
        handleImageUpload(event)
    });

    // Make the websocket
    const ws = client.make_websocket("ws://localhost:8888/ws/echo");
    ws.onopen = function() {
        ws.send("Hello, world");
    };
    ws.onmessage = function (evt) {
       console.log("ws recv:",evt.data);
    };

    // A basic GET call
    const get_resp = await client.get_json(
        '/upload?url=yaks.com&title=YAK_SHAVER');
    console.log('GET /upload response:',get_resp);

    // A basic POST call
    const post_obj = await client.post_json('/upload-post',{
        a: 1, b:"Some text", c:false
    });
    console.log("POST /upload-post returned object:",post_obj);
}

async_main();
