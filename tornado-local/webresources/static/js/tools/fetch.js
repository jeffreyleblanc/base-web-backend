

export async function POST_JSON(url, obj){
    const resp = await fetch(url, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(obj)
    });
    const json_resp = await resp.json();
    return json_resp;
}
