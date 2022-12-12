/* Copyright 2022 Jeffrey LeBlanc */

// returns the cookie with the given name,
// or undefined if not found
function getCookie(name) {
    const matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

async function async_main(){
    console.log("Start of main");

    // Our session secret
    const session_secret = "_5QFrDCHm1c2WMzoDNgCWoRvuusomPZCVvd540XwtKM";

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
    const proto_string = `Bearer--${session_secret}`
    const ws = new WebSocket("ws://localhost:8888/ws/echo",proto_string);
    ws.onopen = function() {
        ws.send("Hello, world");
    };
    ws.onmessage = function (evt) {
       console.log("ws recv:",evt.data);
    };

    // A basic GET call
    const get_resp = await fetch('/upload?url=yaks.com&title=YAK_SHAVER');
    console.log('GET /upload response:',get_resp);

    // A basic POST call
    const post_resp = await fetch('/upload-post', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${session_secret}`,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-XSRFToken': getCookie('_xsrf')
        },
        body: JSON.stringify({a: 1, b: 'Some text'})
    });
    const post_obj = await post_resp.json();
    console.log("POST /upload-post returned object:",post_obj);
}

async_main();
