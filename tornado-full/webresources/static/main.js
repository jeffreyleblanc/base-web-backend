console.log('Hello!');

// returns the cookie with the given name,
// or undefined if not found
function getCookie(name) {
  let matches = document.cookie.match(new RegExp(
    "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : undefined;
}


document.querySelector('#fileUpload').addEventListener('change', event => {
  handleImageUpload(event)
})

const handleImageUpload = event => {
  const files = event.target.files
  const formData = new FormData()
  formData.append('myFile', files[0])

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
  })
}




const ws = new WebSocket("ws://localhost:8888/ws/echo");
ws.onopen = function() {
    ws.send("Hello, world");
};
ws.onmessage = function (evt) {
   console.log(evt.data);
};

async function async_main(){
    const resp = await fetch('/upload?url=yaks.com&title=YAK_SHAVER');
    console.log('resp!',resp);

    const resp2 = await fetch('/upload-post', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-XSRFToken': getCookie('_xsrf')
        },
        body: JSON.stringify({a: 1, b: 'Some text'})
    });
    const jsonrep = await resp2.json();
    console.log(jsonrep);

}

async_main();
