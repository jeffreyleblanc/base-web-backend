/* Copyright 2022 Jeffrey LeBlanc */

export function get_cookie(name){
    // Returns cookie or undefined
    let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return (matches)? decodeURIComponent(matches[1]) : undefined;
}


export async function submit_form(event){
    event.preventDefault();
    const formEl = event.currentTarget;
    const url = formEl.action;

    try {
        const data = new URLSearchParams();
        for(const pair of new FormData(formEl)){
            data.append(pair[0], pair[1]); }

        const resp = await fetch(url,{
            method: 'post',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-XSRFToken': get_cookie('_xsrf')
            },
            body: data
        });

        const resp_obj = await resp.json();
        if(resp.status==200){
            return resp_obj;
        }else{
            const err = new Error(resp_obj.error)
            err.got_resp = true;
            err.resp_obj = resp_obj;
            err.status = resp.status
            throw err;
        }

    }catch(error){
        if(error.got_resp){ throw error }
        const err = new Error(error.message);
        err.got_resp = false;
        err.error = error;
        throw err;
    }
}
